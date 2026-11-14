"""Load every raw source into one common table -> data/processed/raw_merged.csv.

Text is only joined into one string per conversation here (turns separated by " ");
all normalisation happens in clean.py so every source is treated identically.

Usage: python src/load_data.py
"""
import gzip
import json

import pandas as pd

from config import PROCESSED, RAW, SYNTHETIC_OWN_CSV, UNKNOWN
from label_robocall import label_frame

COLUMNS = ["id", "text", "fraud_type", "label", "source", "scam_type", "is_synthetic",
           "region", "language", "modality", "group_id", "known_names", "label_rule"]


def _finish(df, source):
    df = df.reset_index(drop=True)
    df["id"] = [f"{source}_{i:05d}" for i in range(len(df))]
    df["source"] = source
    df["label"] = (df["fraud_type"] != "F0").astype(int)
    df.loc[df["fraud_type"] == UNKNOWN, "label"] = -1
    for col, default in [("known_names", ""), ("label_rule", "source_label"), ("language", "en"),
                         ("group_id", None)]:
        if col not in df:
            df[col] = default
    df["group_id"] = df["group_id"].fillna(df["id"]).astype(str)
    return df[COLUMNS]


def load_abcd():
    with gzip.open(RAW / "abcd" / "data" / "abcd_v1.1.json.gz", "rt", encoding="utf-8") as f:
        data = json.load(f)
    rows = []
    for convs in data.values():  # ignore ABCD's own split; we re-split
        for c in convs:
            turns = [t for spk, t in c["original"] if spk in ("agent", "customer")]  # drop "action" logs
            rows.append({
                "text": " ".join(turns),
                "fraud_type": "F0",
                "scam_type": c["scenario"]["flow"],
                "is_synthetic": False,  # crowd-sourced role-play chats, real people typing
                "region": "us",
                "modality": "chat",
                "group_id": f"abcd_{c['convo_id']}",
                "known_names": c["scenario"]["personal"].get("customer_name", ""),
            })
    return _finish(pd.DataFrame(rows), "abcd")


def load_robocall():
    meta = pd.read_csv(RAW / "robocall" / "metadata.csv")
    meta = label_frame(meta)
    non_en = meta["language"] != "en"
    meta.loc[non_en, "fraud_type"] = UNKNOWN          # kept, tagged, excluded from train/eval
    meta.loc[non_en, "label_rule"] = "non_english"
    df = pd.DataFrame({
        "text": meta["transcript"].fillna(""),
        "fraud_type": meta["fraud_type"],
        "label_rule": meta["label_rule"],
        "scam_type": meta["label_rule"],
        "is_synthetic": False,
        "region": "us",
        "language": meta["language"],
        "modality": "robocall",
        "group_id": "robocall_" + meta["case_details"].fillna("none"),  # FTC campaign/carrier
    })
    return _finish(df, "robocall")


BOTHBOSU_MAP = {"ssn": "F3", "refund": "F4", "support": "F4", "reward": "F9",
                "delivery": "F0", "insurance": "F0", "telemarketing": "F0", "wrong": "F0"}


def load_bothbosu():
    raw = pd.read_csv(RAW / "bothbosu" / "scam-dialogue_all.csv")
    ft = raw["type"].map(BOTHBOSU_MAP)
    # sanity: our mapping must agree with the dataset's own binary label
    assert ((ft != "F0").astype(int) == raw["label"]).all(), "BothBosu mapping disagrees with label"
    df = pd.DataFrame({"text": raw["dialogue"], "fraud_type": ft, "scam_type": raw["type"],
                       "is_synthetic": True, "region": "unknown", "modality": "call"})
    return _finish(df, "bothbosu")


USENIX_MAP = {"romance_baiting": "F5", "tax_scam": "F3", "e-commerce": "F4", "neutral": "F0"}


def load_usenix():
    base = RAW / "usenix_romance" / "data"
    rows = []
    for cls, ft in USENIX_MAP.items():
        for path in sorted((base / cls).glob("*.json"), key=lambda p: int(p.stem)):
            conv = json.loads(path.read_text(encoding="utf-8"))["conversation"]
            rows.append({"text": " ".join(t["Statement"] for t in conv), "fraud_type": ft,
                         "scam_type": cls, "is_synthetic": True, "region": "unknown", "modality": "chat"})
    return _finish(pd.DataFrame(rows), "usenix_romance")


def load_synthetic_own():
    raw = pd.read_csv(SYNTHETIC_OWN_CSV)
    df = pd.DataFrame({"text": raw["text"], "fraud_type": raw["family"], "scam_type": raw["sub_type"],
                       "is_synthetic": True, "region": "us", "modality": "call",
                       "group_id": "synthetic_own_" + raw["call_id"].astype(str)})
    return _finish(df, "synthetic_own")


LOADERS = [load_abcd, load_robocall, load_bothbosu, load_usenix, load_synthetic_own]


def load_all():
    return pd.concat([fn() for fn in LOADERS], ignore_index=True)


if __name__ == "__main__":
    df = load_all()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out = PROCESSED / "raw_merged.csv"
    df.to_csv(out, index=False)
    print(f"{len(df)} rows -> {out}\n")
    print(pd.crosstab(df["source"], df["fraud_type"], margins=True).to_string())
