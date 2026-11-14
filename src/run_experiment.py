"""Train every model on every split, evaluate, and write results/metrics.csv + results/summary.md.

Usage: python src/run_experiment.py [--models keyword_rules tfidf_lr]
"""
import argparse

import numpy as np
import pandas as pd

from config import PROCESSED, RESULTS
from evaluate import binary_metrics, choose_threshold, fraud_score, predict_types, type_metrics
from models import MODELS, ZeroShotLLM

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


def run_llm(llm_model, n_sample, n_early, workers=1):
    """Zero-shot LLM (no training) on a fixed random sample of every test set.
    It is the same model for every split, so ONE shared validation sample (from Test A val)
    sets the FPR <= 2% threshold. Writes results/metrics_llm*.csv + results/summary_llm.md."""
    from config import SEED
    merged = pd.read_csv(PROCESSED / "merged.csv")
    model = ZeroShotLLM(model=llm_model, workers=workers).fit([], [])
    val = load_split("A", merged)["val"]
    val = val.sample(min(n_sample, len(val)), random_state=SEED)
    rows, type_rows, source_rows = [], [], []
    for test in TESTS:
        t = load_split(test, merged)["test"]
        t = t.sample(min(n_sample, len(t)), random_state=SEED)
        for early in (False, True):
            n = n_early if early else n_sample
            parts = {"val": val.head(n), "test": t.head(n)}
            variant = f"first{EARLY_WORDS}" if early else "full"
            row, per_type, per_source = evaluate_one(model, parts, early)
            rows.append({"model": f"zero_shot_llm ({llm_model})", "test": test, "variant": variant,
                         "n_test": len(parts["test"]), **row})
            type_rows += [{"model": "zero_shot_llm", "test": test, "variant": variant, "fraud_type": k,
                           "f1": f, "support": s} for k, (f, s) in per_type.items()]
            source_rows += [{"model": "zero_shot_llm", "test": test, "variant": variant, "source": s, **r}
                            for s, r in per_source.iterrows()]
            print(f"LLM {test:22s} {variant:8s} n={len(parts['test']):3d} FPR={row['fpr']:.3f} "
                  f"recall={row['recall']:.3f} F1={row['f1_binary']:.3f} AUC={row['roc_auc']:.3f} "
                  f"macroF1(types)={row['macro_f1_types']:.3f}", flush=True)
    metrics = pd.DataFrame(rows)
    metrics.to_csv(RESULTS / "metrics_llm.csv", index=False)
    pd.DataFrame(type_rows).to_csv(RESULTS / "metrics_llm_per_type.csv", index=False)
    pd.DataFrame(source_rows).to_csv(RESULTS / "metrics_llm_per_source.csv", index=False)
    cols = ["model", "test", "variant", "n_test", "fpr", "recall", "precision", "f1_binary", "roc_auc",
            "macro_f1_types", "tn", "fp", "fn", "tp"]
    md = ["# Zero-shot LLM results\n",
          f"Model `{llm_model}` via Ollama, no training. Random sample of {n_sample} calls per test set "
          f"({n_early} for `first{EARLY_WORDS}`); threshold from a shared validation sample (FPR <= 2%).\n",
          metrics[cols].round(3).to_markdown(index=False), ""]
    (RESULTS / "summary_llm.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nresults -> {RESULTS / 'summary_llm.md'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=list(MODELS), choices=list(MODELS))
    ap.add_argument("--use-llm", action="store_true", help="run ONLY the zero-shot LLM (needs Ollama running)")
    ap.add_argument("--llm-model", default="qwen2.5:3b")
    ap.add_argument("--llm-sample", type=int, default=200)
    ap.add_argument("--llm-early-sample", type=int, default=60)
    ap.add_argument("--llm-workers", type=int, default=1, help="parallel requests (= OLLAMA_NUM_PARALLEL)")
    args = ap.parse_args()
    if args.use_llm:
        run_llm(args.llm_model, args.llm_sample, args.llm_early_sample, args.llm_workers)
    else:
        main(args.models)
