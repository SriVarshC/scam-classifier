"""Build train/val/test splits -> data/processed/splits/ (id, fraud_type, label only).

Design "Option 1" (agreed with user 2026-11-14): there are only 2 real genuine calls, so
  * TRAINING uses SYNTHETIC calls only  -> the "real recording = scam" shortcut can't be learned.
  * Thresholds are chosen on a held-out SYNTHETIC validation set (FPR <= 2%).

Test A  (in-distribution): synthetic calls, group split ~70/15/15 stratified by fraud type.
Test B  (never-seen sources):
   B_real    train/val = all synthetic; test = all REAL calls (robocall + youtube_scam).
             Measures recall on real scams (FPR not measurable: only 2 real genuine calls).
   B_<src>   for every synthetic source with BOTH labels: train/val = the other synthetic
             sources; test = that whole source -> FPR + recall on an unseen source.
             (usenix_romance is 100% scam, so it is train-only and never a held-out test.)
Test C  (early decision): evaluate.py truncates every test set to its first 50 words.

UNK rows (no fraud type) are excluded everywhere.

Usage: python src/split.py
"""
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from config import PROCESSED, RESULTS, SEED, UNKNOWN

SPLITS = PROCESSED / "splits"
N_FOLDS = 7  # Test A: 1 test fold + 1 val fold + 5 train folds ≈ 71/14/14
VAL_SHARE = 0.15
OUT_COLS = ["id", "fraud_type", "label"]


def group_folds(df, n_folds=N_FOLDS):
    sgkf = StratifiedGroupKFold(n_splits=n_folds, shuffle=True, random_state=SEED)
    fold = np.empty(len(df), dtype=int)
    for k, (_, idx) in enumerate(sgkf.split(df, df["fraud_type"], df["group_id"])):
        fold[idx] = k
    return fold


def train_val(df):
    """Group-aware train/val split (~85/15) of a training pool."""
    fold = group_folds(df, n_folds=round(1 / VAL_SHARE))
    return df[fold != 0], df[fold == 0]


def write(name, train, val, test):
    for part, df in (("train", train), ("val", val), ("test", test)):
        df[OUT_COLS].to_csv(SPLITS / f"{name}_{part}.csv", index=False)


def check_no_leak(name, *parts):
    names = ("train", "val", "test")
    for i in range(3):
        for j in range(i + 1, 3):
            shared = set(parts[i]["group_id"]) & set(parts[j]["group_id"])
            assert not shared, f"{name}: {len(shared)} groups shared between {names[i]} and {names[j]}"


def describe(name, parts, md):
    md.append(f"## {name}\n")
    rows = []
    for part, df in zip(("train", "val", "test"), parts):
        r = {"split": part, "rows": len(df), "real %": round(100 * (~df["is_synthetic"]).mean(), 1),
             "scam %": round(100 * df["label"].mean(), 1), "genuine": int((df["label"] == 0).sum()),
             "sources": ", ".join(sorted(df["source"].unique()))}
        r.update(df["fraud_type"].value_counts().to_dict())
        rows.append(r)
    tab = pd.DataFrame(rows).fillna(0)
    type_cols = sorted(c for c in tab.columns if c.startswith("F"))
    tab[type_cols] = tab[type_cols].astype(int)
    md += [tab[["split", "rows", "real %", "scam %", "genuine", *type_cols, "sources"]].to_markdown(index=False), ""]


def main():
    df = pd.read_csv(PROCESSED / "merged.csv")
    df = df[(df["fraud_type"] != UNKNOWN) & (df["label"] >= 0)]
    real, synth = df[~df["is_synthetic"]], df[df["is_synthetic"]]
    SPLITS.mkdir(parents=True, exist_ok=True)
    for old in SPLITS.glob("*.csv"):
        old.unlink()
    md = ["# Split summary (Option 1: train on synthetic only)\n"]

    # ---------- Test A: in-distribution synthetic ----------
    fold = group_folds(synth)
    a = (synth[fold >= 2], synth[fold == 1], synth[fold == 0])
    check_no_leak("A", *a)
    write("A", *a)
    describe("Test A — synthetic, in-distribution", a, md)

    # ---------- Test B_real: unseen REAL calls ----------
    tr, va = train_val(synth)
    check_no_leak("B_real", tr, va, real)
    write("B_real", tr, va, real)
    describe("Test B_real — trained on synthetic, tested on all real calls", (tr, va, real), md)

    # ---------- Test B_<src>: leave one synthetic source out ----------
    for src, g in synth.groupby("source"):
        if g["label"].nunique() < 2:
            continue  # single-label source: FPR can't be measured -> train-only
        tr, va = train_val(synth[synth["source"] != src])
        check_no_leak(f"B_{src}", tr, va, g)
        write(f"B_{src}", tr, va, g)
        describe(f"Test B_{src} — {src} never seen in training", (tr, va, g), md)

    md += ["Test C: evaluate.py truncates every test set above to its first 50 words.", ""]
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "split_summary.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md).encode("ascii", "replace").decode())


if __name__ == "__main__":
    main()
