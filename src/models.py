"""Models. All share: fit(texts, fraud_types) and predict_proba(texts) -> (n, len(classes_)).

The binary fraud score used for FPR/threshold work is 1 - P(F0).
"""
import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from config import SEED

# Phrases are written in cleaned form (lowercase, punctuation -> space, e.g. "don t").
# Chosen from domain knowledge, never tuned on test data.
KEYWORDS = {
    "F1": ["bank account", "fraud department", "suspicious transaction", "your card", "debit card",
           "credit card", "zelle", "wire transfer", "safe account", "verify your account",
           "unauthorized", "account has been locked", "account has been compromised", "routing number"],
    "F2": ["verification code", "one time code", "one time passcode", "otp", "reset your password",
           "code we sent", "read me the code", "security code", "two factor", "login", "password"],
    "F3": ["social security", "irs", "warrant", "arrest", "police", "legal action", "federal", "government",
           "back taxes", "tax", "suspended", "lawsuit", "officer", "customs", "legal department"],
    "F4": ["amazon", "refund", "tech support", "technical support", "computer", "virus", "microsoft",
           "remote access", "order placed", "apple", "subscription", "renewal", "your order"],
    "F5": ["my love", "my dear", "sweetheart", "darling", "soulmate", "meet in person", "miss you",
           "i love you", "our future together", "plane ticket"],
    "F6": ["investment", "invest", "crypto", "bitcoin", "profit", "returns", "trading", "platform",
           "mentor", "guaranteed", "usdt", "portfolio"],
    "F7": ["intimate", "explicit", "expose", "embarrassing", "leak", "your contacts", "nude", "video call",
           "recording of you", "share the video"],
    "F8": ["grandma", "grandpa", "jail", "bail", "accident", "hospital", "kidnapped", "don t tell mom",
           "don t tell dad", "lawyer", "in trouble"],
    "F9": ["you have won", "you ve won", "prize", "winner", "congratulations", "lottery", "claim your",
           "processing fee", "job offer", "upfront fee", "sweepstakes", "free vacation"],
    "GENERIC": ["don t hang up", "act now", "immediately", "urgent", "gift card", "gift cards",
                "do not tell anyone", "keep this confidential", "final notice", "press [NUMBER]",
                "right away", "today only"],
}


class KeywordRules:
    """Model 0: weighted keyword counts. P(type) ∝ its hit count; F0 gets a constant weight of 1,
    so the fraud score is S / (S + 1) where S is the total number of hits."""

    def __init__(self, keywords=KEYWORDS, generic_weight=0.5):
        self.generic_weight = generic_weight
        self.patterns = {t: re.compile(r"\b(" + "|".join(re.escape(p) for p in ps) + r")\b", re.I)
                         for t, ps in keywords.items()}

    def fit(self, texts, y):
        self.classes_ = np.array(sorted(set(y) | {"F0"}))
        return self

    def predict_proba(self, texts):
        fraud_types = [c for c in self.classes_ if c != "F0"]
        out = np.zeros((len(texts), len(self.classes_)))
        f0 = list(self.classes_).index("F0")
        for i, text in enumerate(texts):
            scores = {t: len(self.patterns[t].findall(text)) if t in self.patterns else 0 for t in fraud_types}
            generic = self.generic_weight * len(self.patterns["GENERIC"].findall(text))
            for t in fraud_types:  # spread generic pressure evenly over fraud types
                scores[t] += generic / len(fraud_types)
            for j, c in enumerate(self.classes_):
                out[i, j] = 1.0 if j == f0 else scores[c]
            out[i] /= out[i].sum()
        return out


class TfidfLR:
    """Model 1: word 1–2 gram TF-IDF + multinomial logistic regression, class_weight='balanced'."""

    def __init__(self, C=1.0):
        self.vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, max_features=200_000, sublinear_tf=True)
        self.clf = LogisticRegression(C=C, class_weight="balanced", max_iter=3000, random_state=SEED)

    def fit(self, texts, y):
        self.clf.fit(self.vec.fit_transform(texts), y)
        self.classes_ = self.clf.classes_
        return self

    def predict_proba(self, texts):
        return self.clf.predict_proba(self.vec.transform(texts))


MODELS = {"keyword_rules": KeywordRules, "tfidf_lr": TfidfLR}
