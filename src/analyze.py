"""Step 7: look for shortcuts and sanity-check the pipeline. Run after run_experiment.py.

1. Top 30 TF-IDF features per class -> results/top_words.txt (suspicious format tokens flagged)
2. 20 false positives / 20 false negatives (TF-IDF + LR) -> results/errors_fp.csv, errors_fn.csv
3. Test A vs Test B gap per model -> results/analysis.md
4. Label-shuffle check: TF-IDF + LR trained on shuffled labels must score ROC-AUC ≈ 0.5
   (accuracy is not used: the test set is ~93% genuine, so accuracy would be high by default)

Usage: python src/analyze.py
"""
import numpy as np
import pandas as pd

from config import RESULTS, SEED
from evaluate import binary_metrics, choose_threshold, fraud_score
from fit_cache import fit_or_load
from models import TfidfLR
from run_experiment import TESTS, load_split
from config import PROCESSED

# Tokens that describe *format* (greetings, call openers, transcription fillers, IVR prompts,
# speaker tags, masking placeholders) rather than scam content.
SUSPICIOUS = {"uh", "um", "hmm", "ok", "okay", "yeah", "number", "name", "email", "press", "press number",
              "please press", "id", "order id", "hi", "hello", "hey", "good morning", "good afternoon",
              "thanks", "thank", "thank you", "how can", "can help", "help you", "can i", "i help",
              "help you today", "how may", "may i", "anything else", "is there", "there anything", "great",
              "caller", "receiver", "agent", "customer", "user", "assistant", "recipient", "speaker",
              "this is", "calling", "call", "speak", "talk", "ma am", "sir", "goodbye", "bye", "have a"}


def top_words(model, k=30):
    names = np.array(model.vec.get_feature_names_out())
    lines, flagged_total = [], 0
    for i, cls in enumerate(model.classes_):
        top = names[np.argsort(model.clf.coef_[i])[-k:][::-1]]
        flagged = [w for w in top if w in SUSPICIOUS or "number" in w or "name" in w.split()]
        flagged_total += len(flagged)
        lines.append(f"== {cls} ({len(flagged)}/{k} flagged as format/style tokens)")
        lines.append(", ".join(f"*{w}*" if w in flagged else w for w in top))
        lines.append("")
    return "\n".join(lines), flagged_total


def collect_errors(merged):
    fps, fns = [], []
    for test in TESTS:
        parts = load_split(test, merged)
        model = fit_or_load("tfidf_lr", TfidfLR, list(parts["train"]["text"]),
                            parts["train"]["fraud_type"].tolist(), parts["train"]["id"].tolist())
        thr = choose_threshold(fraud_score(model.predict_proba(list(parts["val"]["text"])), model.classes_),
                               parts["val"]["label"].to_numpy())
        df = parts["test"].assign(score=fraud_score(model.predict_proba(list(parts["test"]["text"])),
                                                    model.classes_), test=test, threshold=thr)
        fps.append(df[(df["label"] == 0) & (df["score"] >= thr)])
        fns.append(df[(df["label"] == 1) & (df["score"] < thr)])
        if test == "A":
            a_model = model
    cols = ["test", "id", "source", "fraud_type", "score", "threshold", "text"]
    def pick(frames, n=20):  # round-robin across tests so every test is represented
        df = pd.concat(frames).sample(frac=1, random_state=SEED)
        return df.assign(_r=df.groupby("test").cumcount()).sort_values("_r").head(n)[cols]
    return a_model, pick(fps), pick(fns), sum(map(len, fps)), sum(map(len, fns))


def gap_table():
    m = pd.read_csv(RESULTS / "metrics.csv")
    m = m[m["variant"] == "full"]
    a = m[m["test"] == "A"].set_index("model")
    loso = m[m["test"].str.startswith("B_") & (m["test"] != "B_real")]  # unseen synthetic sources
    b = loso.groupby("model")[["f1_binary", "fpr", "recall", "roc_auc"]].mean()
    real = m[m["test"] == "B_real"].set_index("model")
    return pd.DataFrame({"A F1": a["f1_binary"], "B F1 (avg unseen sources)": b["f1_binary"],
                         "gap F1": a["f1_binary"] - b["f1_binary"],
                         "A FPR": a["fpr"], "B FPR (avg)": b["fpr"],
                         "A AUC": a["roc_auc"], "B AUC (avg)": b["roc_auc"],
                         "real-scam recall (B_real)": real["recall"]}).round(3)


def shuffle_check(merged, seeds=(SEED, 0, 1, 2, 3)):
    """Mean/std ROC-AUC over several shuffles (one shuffle is noisy: only ~100 test scams)."""
    parts = load_split("A", merged)
    overlap = len(set(parts["train"]["text"]) & set(parts["test"]["text"]))
    aucs = []
    for seed in seeds:
        y = parts["train"]["fraud_type"].sample(frac=1, random_state=seed).tolist()
        model = fit_or_load("tfidf_lr", TfidfLR, list(parts["train"]["text"]), y,
                           parts["train"]["id"].tolist())
        test_s = fraud_score(model.predict_proba(list(parts["test"]["text"])), model.classes_)
        aucs.append(binary_metrics(parts["test"]["label"].to_numpy(), test_s, 0.5)["roc_auc"])
    return {"auc_mean": float(np.mean(aucs)), "auc_std": float(np.std(aucs)), "aucs": aucs,
            "text_overlap": overlap}


def main():
    merged = pd.read_csv(PROCESSED / "merged.csv")
    a_model, fp, fn, n_fp, n_fn = collect_errors(merged)
    words, n_flagged = top_words(a_model)
    (RESULTS / "top_words.txt").write_text(words, encoding="utf-8")
    fp.to_csv(RESULTS / "errors_fp.csv", index=False)
    fn.to_csv(RESULTS / "errors_fn.csv", index=False)
    gaps = gap_table()
    sh = shuffle_check(merged)
    ok = abs(sh["auc_mean"] - 0.5) < 0.1 and sh["text_overlap"] == 0

    md = ["# Analysis\n",
          "## 1. Top TF-IDF features (Test A model)\n",
          f"{n_flagged} of the {30 * len(a_model.classes_)} top features (30 per class) are format/style tokens "
          f"(marked *like this* in `top_words.txt`). F0 excerpt:\n",
          "```", words.split("\n\n")[0], "```", "",
          "## 2. Errors (TF-IDF + LR, all tests)\n",
          f"False positives: {n_fp} total, sample of {len(fp)} in `errors_fp.csv` — by source: "
          f"{fp['source'].value_counts().to_dict()}",
          f"False negatives: {n_fn} total, sample of {len(fn)} in `errors_fn.csv` — by type: "
          f"{fn['fraud_type'].value_counts().to_dict()}", "",
          "## 3. Test A vs Test B gap\n", gaps.to_markdown(), "",
          "## 4. Label-shuffle sanity check (TF-IDF + LR, Test A)\n",
          f"ROC-AUC with shuffled training labels = **{sh['auc_mean']:.3f} ± {sh['auc_std']:.3f}** over "
          f"{len(sh['aucs'])} shuffles ({', '.join(f'{a:.2f}' for a in sh['aucs'])}); "
          f"exact train/test text overlap = {sh['text_overlap']}. "
          f"{'PASS — ≈ 0.5, no leakage through the pipeline.' if ok else 'FAIL — investigate leakage.'}", ""]
    (RESULTS / "analysis.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md).encode("ascii", "replace").decode())  # Windows console can't print ≈ / —


if __name__ == "__main__":
    main()
