"""Metrics: threshold chosen on validation (FPR <= 2%), then binary + per-fraud-type metrics on test."""
import numpy as np
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

TARGET_FPR = 0.02


def fraud_score(proba, classes):
    return 1.0 - proba[:, list(classes).index("F0")]


def choose_threshold(scores, y_true, target_fpr=TARGET_FPR):
    """Lowest threshold whose validation FPR <= target (=> highest recall within the FPR budget)."""
    neg = np.sort(scores[y_true == 0])
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
    y_pred = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    return {
        "fpr": fp / (fp + tn) if fp + tn else np.nan,
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "f1_binary": f1_score(y_true, y_pred, zero_division=0),
        "roc_auc": roc_auc_score(y_true, scores) if len(set(y_true)) == 2 else np.nan,
        "tn": tn, "fp": fp, "fn": fn, "tp": tp,
    }


def type_metrics(true_types, pred_types):
    """Macro F1 over fraud types that actually occur in the test set (others can't be measured)."""
    labels = sorted(set(true_types))
    per = f1_score(true_types, pred_types, labels=labels, average=None, zero_division=0)
    support = {l: int((np.asarray(true_types) == l).sum()) for l in labels}
    return {"macro_f1_types": float(np.mean(per))}, {l: (float(f), support[l]) for l, f in zip(labels, per)}
