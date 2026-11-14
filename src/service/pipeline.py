"""Analyse one transcript for the service (fast mode, fits a ~30 s caller deadline).

  1. split the text into ~30-word windows (~12-15 s of speech each) - same chunking as the demo;
  2. per window: red-flag rules (+ F17 script match) and the classifier -> live risk-score timeline;
  3. ONE LLM call on the whole transcript: verdict + risk judgement + summary (short timeout, no retries,
     no disk cache - callers' transcripts are never written to disk);
  4. final risk score = rules + LLM judgement + trust signals + classifier (config/scoring.yaml).
If the LLM is unavailable or too slow, the service still answers from rules + classifier, says so in
`notes`, and returns a clearly marked fallback summary.
"""
import os
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from call_analysis.chunking import chunk_call, normalise  # noqa: E402
from call_analysis.flags import ScriptMatcher, rule_flags_in_chunk, t06_holds, verify_quotes  # noqa: E402
from call_analysis.scoring import CallClassifier, compute_score, render  # noqa: E402
from call_analysis.settings import load as load_settings  # noqa: E402

ARTIFACT = Path(__file__).resolve().parent / "artifacts" / "classifier.joblib"
MAX_CLASSES = 20
MAX_CLASS_LEN = 100
FALLBACK_WORDS = 40


def label_for(level, llm_verdict):
    """Primary class. High -> fraud. Medium -> fraud if the LLM also says scam, else uncertain.
    Low/Safe -> uncertain if the LLM says scam, else not_fraud."""
    if level == "High":
        return "fraud"
    if level == "Medium":
        return "fraud" if llm_verdict == "scam" else "uncertain"
    return "uncertain" if llm_verdict == "scam" else "not_fraud"


# The LLM's scam types (call_analysis.llm.SCAM_TYPES) mapped to the dashboard's F0-F9 codes.
# Output mapping only: no change to the model or its decision.
TYPE_TO_CATEGORY = {
    "not fraud": "F0", "financial impersonation": "F1", "account takeover": "F2",
    "government impersonation": "F3", "tech support / business impersonation": "F4",
    "romance": "F5", "investment / crypto": "F6", "sextortion": "F7",
    "family emergency": "F8", "prize / job / advance fee": "F9",
}


def category_for(label, scam_type):
    """F0-F9 code for the dashboard, or "unknown". The decision (label) wins: not_fraud -> F0;
    fraud/uncertain -> the LLM's type, or "unknown" if it gave none (or said "not fraud")."""
    if label == "not_fraud":
        return "F0"
    code = TYPE_TO_CATEGORY.get(str(scam_type).strip().lower())
    return code if code and code != "F0" else "unknown"


def _slug(text):
    return "_".join(str(text).lower().replace("/", " ").split())[:60] or "unknown"


class ScamService:
    def __init__(self, llm=None, use_llm=True):
        from models import get_encoder
        get_encoder().persist = False                 # never write callers' embeddings to disk
        self.matcher = ScriptMatcher()
        self.classifier = CallClassifier(artifact=os.environ.get("SCAM_CLASSIFIER_PATH", str(ARTIFACT)))
        self.llm, self.llm_error = llm, None
        if self.llm is None and use_llm:
            try:
                from call_analysis.llm import CallLLM
                self.llm = CallLLM(use_cache=False, retries=0,
                                   timeout_s=float(os.environ.get("SCAM_LLM_TIMEOUT_SECONDS", "20")))
            except (SystemExit, Exception) as e:  # service must start even without an LLM
                self.llm_error = f"LLM unavailable at startup: {e}"
        self._llm_lock = threading.Lock()
        if self.llm is not None and use_llm and llm is None:
            self._warm_up()

    def _warm_up(self):
        """Load the model into memory before traffic arrives (a cold 7B load can exceed the caller's deadline)."""
        saved = self.llm.timeout_s
        self.llm.timeout_s = 600
        try:
            self.llm._call_once('Reply with JSON: {"ok": true}')
        except Exception as e:
            self.llm_error = f"LLM warm-up failed: {type(e).__name__}"
        finally:
            self.llm.timeout_s = saved

    @property
    def llm_name(self):
        return f"{self.llm.provider}:{self.llm.model}" if self.llm else None

    def _ask_llm(self, transcript):
        from call_analysis.llm import quick
        if not self.llm:
            return None, self.llm_error or "LLM disabled"
        try:
            with self._llm_lock:                       # one LLM request at a time
                out = quick(self.llm, transcript)
            return out, None if out else "LLM answer could not be parsed"
        except Exception as e:  # timeout, connection refused, HTTP 5xx ...
            return None, f"LLM call failed: {type(e).__name__}"

    def analyze(self, text, request_id):
        cfg = load_settings()
        call = {"id": request_id, "transcript": normalise(text), "chunks": chunk_call(text, "api")}
        first, occurrences, timeline = {}, [], []
        for i, chunk in enumerate(call["chunks"]):
            new = rule_flags_in_chunk(chunk)
            if "F17" not in first:
                hit = self.matcher.in_chunk(chunk)
                if hit:
                    new.append(hit)
            occurrences += new
            for f in new:
                first.setdefault(f["id"], f)
            so_far = " ".join(s["text"] for ch in call["chunks"][:i + 1] for s in ch["segments"])
            clf = self.classifier.fraud_score(so_far)
            reds = [f for f in first.values() if f["severity"] != "trust"]
            trust = [f for f in first.values() if f["severity"] == "trust"]
            score, level, _ = compute_score(reds, trust, None, clf)
            timeline.append({"window": i, "end_s": chunk["end_s"], "risk_score": score, "level": level,
                             "new_flags": [f["id"] for f in new]})

        llm_out, llm_problem = self._ask_llm(render(call["chunks"]))
        reds = [f for f in first.values() if f["severity"] != "trust"]
        trust = [f for f in first.values() if f["severity"] == "trust"]
        t06 = t06_holds(call, reds)
        if t06:
            trust.append(t06)
        judgement = llm_out["risk_judgement"] if llm_out else None
        score, level, components = compute_score(reds, trust, judgement,
                                                 self.classifier.fraud_score(call["transcript"]))
        verify_quotes(call, occurrences + trust)

        verdict = llm_out["verdict"] if llm_out else "unavailable"
        label = label_for(level, verdict)
        scam_type = llm_out["likely_scam_type"] if llm_out else "unknown"
        recommendation = cfg["recommendations"][level]
        notes = []
        if llm_out:
            summary = llm_out["summary"]
        else:
            words = call["transcript"].split()
            summary = ("Automatic summary unavailable (" + llm_problem + "). Transcript begins: \""
                       + " ".join(words[:FALLBACK_WORDS]) + ("..." if len(words) > FALLBACK_WORDS else "") + "\"")
            notes.append(f"{llm_problem}; result is based on rules and the classifier only.")
        notes.append("Speaker roles are unknown for API text, so flags are checked on every line.")

        category = category_for(label, scam_type)
        classes = [label, f"category:{category}", f"risk_level:{level.lower()}", f"risk_score:{score}",
                   f"recommendation:{_slug(recommendation)}", f"type:{_slug(scam_type)}",
                   f"llm_verdict:{_slug(verdict)}"]
        classes += [f"flag:{f['id']}" for f in sorted(reds, key=lambda f: f["timestamp_s"])]
        classes = [c[:MAX_CLASS_LEN] for c in classes][:MAX_CLASSES]

        return {
            "request_id": request_id,
            "classes": classes,
            "summary": summary,
            # --- extra detail for direct JSON consumers (ignored by the transcription API) ---
            "label": label, "category": category, "risk_score": score, "risk_level": level, "recommendation": recommendation,
            "llm_verdict": verdict, "likely_scam_type": scam_type,
            "claimed_identity": llm_out["claimed_identity"] if llm_out else "unknown",
            "caller_request": llm_out["caller_request"] if llm_out else "unknown",
            "red_flags": [{k: f[k] for k in ("id", "name", "severity", "quote", "timestamp_s")} for f in reds],
            "trust_signals": [{k: t[k] for k in ("id", "name", "quote")} for t in trust],
            "score_components": components, "timeline": timeline,
            "llm_model": self.llm_name, "notes": notes,
            "disclaimer": "The risk score is a weighted rule/LLM/classifier score, not a probability. "
                          "It does not prove fraud.",
        }
