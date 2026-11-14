"""Step 3: rules engine. Red flags + trust signals, each with an exact quote, chunk index and timestamp.

Matching (on the CALLER side only - lines spoken by "You" are skipped):
  * case- and punctuation-insensitive word matching ("Don't" == "dont");
  * a pattern word also matches common inflections (suspend -> suspended, arrest -> arrested);
  * fuzzy: words of 5+ letters with the same first letter match if their similarity >=
    flags.fuzzy_token_ratio (ASR noise; "verificaton" -> "verification", but "report" != "deport");
  * "*" in a pattern skips 0-3 words ("read * code" matches "read me the code").
Every quote is cut from the original transcript text, and verify_quotes() fails loudly if any
quote is not found verbatim in the transcript.
"""
import re
from difflib import SequenceMatcher

import numpy as np

from call_analysis.settings import load as load_settings

WORDS_PER_SECOND = 2.5
SUFFIXES = ("", "s", "es", "d", "ed", "ing", "ion", "ation", "ment", "er", "ly")
GAP = "*"
MAX_GAP = 3

# id, name, severity, patterns
RED_FLAGS = [
    ("F01", "Asks for one-time code / PIN / password", "critical", [
        "code we sent", "code that * sent", "code you received", "verification code", "one time code",
        "one time passcode", "one time password", "otp", "read me the code", "read * the code",
        "tell me the code", "give me the code", "security code", "authentication code", "passcode",
        "your pin", "pin number", "your password",
        # v2 (after the first demo run, validated on held-out calls): other wordings of the same request
        "sent * code", "sent you * code", "texted * code", "what does the code say",
        "the pin", "need * pin", "need * password"]),
    ("F02", "Safe / secure account - move money to protect it", "critical", [
        "safe account", "secure account", "protected account", "safety account", "move your money",
        "move * money * safe", "transfer * funds * safe", "transfer * money * secure", "protect your money",
        "protect your funds", "keep your money safe"]),
    ("F03", "Remote access app request", "critical", [
        "anydesk", "any desk", "teamviewer", "team viewer", "ultraviewer", "remote access", "remote desktop",
        "install * app", "download * app", "install this", "access to your computer", "access your computer",
        "control of your computer", "connect to your computer"]),
    ("F04", "Payment by gift card / crypto / cash courier / wire", "critical", [
        "gift card", "google play card", "itunes card", "steam card", "prepaid card", "bitcoin", "crypto",
        "cryptocurrency", "usdt", "western union", "moneygram", "wire transfer", "wire * money",
        "send cash", "cash courier", "courier * cash", "pick up the cash"]),
    ("F12", "Threats (arrest, lawsuit, frozen/suspended account, deportation)", "high", [
        "arrest", "warrant", "lawsuit", "legal action", "legal enforcement", "enforcement action", "police",
        "frozen", "freeze your", "suspend", "suspension", "deport", "jail", "prison", "seize", "seizure",
        "sue you", "criminal charges"]),
    ("F13", "Secrecy request", "high", [
        "don't tell", "do not tell", "not tell anyone", "keep this between us", "keep this confidential",
        "keep it confidential", "keep it secret", "keep this secret", "don't discuss", "do not discuss",
        "don't share this", "don't mention"]),
    ("F14", "Asks for SSN / full card number / account number", "high", [
        # SSN only counts when it is REQUESTED (merely mentioning it is common in genuine talk too)
        "give * social security", "provide * social security", "confirm * social security",
        "verify * social security", "read * social security", "what is your social security",
        "your social security number please", "give * ssn", "confirm * ssn", "verify * ssn", "your ssn",
        "last four digits of your social", "last four of your social",
        "card number", "credit card number", "debit card number", "account number", "routing number",
        "bank account number"]),
    ("F20", "Urgency", "medium", [
        "right now", "immediately", "immediate", "within the hour", "within * hours", "urgent", "urgently",
        "as soon as possible", "act now", "right away", "final notice", "last chance", "today only",
        "no time", "quickly", "hurry"]),  # v2: quickly / hurry
    ("F21", "Don't hang up / keep you on the line", "medium", [
        "don't hang up", "do not hang up", "stay on the line", "stay on line", "keep you on the line",
        "don't disconnect", "do not disconnect", "stay on the phone", "don't leave the call"]),
    ("F22", "Won't give name / company / ID", "medium", [
        "can't give * name", "cannot give * name", "can't tell you * name", "not allowed to * name",
        "can't give * id", "cannot give * badge", "doesn't matter who", "you don't need to know",
        "not important who"]),
    ("F25", "Too good to be true (prize, won, refund, guaranteed)", "medium", [
        "you have won", "you've won", "you won", "prize", "winner", "congratulations", "refund",
        "guaranteed", "selected to receive", "claim your", "lottery", "jackpot", "reward"]),
]

TRUST_SIGNALS = [
    ("T04", "Tells you to call back on the official number / number on your card", [
        "number on the back of your card", "number on your card", "number on the back of the card",
        "call the number on", "official number", "official website", "call your bank directly",
        "call us back on the number", "hang up and call", "call the bank directly"]),
]
T06 = ("T06", "No request for money, codes or personal data during the whole call")
# T06 is withheld if any of these flags fired or any money request appears on the caller side
T06_BLOCKING_FLAGS = {"F01", "F02", "F03", "F04", "F14"}
MONEY_REQUEST = ["pay", "payment", "fee", "send * money", "transfer", "purchase", "buy", "deposit",
                 "processing fee", "your card details", "your bank details", "date of birth"]

# F17: small library of GENERIC scam scripts (written for this project, not taken from the test calls)
SCAM_SCRIPTS = [
    "This is the Social Security Administration. Your social security number has been suspended due to "
    "suspicious activity. Press one to speak to an officer or a warrant will be issued for your arrest.",
    "This is the IRS. You owe back taxes and a lawsuit has been filed against you. Pay today with gift "
    "cards or the local police will come to arrest you.",
    "This is Amazon. An order for an iPhone was placed on your account and your card was charged. If you "
    "did not make this purchase press one to speak to a representative.",
    "This is Microsoft technical support. Your computer is infected with a virus. Please install this "
    "remote access app so our technician can fix it.",
    "This is the fraud department of your bank. Someone is trying to access your account. To protect your "
    "money we need to move it to a safe account. Please read me the code we just sent you.",
    "Grandma it's me, I'm in trouble. I was in an accident and I'm in jail. I need money for bail right "
    "now, please don't tell mom and dad.",
    "Congratulations, you have been selected to receive a prize. To claim your reward you just need to pay "
    "a small processing fee with a gift card.",
    "Our investment group made forty percent profit this week trading crypto with our mentor. Deposit "
    "today on our platform to join the next round.",
    "We are calling about your car's extended warranty. This is your final notice before we close the "
    "file. Press one now to speak with a specialist.",
    "Your account has been locked because of unusual activity. Verify your identity by giving me your "
    "account number and the one time passcode.",
    # v2: customs / package-seizure script (generic, not copied from any test call)
    "This is customs and border protection. A package in your name was seized because it contained illegal "
    "items. Press one to speak with an investigation officer or face legal consequences.",
]


def _norm(word):
    return re.sub(r"[^\w]", "", word.lower())


def _tokens(text):
    """[(normalised word, start char, end char)] for the original text (empty normalised words dropped)."""
    return [(_norm(m.group()), m.start(), m.end()) for m in re.finditer(r"\S+", text) if _norm(m.group())]


def _word_match(pat, word, ratio):
    if word == pat:
        return True
    if len(pat) >= 4 and word.startswith(pat) and word[len(pat):] in SUFFIXES:
        return True
    # fuzzy (ASR noise): long words only, same first letter ("report" must not match "deport")
    return (len(pat) >= 5 and len(word) >= 5 and word[0] == pat[0]
            and SequenceMatcher(None, pat, word).ratio() >= ratio)


def _compile(pattern):
    return [GAP if p == GAP else _norm(p) for p in pattern.split()]


def _match_at(pat, toks, i, ratio):
    """End index (exclusive) if pattern matches starting at token i, else None."""
    if not pat:
        return i
    if pat[0] == GAP:
        for skip in range(MAX_GAP + 1):
            end = _match_at(pat[1:], toks, i + skip, ratio)
            if end is not None:
                return end
        return None
    if i < len(toks) and _word_match(pat[0], toks[i][0], ratio):
        return _match_at(pat[1:], toks, i + 1, ratio)
    return None


def find_phrase(text, patterns):
    """First match of any pattern in text -> (start_token, end_token, tokens) or None."""
    cfg = load_settings()["flags"]
    toks = _tokens(text)
    compiled = [_compile(p) for p in patterns]
    for i in range(len(toks)):
        for pat in compiled:
            end = _match_at(pat, toks, i, cfg["fuzzy_token_ratio"])
            if end is not None and end > i:
                return i, end, toks
    return None


def _quote(text, start, end, toks):
    ctx = load_settings()["flags"]["quote_context_words"]
    a, b = max(0, start - ctx), min(len(toks), end + ctx)
    return text[toks[a][1]:toks[b - 1][2]]


def _caller_segments(chunk):
    """(segment text, word offset of the segment inside the chunk) for non-"You" segments."""
    offset = 0
    for seg in chunk["segments"]:
        if seg["speaker"] != "You":
            yield seg["text"], offset
        offset += len(seg["text"].split())


def _evidence(fid, name, severity, chunk, text, offset, start, end, toks):
    words_before = offset + len(text[:toks[start][1]].split())
    return {"id": fid, "name": name, "severity": severity, "quote": _quote(text, start, end, toks),
            "chunk": chunk["index"], "timestamp_s": round(chunk["start_s"] + words_before / WORDS_PER_SECOND, 1)}


def rule_flags_in_chunk(chunk):
    """Phrase-based red flags and T04 found in one chunk (every occurrence id once per chunk)."""
    found = []
    defs = [(f, n, s, p) for f, n, s, p in RED_FLAGS] + [(t, n, "trust", p) for t, n, p in TRUST_SIGNALS]
    for fid, name, severity, patterns in defs:
        for text, offset in _caller_segments(chunk):
            hit = find_phrase(text, patterns)
            if hit:
                found.append(_evidence(fid, name, severity, chunk, text, offset, *hit))
                break
    return found


class ScriptMatcher:
    """F17: embedding similarity between caller segments and the generic scam-script library."""

    def __init__(self):
        from models import get_encoder
        self.encoder = get_encoder()
        self.library = self.encoder.encode(SCAM_SCRIPTS)
        self.threshold = load_settings()["flags"]["script_similarity"]

    def in_chunk(self, chunk):
        for text, offset in _caller_segments(chunk):
            sims = self.library @ self.encoder.encode([text])[0]
            if sims.max() >= self.threshold:
                words = text.split()
                quote = text if len(words) <= 30 else text[:_tokens(text)[29][2]]
                return {"id": "F17", "name": "Matches a known scam script", "severity": "high", "quote": quote,
                        "chunk": chunk["index"],
                        "timestamp_s": round(chunk["start_s"] + offset / WORDS_PER_SECOND, 1),
                        "similarity": round(float(sims.max()), 3), "script_no": int(np.argmax(sims))}
        return None


def t06_holds(call, flags):
    """T06: no money / code / personal-data request anywhere on the caller side of the whole call.
    v2: never awarded when any high or critical red flag fired (a threat with "press one" is not reassuring)."""
    if any(f["id"] in T06_BLOCKING_FLAGS or f["severity"] in ("critical", "high") for f in flags):
        return None
    for chunk in call["chunks"]:
        for text, _ in _caller_segments(chunk):
            if find_phrase(text, MONEY_REQUEST):
                return None
    last = call["chunks"][-1]
    return {"id": T06[0], "name": T06[1], "severity": "trust",
            "quote": "", "chunk": last["index"], "timestamp_s": last["end_s"]}


def verify_quotes(call, flags):
    """Fail loudly if any quote is not verbatim in the transcript (T06 has no quote by design)."""
    bad = [f for f in flags if f["id"] != "T06" and (not f["quote"] or f["quote"] not in call["transcript"])]
    if bad:
        raise AssertionError(f"{call['id']}: {len(bad)} quote(s) not found verbatim: "
                             + "; ".join(f"{f['id']}={f['quote']!r}" for f in bad))
    return True
