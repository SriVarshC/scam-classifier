"""Metrics: threshold chosen on validation (FPR <= 1.5%, inside the 2% target), then binary + type metrics.

Reporting rules (PERF.md P0-2 / P0-3):
  * every rate comes with a 95% Wilson interval;
  * FPR is NA when the test set has fewer than `MIN_NEGATIVES` genuine calls - "0 out of 2" says
    nothing about 2%, and quoting it as 0% is how a meaningless number reaches the README;
  * type metrics cover the fixed F0-F9 set, so a fraud type with no test rows scores 0 (support 0)
    instead of silently vanishing from the average.
"""
import numpy as np
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

from config import FRAUD_TYPES

TARGET_FPR = 0.02          # the project target (CLAUDE.md)
THRESHOLD_FPR = 0.015      # threshold chosen slightly inside the target: a margin against sampling noise
MIN_NEGATIVES = 100        # below this many genuine calls an FPR is not reported

CLASSES = list(FRAUD_TYPES)  # F0-F9, fixed order


def fraud_score(proba, classes):
    return 1.0 - proba[:, list(classes).index("F0")]


def wilson_interval(successes, n, z=1.96):
    """95% Wilson score interval for a binomial rate (better than normal approx. at small n)."""
    if n <= 0:
        return float(np.nan), float(np.nan)
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return float(max(0.0, centre - half)), float(min(1.0, centre + half))


def choose_threshold(scores, y_true, target_fpr=THRESHOLD_FPR):
    """Lowest threshold whose validation FPR <= target (=> highest recall within the FPR budget)."""
    neg = np.sort(np.asarray(scores)[np.asarray(y_true) == 0])
    if len(neg) == 0:
        return 0.5
    k = int(np.floor(target_fpr * len(neg)))          # number of negatives we may flag
    t = neg[len(neg) - k - 1] if k < len(neg) else neg[0]
    return float(np.nextafter(t, np.inf))             # strictly above that negative


def predict_types(proba, classes, scores, threshold):
    """Flagged rows get the most likely fraud type; the rest are F0."""
    classes = np.array(classes)
    fraud_cols = [i for i, c in enumerate(classes) if c != "F0"]
    best = classes[np.array(fraud_cols)[proba[:, fraud_cols].argmax(axis=1)]]
    return np.where(scores >= threshold, best, "F0")


def binary_metrics(y_true, scores, threshold):
    y_true = np.asarray(y_true)
    y_pred = (np.asarray(scores) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    n_neg, n_pos = int(fp + tn), int(tp + fn)
    fpr_lo, fpr_hi = wilson_interval(fp, n_neg)
    rec_lo, rec_hi = wilson_interval(tp, n_pos)
    return {
        # NA (not 0.0) when there are too few genuine calls to estimate it
        "fpr": fp / n_neg if n_neg >= MIN_NEGATIVES else np.nan,
        "fpr_ci_low": fpr_lo, "fpr_ci_high": fpr_hi, "n_negatives": n_neg,
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "recall_ci_low": rec_lo, "recall_ci_high": rec_hi, "n_positives": n_pos,
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "f1_binary": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_true, scores) if len(set(y_true)) == 2 else np.nan,
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
    }


def type_metrics(true_types, pred_types):
    """Macro F1 over the fixed F0-F9 set. Types absent from the test set count as F1 = 0, support 0,
    so the macro average cannot be inflated by leaving hard/missing types out."""
    per = f1_score(true_types, pred_types, labels=CLASSES, average=None, zero_division=0)
    support = {l: int((np.asarray(true_types) == l).sum()) for l in CLASSES}
    return {"macro_f1_types": float(np.mean(per))}, {l: (float(f), support[l]) for l, f in zip(CLASSES, per)}
