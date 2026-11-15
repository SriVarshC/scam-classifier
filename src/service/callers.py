"""Shared registry of callers flagged as fraud (all CallGuard users).

Abuse-resistant by design: a caller can only be added with a REPORT TICKET that this service signed when it
classified a call (POST /v1/classify returns "report:<ticket>" among `classes` for fraud/uncertain calls; the
transcription API forwards classes unchanged). A ticket is single-use, expires after TICKET_TTL_S, and:
  * fraud call      -> the dashboard reports it automatically (or the user does);
  * uncertain call  -> only a manual "Report caller as fraud" counts.
So nobody can flag an arbitrary number without a call our model actually analysed.

Privacy: caller IDs are never stored. Only HMAC-SHA256(secret, normalised caller key) is kept, with counts,
category, risk score and dates. The secret (SCAM_CALLERS_SECRET) also signs the tickets.

Env: SCAM_CALLERS_SECRET (>= 32 chars, required to enable), SCAM_CALLERS_DB (default
/var/lib/scam-service/callers.db), SCAM_CALLERS_TICKET_TTL_S (default 86400).
"""
import base64
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import threading
import time
from pathlib import Path

TICKET_TTL_S = int(os.environ.get("SCAM_CALLERS_TICKET_TTL_S", "86400"))
CATEGORY_RE = re.compile(r"^(F[0-9]|unknown)$")
LABELS = {"f": "fraud", "u": "uncertain"}


def normalise_caller(raw):
    """Stable key for a caller: phone numbers -> +digits (7-15 digits); platform IDs ("wa:...", "tg:...",
    "@user") -> lower-case. Returns "" if nothing usable."""
    s = str(raw or "").strip()
    if not s:
        return ""
    low = s.lower()
    if low.startswith(("wa:", "tg:", "@")):
        key = re.sub(r"\s+", "", low)
        return key if 3 < len(key) <= 80 else ""
    digits = re.sub(r"\D", "", s)
    if s.lstrip().startswith("00"):
        digits = digits[2:]
    return f"+{digits}" if 7 <= len(digits) <= 15 else ""


def _b64(b):
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64(s):
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


class CallerRegistry:
    def __init__(self, secret, db_path):
        if not secret or len(secret) < 32:
            raise ValueError("SCAM_CALLERS_SECRET must be at least 32 characters")
        self.key = secret.encode()
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS callers (
                caller_hash TEXT PRIMARY KEY, reports INTEGER NOT NULL, auto_reports INTEGER NOT NULL,
                manual_reports INTEGER NOT NULL, category TEXT, max_risk_score INTEGER,
                first_seen INTEGER NOT NULL, last_seen INTEGER NOT NULL)""")
            db.execute("CREATE TABLE IF NOT EXISTS used_tickets (nonce TEXT PRIMARY KEY, used_at INTEGER NOT NULL)")

    @classmethod
    def from_env(cls):
        secret = os.environ.get("SCAM_CALLERS_SECRET", "")
        if not secret:
            return None
        return cls(secret, os.environ.get("SCAM_CALLERS_DB", "/var/lib/scam-service/callers.db"))

    def _db(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def _hash(self, key):
        return hmac.new(self.key, b"caller:" + key.encode(), hashlib.sha256).hexdigest()

    # ---------- tickets ----------
    def issue_ticket(self, label, category, risk_score, now=None):
        """Compact signed ticket (fits in one 100-char class). None for not_fraud calls."""
        tag = {"fraud": "f", "uncertain": "u"}.get(label)
        if tag is None:
            return None
        cat = category if CATEGORY_RE.match(str(category)) else "unknown"
        payload = f"{int(now or time.time())}.{tag}.{cat}.{int(risk_score)}.{secrets.token_urlsafe(6)}"
        sig = hmac.new(self.key, b"ticket:" + payload.encode(), hashlib.sha256).digest()[:12]
        return f"{_b64(payload.encode())}.{_b64(sig)}"

    def _verify(self, ticket, now):
        try:
            body, sig = str(ticket).strip().split(".")
            payload = _unb64(body).decode()
            good = hmac.new(self.key, b"ticket:" + payload.encode(), hashlib.sha256).digest()[:12]
            if not hmac.compare_digest(_unb64(sig), good):
                return None
            ts, tag, cat, score, nonce = payload.split(".")
            if not (0 <= now - int(ts) <= TICKET_TTL_S) or tag not in LABELS:
                return None
            return {"label": LABELS[tag], "category": cat, "risk_score": int(score), "nonce": nonce}
        except Exception:
            return None

    # ---------- report / check ----------
    def report(self, ticket, caller, manual=False, now=None):
        now = int(now or time.time())
        key = normalise_caller(caller)
        if not key:
            return {"ok": False, "reason": "no usable caller id"}
        t = self._verify(ticket, now)
        if t is None:
            return {"ok": False, "reason": "invalid or expired report ticket"}
        if t["label"] == "uncertain" and not manual:
            return {"ok": False, "reason": "uncertain calls are only added by a manual report"}
        h = self._hash(key)
        with self._lock, self._db() as db:
            try:
                db.execute("INSERT INTO used_tickets VALUES (?, ?)", (t["nonce"], now))
            except sqlite3.IntegrityError:
                return {"ok": False, "reason": "ticket already used"}
            db.execute("DELETE FROM used_tickets WHERE used_at < ?", (now - 2 * TICKET_TTL_S,))
            db.execute("""INSERT INTO callers VALUES (?, 1, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(caller_hash) DO UPDATE SET reports = reports + 1,
                  auto_reports = auto_reports + excluded.auto_reports,
                  manual_reports = manual_reports + excluded.manual_reports,
                  category = CASE WHEN excluded.category != 'unknown' THEN excluded.category ELSE category END,
                  max_risk_score = MAX(max_risk_score, excluded.max_risk_score), last_seen = excluded.last_seen""",
                       (h, 0 if manual else 1, 1 if manual else 0, t["category"], t["risk_score"], now, now))
        return {"ok": True, **self.check(key)}

    def check(self, caller):
        key = normalise_caller(caller)
        if not key:
            return {"flagged": False, "reports": 0}
        with self._db() as db:
            row = db.execute("SELECT reports, auto_reports, manual_reports, category, max_risk_score, first_seen, "
                             "last_seen FROM callers WHERE caller_hash = ?", (self._hash(key),)).fetchone()
        if not row:
            return {"flagged": False, "reports": 0}
        iso = lambda s: time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(s))  # noqa: E731
        return {"flagged": True, "reports": row[0], "auto_reports": row[1], "manual_reports": row[2],
                "category": row[3], "max_risk_score": row[4], "first_seen": iso(row[5]), "last_seen": iso(row[6])}
