"""Reuse model fits between experiment runs (PERF.md P2-2).

The key hashes the model name, hyper-parameters, training ids AND labels, so a different split or a
label shuffle never returns a stale model. Only CPU sklearn models are cached (DeBERTa is retrained).
Files live in data/processed/fit_cache/ (git-ignored, like the rest of data/processed/).
Set FIT_CACHE=0 to bypass the cache for one run.
"""
import hashlib
import json
import os

import joblib

from config import PROCESSED

CACHE_DIR = PROCESSED / "fit_cache"
VERSION = 1  # bump when a cached model would change meaning (features, cleaning, ...)
CACHEABLE = {"keyword_rules", "tfidf_lr", "embedding_lr"}


def enabled():
    return os.environ.get("FIT_CACHE", "1") != "0"


def _key(name, params, ids, labels):
    blob = json.dumps([VERSION, name, params, [str(i) for i in ids], [str(y) for y in labels]],
                      sort_keys=True).encode("utf-8")
    return f"{name}_{hashlib.sha256(blob).hexdigest()[:16]}"


def fit_or_load(name, factory, texts, labels, ids, params=None):
    """Load the cached fit for these (model, params, train ids, labels) or fit and cache it."""
    texts, labels = list(texts), list(labels)
    if not enabled():
        return factory().fit(texts, labels)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / f"{_key(name, params or {}, ids, labels)}.joblib"
    if path.exists():
        print(f"    cached fit: {path.name}", flush=True)
        return joblib.load(path)
    model = factory().fit(texts, labels)
    joblib.dump(model, path)
    return model
