"""Train every model on every split, evaluate, and write results/metrics.csv + results/summary.md.

Usage: python src/run_experiment.py [--models keyword_rules tfidf_lr]
"""
import argparse

import numpy as np
import pandas as pd

from config import PROCESSED, RESULTS
from evaluate import binary_metrics, choose_threshold, fraud_score, predict_types, type_metrics
from models import MODELS

SPLITS = PROCESSED / "splits"
TESTS = ["A"] + sorted(p.name[:-len("_test.csv")] for p in SPLITS.glob("B_*_test.csv"))
EARLY_WORDS = 50


def load_split(name, merged):
    parts = {}
    for p in ("train", "val", "test"):
        ids = pd.read_csv(SPLITS / f"{name}_{p}.csv")[["id"]]
        parts[p] = ids.merge(merged, on="id", how="left")
    return parts


def truncate(texts, n=EARLY_WORDS):
    return [" ".join(t.split()[:n]) for t in texts]


def evaluate_one(model, parts, early):
    val, test = parts["val"], parts["test"]
    val_x = truncate(val["text"]) if early else list(val["text"])
    test_x = truncate(test["text"]) if early else list(test["text"])
    v_score = fraud_score(model.predict_proba(val_x), model.classes_)
    threshold = choose_threshold(v_score, val["label"].to_numpy())
    proba = model.predict_proba(test_x)
    t_score = fraud_score(proba, model.classes_)
    pred_types = predict_types(proba, model.classes_, t_score, threshold)
    row = {"threshold": threshold, **binary_metrics(test["label"].to_numpy(), t_score, threshold)}
    summary, per_type = type_metrics(test["fraud_type"].tolist(), pred_types)
    row.update(summary)
    flagged = t_score >= threshold
    per_source = (test.assign(flag=flagged).groupby("source")
                  .apply(lambda g: pd.Series({"n": len(g), "flag_rate": g["flag"].mean(),
                                              "label_mean": g["label"].mean()}), include_groups=False))
    return row, per_type, per_source


def main(model_names):
    merged = pd.read_csv(PROCESSED / "merged.csv")
    rows, type_rows, source_rows = [], [], []
    for test in TESTS:
        parts = load_split(test, merged)
        for name in model_names:
            model = MODELS[name]().fit(list(parts["train"]["text"]), parts["train"]["fraud_type"].tolist())
            for early in (False, True):
                variant = f"first{EARLY_WORDS}" if early else "full"
                row, per_type, per_source = evaluate_one(model, parts, early)
                rows.append({"model": name, "test": test, "variant": variant, **row})
                type_rows += [{"model": name, "test": test, "variant": variant, "fraud_type": t,
                               "f1": f, "support": s} for t, (f, s) in per_type.items()]
                source_rows += [{"model": name, "test": test, "variant": variant, "source": s, **r}
                                for s, r in per_source.iterrows()]
                print(f"{name:14s} {test:11s} {variant:8s} FPR={row['fpr']:.3f} recall={row['recall']:.3f} "
                      f"F1={row['f1_binary']:.3f} AUC={row['roc_auc']:.3f} macroF1(types)={row['macro_f1_types']:.3f}")

    RESULTS.mkdir(exist_ok=True)
    metrics = pd.DataFrame(rows)
    metrics.to_csv(RESULTS / "metrics.csv", index=False)
    per_type = pd.DataFrame(type_rows)
    per_type.to_csv(RESULTS / "metrics_per_type.csv", index=False)
    per_source = pd.DataFrame(source_rows)
    per_source.to_csv(RESULTS / "metrics_per_source.csv", index=False)
    write_summary(metrics, per_type)


def write_summary(metrics, per_type):
    cols = ["model", "test", "variant", "fpr", "recall", "precision", "f1_binary", "roc_auc",
            "macro_f1_types", "tn", "fp", "fn", "tp"]
    md = ["# Results\n", "Threshold chosen on validation so FPR <= 2%. `first50` = Test C (first 50 words).\n",
          "## Binary scam detection + fraud-type macro F1\n", metrics[cols].round(3).to_markdown(index=False), ""]
    full = per_type[per_type["variant"] == "full"]
    pivot = full.pivot_table(index=["model", "test"], columns="fraud_type", values="f1").round(2)
    support = full.groupby("fraud_type")["support"].max()
    md += ["## Per fraud type F1 (full transcripts; types absent from a test set are blank)\n",
           pivot.to_markdown(), "", "Max test support per type: " +
           ", ".join(f"{t}={s}" for t, s in support.items()), ""]
    (RESULTS / "summary.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nresults -> {RESULTS / 'summary.md'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=list(MODELS), choices=list(MODELS))
    main(ap.parse_args().models)
