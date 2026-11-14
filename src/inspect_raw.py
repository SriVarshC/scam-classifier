"""Step 2: inspect each raw dataset (columns, row count, label values, 3 samples).

Read-only: never writes to data/raw/.
Usage: python src/inspect_raw.py
"""
import gzip
import json
from pathlib import Path

import pandas as pd

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"
pd.set_option("display.max_colwidth", 200)
pd.set_option("display.width", 200)


def header(name):
    print("\n" + "=" * 80 + f"\n{name}\n" + "=" * 80)


def show_df(df, label_cols=()):
    print(f"rows: {len(df)}   columns: {list(df.columns)}")
    for c in label_cols:
        if c in df.columns:
            print(f"\nvalue counts for '{c}':\n{df[c].value_counts(dropna=False).head(25).to_string()}")
    print("\n3 sample rows:")
    print(df.sample(3, random_state=42).to_string())


def inspect_bothbosu():
    header("bothbosu  (scam-dialogue_all.csv)")
    df = pd.read_csv(RAW / "bothbosu" / "scam-dialogue_all.csv")
    show_df(df, ["label", "type"])
    tr = pd.read_csv(RAW / "bothbosu" / "scam-dialogue_train.csv")
    te = pd.read_csv(RAW / "bothbosu" / "scam-dialogue_test.csv")
    print(f"\ntrain rows: {len(tr)}, test rows: {len(te)}, train+test == all? {len(tr) + len(te) == len(df)}")


def inspect_robocall():
    header("robocall  (metadata.csv)")
    df = pd.read_csv(RAW / "robocall" / "metadata.csv")
    show_df(df, ["language", "label"])
    n_wav = len(list((RAW / "robocall").rglob("*.wav")))
    print(f"\nwav files on disk: {n_wav}")


def inspect_abcd():
    header("abcd  (abcd_v1.1.json.gz)")
    with gzip.open(RAW / "abcd" / "data" / "abcd_v1.1.json.gz", "rt", encoding="utf-8") as f:
        data = json.load(f)
    print(f"top-level type: {type(data).__name__}, keys: {list(data)[:10]}")
    for split, convs in data.items():
        print(f"  {split}: {len(convs)} conversations")
    first = data[next(iter(data))][0]
    print(f"\nkeys of one conversation: {list(first)}")
    for k, v in first.items():
        preview = json.dumps(v)[:300]
        print(f"  {k}: {preview}")
    flows = pd.Series([c["scenario"]["flow"] for s in data.values() for c in s])
    print(f"\nscenario 'flow' counts:\n{flows.value_counts().to_string()}")


def inspect_usenix():
    header("usenix_romance  (data/<class>/*.json)")
    base = RAW / "usenix_romance" / "data"
    for cls in sorted(p.name for p in base.iterdir() if p.is_dir()):
        files = sorted((base / cls).glob("*.json"))
        print(f"  {cls}: {len(files)} files")
    sample = json.loads(sorted((base / "tax_scam").glob("*.json"))[0].read_text(encoding="utf-8"))
    print(f"\nsample file type: {type(sample).__name__}")
    print(json.dumps(sample, indent=1)[:1500])


if __name__ == "__main__":
    for fn in (inspect_bothbosu, inspect_robocall, inspect_abcd, inspect_usenix):
        try:
            fn()
        except Exception as e:  # keep going so we see every dataset
            print(f"!! {fn.__name__} failed: {type(e).__name__}: {e}")
