"""Normalise every source identically, mask names/numbers, drop short texts and duplicates.

raw_merged.csv -> merged.csv (+ results/data_summary.md)

Order note: name masking runs *before* lowercasing because it relies on capitalisation;
otherwise the steps follow CLAUDE.md.

Usage: python src/clean.py
"""
import re

import pandas as pd
from datasketch import MinHash, MinHashLSH

import math

import numpy as np

from config import CHUNK_WORDS, MAX_CHUNKS, MIN_WORDS, NEAR_DUP_THRESHOLD, PROCESSED, RESULTS, SEED

URL_RE = re.compile(r"https?://\S+|www\.\S+|\b[\w-]+\.(com|net|org|gov|io)\b\S*", re.I)
EMAIL_RE = re.compile(r"\S+@\S+")
SPEAKER_RE = re.compile(r"(?i)(^|\s)(caller|receiver|recipient|agent|customer|user|assistant|scammer|victim"
                        r"|speaker\s?\d*)\s*:")
# A capitalised word (or two) right after a self-introduction / title is treated as a person's name.
NAME_INTRO_RE = re.compile(r"\b([Mm]y name is|[Tt]his is|[Ii]s this|i am|i'm|name's|speaking with|[Hh]i|[Hh]ello|[Hh]ey"
                           r"|[Dd]ear|[Tt]hanks|[Tt]hank you|Mr\.?|Ms\.?|Mrs\.?|Miss|Officer|Dr\.?|Agent)"
                           r",?\s+([A-Z][a-z]+)(\s+[A-Z][a-z]+)?")
NOT_NAMES = {"Amazon", "Apple", "Microsoft", "Google", "The", "Your", "Social", "Customer", "Officer", "Agent",
             "Federal", "Department", "Internal", "Bank", "Chase", "Wells", "Discover", "Spectrum", "Just",
             "Calling", "Regarding", "From", "With", "Not", "Very", "So", "Here", "Sure", "Going", "Sorry",
             "There", "Good", "Thanks", "Thank", "How", "Yes", "Yeah", "Okay", "Ok", "Hello", "Hi", "This",
             "Is", "It", "We", "What", "Who", "Sir", "Madam", "Ma", "Everyone", "All", "Again", "Grandpa",
             "Grandma", "Mom", "Dad", "Honey", "Please", "Great", "Well", "Oh", "Um", "Uh", "That", "I"}
DIGIT_TOKEN_RE = re.compile(r"\S*\d\S*")
PUNCT_RE = re.compile(r"[^\w\s\[\]]|_")
REPEAT_NUM_RE = re.compile(r"(\[NUMBER\]\s*){2,}")


def _mask_intro_names(text):
    def repl(m):
        first, second = m.group(2), (m.group(3) or "").strip()
        if first in NOT_NAMES:
            return m.group(0)
        keep_second = f" {second}" if second in NOT_NAMES else ""  # e.g. "Chris From" -> keep "From"
        return f"{m.group(1)} [NAME]{keep_second}"
    return NAME_INTRO_RE.sub(repl, text)


def clean_text(text, known_names=""):
    text = str(text)
    text = URL_RE.sub(" ", EMAIL_RE.sub(" [EMAIL] ", text))
    for full in filter(None, str(known_names).split("|")):
        for part in sorted({full, *full.split()}, key=len, reverse=True):
            if len(part) > 1:
                text = re.sub(rf"\b{re.escape(part)}\b", " [NAME] ", text, flags=re.I)
    text = _mask_intro_names(text)
    text = SPEAKER_RE.sub(" ", text)
    text = text.replace("[NAME]", "\x00N").replace("[EMAIL]", "\x00E")      # protect placeholders
    text = text.replace("[", " ").replace("]", " ").lower()
    text = DIGIT_TOKEN_RE.sub(" [NUMBER] ", text)
    text = text.replace("\x00n", " [NAME] ").replace("\x00e", " [EMAIL] ")
    text = PUNCT_RE.sub(" ", text)
    text = REPEAT_NUM_RE.sub("[NUMBER] ", text)
    text = text.replace("[number]", "[NUMBER]").replace("[name]", "[NAME]").replace("[email]", "[EMAIL]")
    return re.sub(r"\s+", " ", text).strip()


def chunk_long_texts(df, max_words=CHUNK_WORDS, max_chunks=MAX_CHUNKS):
    """Cut texts longer than max_words into equal pieces; keep up to max_chunks evenly spaced
    pieces (always the first and last). Pieces keep the parent's group_id so splits keep them together."""
    rows = []
    for row in df.to_dict("records"):
        words = row["text"].split()
        n_pieces = math.ceil(len(words) / max_words)
        if n_pieces <= 1:
            rows.append(row)
            continue
        size = math.ceil(len(words) / n_pieces)
        pieces = [words[i:i + size] for i in range(0, len(words), size)]
        keep = sorted(set(np.linspace(0, len(pieces) - 1, min(max_chunks, len(pieces))).round().astype(int)))
        for k in keep:
            rows.append({**row, "id": f"{row['id']}_c{k}", "text": " ".join(pieces[k])})
    return pd.DataFrame(rows)


def _minhash(text, num_perm=128):
    words = text.split()
    m = MinHash(num_perm=num_perm, seed=SEED)
    for i in range(max(1, len(words) - 2)):
        m.update(" ".join(words[i:i + 3]).encode("utf-8"))
    return m


def drop_near_duplicates(df, threshold=NEAR_DUP_THRESHOLD):
    """Keep the first row of each near-duplicate cluster (real sources are loaded first)."""
    lsh = MinHashLSH(threshold=threshold, num_perm=128)
    keep, dup_of = [], {}
    for idx, text in zip(df.index, df["text"]):
        mh = _minhash(text)
        hits = lsh.query(mh)
        if hits:
            dup_of[idx] = hits[0]
        else:
            lsh.insert(idx, mh)
            keep.append(idx)
    return df.loc[keep], dup_of


def summarise(df, removed):
    lines = ["# Data summary (after cleaning)\n"]
    g = df.groupby("source")
    tab = pd.DataFrame({
        "rows": g.size(),
        "legit (0)": g["label"].apply(lambda s: (s == 0).sum()),
        "fraud (1)": g["label"].apply(lambda s: (s == 1).sum()),
        "unlabelled": g["label"].apply(lambda s: (s == -1).sum()),
        "mean words": g["n_words"].mean().round(0),
        "median words": g["n_words"].median(),
        "synthetic": g["is_synthetic"].first(),
    })
    tab = tab.join(removed, how="left").fillna(0)
    lines += ["## Per source\n", tab.to_markdown(), ""]
    lines += ["## Source x fraud type\n", pd.crosstab(df["source"], df["fraud_type"], margins=True).to_markdown(), ""]
    real = df[~df["is_synthetic"] & (df["label"] >= 0)]
    lines += ["## Real (non-synthetic) rows per fraud type — the only rows allowed in val/test\n",
              real["fraud_type"].value_counts().sort_index().to_frame("real rows").to_markdown(), ""]
    means = tab["mean words"]
    if means.max() > 2 * means.min():
        lines += [f"**WARNING:** mean length differs > 2x between sources "
                  f"({means.idxmin()} {means.min():.0f} vs {means.idxmax()} {means.max():.0f} words) "
                  f"— length could become a source shortcut.", ""]
    return "\n".join(lines)


def main():
    df = pd.read_csv(PROCESSED / "raw_merged.csv", keep_default_na=False)
    df["label"] = df["label"].astype(int)
    df["is_synthetic"] = df["is_synthetic"].astype(str).eq("True")
    start = df.groupby("source").size()

    df["text"] = [clean_text(t, n) for t, n in zip(df["text"], df["known_names"])]
    df["n_words"] = df["text"].str.split().str.len()
    df = df[df["n_words"] >= MIN_WORDS]
    after_short = df.groupby("source").size()

    df = chunk_long_texts(df)
    df["n_words"] = df["text"].str.split().str.len()
    after_chunk = df.groupby("source").size()

    df = df.drop_duplicates("text")
    after_exact = df.groupby("source").size()

    df, dup_of = drop_near_duplicates(df)
    after_near = df.groupby("source").size()

    removed = pd.DataFrame({
        "raw rows": start,
        "dropped short": start - after_short,
        "added by chunking": after_chunk - after_short,
        "dropped exact dup": after_chunk - after_exact,
        "dropped near dup": after_exact - after_near,
    }).fillna(0).astype(int)

    out_cols = ["id", "text", "fraud_type", "label", "source", "scam_type", "is_synthetic", "region",
                "language", "modality", "group_id", "label_rule", "n_words"]
    df[out_cols].to_csv(PROCESSED / "merged.csv", index=False)

    summary = summarise(df, removed)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "data_summary.md").write_text(summary, encoding="utf-8")
    print(summary)
    print(f"\n{len(df)} rows -> {PROCESSED / 'merged.csv'}")


if __name__ == "__main__":
    main()
