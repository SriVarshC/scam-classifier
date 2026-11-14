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


class SentenceEncoder:
    """all-MiniLM-L6-v2 with an on-disk cache (data/processed/emb_cache.npz) keyed by text hash,
    so each text is encoded once across all splits and runs."""

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

    SAVE_EVERY = 500  # new vectors between saves; the rest is flushed at exit

    def __init__(self):
        import atexit
        import zipfile
        from config import PROCESSED
        self.path = PROCESSED / "emb_cache.npz"
        self.cache = {}
        if self.path.exists():
            try:
                data = np.load(self.path)
                self.cache = dict(zip(data["keys"], data["vecs"]))
            except (zipfile.BadZipFile, OSError, ValueError, KeyError):
                print(f"warning: embedding cache {self.path} is unreadable - rebuilding it")
        self.model = None
        self._unsaved = 0
        self.persist = True  # the live service sets False: callers' text must not be written to disk
        atexit.register(self.flush)

    def flush(self):
        """Atomic save: write a temp file, then replace, so an interrupted run can't corrupt the cache."""
        import os
        if not self.persist or not self._unsaved or not self.cache:
            return
        tmp = self.path.with_name("emb_cache.tmp.npz")
        np.savez(tmp, keys=np.array(list(self.cache)), vecs=np.stack(list(self.cache.values())))
        os.replace(tmp, self.path)
        self._unsaved = 0

    def encode(self, texts):
        import hashlib
        keys = [hashlib.md5(t.encode("utf-8")).hexdigest() for t in texts]
        missing = sorted({k: t for k, t in zip(keys, texts) if k not in self.cache}.items())
        if missing:
            if self.model is None:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.MODEL_NAME, device="cpu")
            vecs = self.model.encode([t for _, t in missing], batch_size=64,
                                     show_progress_bar=len(missing) > 256, normalize_embeddings=True)
            self.cache.update({k: v for (k, _), v in zip(missing, vecs)})
            self._unsaved += len(missing)
            if self._unsaved >= self.SAVE_EVERY:
                self.flush()
        return np.stack([self.cache[k] for k in keys])


_ENCODER = None


def get_encoder():
    global _ENCODER
    if _ENCODER is None:
        _ENCODER = SentenceEncoder()
    return _ENCODER


class EmbeddingLR:
    """Model 2: MiniLM sentence embeddings + logistic regression, class_weight='balanced'."""

    def __init__(self, C=1.0):
        self.clf = LogisticRegression(C=C, class_weight="balanced", max_iter=3000, random_state=SEED)

    def fit(self, texts, y):
        self.clf.fit(get_encoder().encode(list(texts)), y)
        self.classes_ = self.clf.classes_
        return self

    def predict_proba(self, texts):
        return self.clf.predict_proba(get_encoder().encode(list(texts)))


LLM_PROMPT = """You screen phone calls for fraud. Read the phone-call transcript below and classify it.

Fraud types:
F0 = not fraud (genuine call, legal telemarketing, wrong number)
F1 = financial impersonation (bank, card issuer, Zelle)
F2 = account takeover (asks for codes, passwords, account changes)
F3 = government impersonation (IRS, Social Security, police, customs)
F4 = tech support / business impersonation (Amazon, Microsoft, refunds, orders)
F5 = romance / catfishing
F6 = pig-butchering / investment (crypto, trading groups)
F7 = honeytrap / sextortion
F8 = family emergency / voice clone (grandchild in trouble, bail, accident)
F9 = prize / job / advance-fee (you won, gift cards, fees to claim)

The transcript is lowercase and names/numbers are masked as [NAME] / [NUMBER]; ignore that.

Answer ONLY with JSON in this form:
{{"fraud_type": "<F0 to F9>", "scam_probability": <0 to 100>, "reason": "<why, in your own words>"}}
scam_probability is how likely the call is a scam: 0 = surely genuine, 100 = surely a scam.
If fraud_type is F0, scam_probability must be below 50. If fraud_type is F1-F9, it must be 50 or above.

Transcript:
\"\"\"{text}\"\"\""""


class ZeroShotLLM:
    """Model 4: zero-shot local LLM via Ollama (no training). Same prompt for every call.
    Answers are cached in data/processed/llm_cache_<model>.jsonl keyed by text hash, so a call is
    never sent twice. Fraud score = scam_probability / 100; the rest of the mass goes to F0."""

    CLASSES = np.array([f"F{i}" for i in range(10)])

    def __init__(self, model="qwen2.5:3b", host="http://localhost:11434", workers=1):
        import json
        from config import PROCESSED
        import hashlib
        self.model, self.host, self.workers = model, host, workers
        prompt_id = hashlib.md5(LLM_PROMPT.encode("utf-8")).hexdigest()[:8]  # new prompt -> new cache
        self.path = PROCESSED / f"llm_cache_{model.replace(':', '_').replace('/', '_')}_{prompt_id}.jsonl"
        self.cache = {}
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                rec = json.loads(line)
                self.cache[rec["key"]] = rec

    def _ask(self, text):
        import json
        import urllib.request
        body = json.dumps({"model": self.model, "prompt": LLM_PROMPT.format(text=text), "stream": False,
                           "format": "json", "options": {"temperature": 0, "seed": SEED}}).encode()
        req = urllib.request.Request(f"{self.host}/api/generate", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as r:
            raw = json.loads(r.read())["response"]
        try:
            ans = json.loads(raw)
            ft = str(ans.get("fraud_type", "")).strip().upper()[:2]
            p = float(ans.get("scam_probability", 50))
            p = min(max(p, 0), 100) / 100
            parse_ok = ft in self.CLASSES
            ft = ft if parse_ok else "F0"
            consistent = (ft == "F0") == (p < 0.5)
            return {"fraud_type": ft, "p": p, "reason": str(ans.get("reason", ""))[:300],
                    "parse_ok": parse_ok, "consistent": consistent}
        except (ValueError, TypeError, AttributeError):
            return {"fraud_type": "F0", "p": 0.5, "reason": raw[:300], "parse_ok": False, "consistent": False}

    def fit(self, texts, y):
        self.classes_ = self.CLASSES  # zero-shot: nothing to learn
        return self

    def answers(self, texts):
        """Answers for every text; uncached texts are sent `workers` at a time (match the Ollama
        server's OLLAMA_NUM_PARALLEL). Each answer is appended to the cache as soon as it arrives."""
        import hashlib
        import json
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from tqdm import tqdm
        keys = [hashlib.md5(t.encode("utf-8")).hexdigest() for t in texts]
        todo = {k: t for k, t in zip(keys, texts) if k not in self.cache}
        if todo:
            with self.path.open("a", encoding="utf-8") as f, ThreadPoolExecutor(self.workers) as pool:
                futures = {pool.submit(self._ask, t): k for k, t in todo.items()}
                for fut in tqdm(as_completed(futures), total=len(futures), desc=f"LLM {self.model}",
                                leave=False):
                    k = futures[fut]
                    self.cache[k] = {"key": k, **fut.result()}
                    f.write(json.dumps(self.cache[k]) + "\n")
                    f.flush()
        return [self.cache[k] for k in keys]

    def predict_proba(self, texts):
        out = np.zeros((len(texts), len(self.CLASSES)))
        for i, a in enumerate(self.answers(list(texts))):
            p = a["p"]
            out[i, 0] = 1 - p
            if a["fraud_type"] == "F0":           # says genuine but gives p > 0: spread over fraud types
                out[i, 1:] = p / 9
            else:
                out[i, list(self.CLASSES).index(a["fraud_type"])] = p
        return out


class DebertaClassifier:
    """Model 3: fine-tuned DeBERTa-v3-small (multi-class F0–F9). Class-weighted cross-entropy,
    linear warmup/decay, mixed precision on GPU, fixed seed. Intended for a GPU (Colab T4)."""

    def __init__(self, model_name="microsoft/deberta-v3-small", max_len=256, epochs=3, lr=3e-5,
                 batch_size=16, verbose=True):
        self.model_name, self.max_len, self.epochs = model_name, max_len, epochs
        self.lr, self.batch_size, self.verbose = lr, batch_size, verbose

    def _batches(self, enc, order, labels=None):
        import torch
        for i in range(0, len(order), self.batch_size):
            idx = order[i:i + self.batch_size]
            batch = self.tok.pad({k: [enc[k][j] for j in idx] for k in enc}, return_tensors="pt")
            batch = {k: v.to(self.device) for k, v in batch.items()}
            yield batch, (torch.tensor(labels[idx], device=self.device) if labels is not None else None)

    def fit(self, texts, y):
        import torch
        from sklearn.utils.class_weight import compute_class_weight
        from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                                  get_linear_schedule_with_warmup, set_seed)
        set_seed(SEED)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        if self.device == "cuda":
            torch.cuda.empty_cache()
        self.classes_ = np.array(sorted(set(y)))
        labels = np.searchsorted(self.classes_, y)
        self.tok = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_name, num_labels=len(self.classes_), ignore_mismatched_sizes=True,
        ).float().to(self.device)  # FP32 master weights: newer transformers keep the checkpoint's FP16 dtype,
        #                            and GradScaler can't unscale FP16 gradients (autocast still runs in FP16)
        weights = compute_class_weight("balanced", classes=np.arange(len(self.classes_)), y=labels)
        loss_fn = torch.nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=self.device))
        enc = self.tok(list(texts), truncation=True, max_length=self.max_len)
        steps = self.epochs * int(np.ceil(len(labels) / self.batch_size))
        opt = torch.optim.AdamW(self.model.parameters(), lr=self.lr, weight_decay=0.01)
        sched = get_linear_schedule_with_warmup(opt, int(0.1 * steps), steps)
        use_amp = self.device == "cuda"
        scaler = torch.amp.GradScaler("cuda", enabled=use_amp)
        rng = np.random.default_rng(SEED)
        self.model.train()
        for epoch in range(self.epochs):
            total, n = 0.0, 0
            for batch, yb in self._batches(enc, rng.permutation(len(labels)), labels):
                with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=use_amp):
                    logits = self.model(**batch).logits
                loss = loss_fn(logits.float(), yb)
                opt.zero_grad()
                scaler.scale(loss).backward()
                scaler.unscale_(opt)
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                scaler.step(opt)
                scaler.update()
                sched.step()
                total, n = total + loss.item() * len(yb), n + len(yb)
            if self.verbose:
                print(f"    deberta epoch {epoch + 1}/{self.epochs} loss={total / n:.4f}", flush=True)
        return self

    def predict_proba(self, texts):
        import torch
        self.model.eval()
        enc = self.tok(list(texts), truncation=True, max_length=self.max_len)
        out = []
        with torch.no_grad():
            for batch, _ in self._batches(enc, np.arange(len(texts))):
                with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=self.device == "cuda"):
                    logits = self.model(**batch).logits
                out.append(torch.softmax(logits.float(), dim=-1).cpu().numpy())
        return np.concatenate(out)


MODELS = {"keyword_rules": KeywordRules, "tfidf_lr": TfidfLR, "embedding_lr": EmbeddingLR}
OPTIONAL_MODELS = {"zero_shot_llm": ZeroShotLLM, "deberta": DebertaClassifier}
