"""Step 4: look for shortcuts in merged.csv BEFORE training.

- label x source x real/synthetic counts
- warn if one label comes mostly from real data and the other mostly from synthetic data
- average transcript length per label and per source

Usage: python src/check_shortcuts.py   -> results/shortcut_check.md
"""
import pandas as pd

from config import PROCESSED, RESULTS

WARN_GAP = 0.5  # warn if the real-data share differs by more than this between labels


def main():
    df = pd.read_csv(PROCESSED / "merged.csv")
    df = df[df["label"] >= 0].copy()  # drop unlabelled rows (non-English / fragments)
    df["label_name"] = df["label"].map({0: "genuine (0)", 1: "scam (1)"})
    df["data"] = df["is_synthetic"].map({True: "synthetic", False: "real"})
    md = ["# Shortcut check (before training)\n", f"Labelled rows: {len(df)}\n"]

    md += ["## 1. Label x source x real/synthetic\n",
           pd.crosstab([df["source"], df["data"]], df["label_name"], margins=True).to_markdown(), ""]
    by_label = pd.crosstab(df["label_name"], df["data"], margins=True)
    share = pd.crosstab(df["label_name"], df["data"], normalize="index").round(3) * 100
    md += ["## 2. Real vs synthetic per label\n", by_label.to_markdown(), "",
           "Share of each label (%):\n", share.to_markdown(), ""]

    real_share = share.get("real", pd.Series(0, index=share.index))
    gap = abs(real_share.get("scam (1)", 0) - real_share.get("genuine (0)", 0)) / 100
    if gap > WARN_GAP:
        md += [f"**⚠️ WARNING — real/synthetic shortcut:** {real_share.get('scam (1)', 0):.1f}% of scams are "
               f"real but only {real_share.get('genuine (0)', 0):.1f}% of genuine calls are.", ""]
    # The other direction: given that a row is real (or synthetic), how predictable is its label?
    for data in ("real", "synthetic"):
        sub = df[df["data"] == data]
        if len(sub) >= 50:
            p = sub["label"].mean()
            if p > 0.9 or p < 0.1:
                md += [f"**⚠️ WARNING — real/synthetic shortcut:** {100 * max(p, 1 - p):.1f}% of {data} rows are "
                       f"{'scams' if p > 0.5 else 'genuine'} ({len(sub)} rows). A model can learn "
                       f"\"{data} recording → {'scam' if p > 0.5 else 'genuine'}\" instead of scam language.", ""]
    for src, g in df.groupby("source"):
        if g["label"].nunique() == 1 and len(g) >= 50:
            md += [f"**⚠️ WARNING — single-label source:** `{src}` is 100% "
                   f"{'scam' if g['label'].iloc[0] == 1 else 'genuine'} ({len(g)} rows, "
                   f"{100 * len(g) / len(df):.0f}% of data) — its style can stand in for the label.", ""]

    md += ["## 3. Transcript length (words)\n",
           "Per label:\n",
           df.groupby("label_name")["n_words"].agg(["count", "mean", "median"]).round(0).to_markdown(), "",
           "Per label x real/synthetic:\n",
           df.groupby(["label_name", "data"])["n_words"].agg(["count", "mean", "median"]).round(0).to_markdown(), "",
           "Per source:\n",
           df.groupby("source")["n_words"].agg(["count", "mean", "median"]).round(0).to_markdown(), "",
           "Per source x label:\n",
           df.pivot_table(index="source", columns="label_name", values="n_words", aggfunc="median").to_markdown(), ""]
    for stat in ("mean", "median"):
        lab = df.groupby("label_name")["n_words"].agg(stat)
        if lab.max() > 1.5 * lab.min():
            md += [f"**⚠️ WARNING — length shortcut:** {stat} length differs by {lab.max() / lab.min():.1f}x "
                   f"between labels ({', '.join(f'{k} {v:.0f}' for k, v in lab.items())} words).", ""]
    src = df.groupby("source")["n_words"].mean()
    if src.max() > 2 * src.min():
        md += [f"**⚠️ WARNING — source length gap:** {src.idxmin()} averages {src.min():.0f} words vs "
               f"{src.idxmax()} {src.max():.0f} words.", ""]

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "shortcut_check.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md).encode("ascii", "replace").decode())  # Windows console can't print emoji


if __name__ == "__main__":
    main()
