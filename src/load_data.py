"""Load every raw source into one common table -> data/processed/raw_merged.csv.

PHONE CALLS ONLY: every row must be a phone-call transcript (real or synthetic).
Chats, emails, SMS and typed conversations are never loaded (ABCD and the USENIX romance /
neutral chats were removed on 2026-11-14 for this reason).

Text is only joined into one string per conversation here (turns separated by " ");
all normalisation happens in clean.py so every source is treated identically.

Usage: python src/load_data.py
"""
import json
import re

import pandas as pd

from config import PROCESSED, RAW, SYNTHETIC_OWN_CSV, UNKNOWN
from label_robocall import label_frame, label_transcript

COLUMNS = ["id", "text", "fraud_type", "label", "source", "scam_type", "is_synthetic",
           "region", "language", "modality", "group_id", "known_names", "label_rule"]


def _finish(df, source):
    df = df.reset_index(drop=True)
    df["id"] = [f"{source}_{i:05d}" for i in range(len(df))]
    df["source"] = source
    df["label"] = (df["fraud_type"] != "F0").astype(int)
    df.loc[df["fraud_type"] == UNKNOWN, "label"] = -1
    df.loc[df["fraud_type"] == UNKNOWN, "label"] = df.get("known_label", df["label"])
    for col, default in [("known_names", ""), ("label_rule", "source_label"), ("language", "en"),
                         ("group_id", None), ("modality", "call")]:
        if col not in df:
            df[col] = default
    df["group_id"] = df["group_id"].fillna(df["id"]).astype(str)
    return df[COLUMNS]


def type_known_scams(texts):
    """Fraud type for rows the source already marks as scam: keyword rules; a rule saying F0
    (benign) or no match -> UNK, so a known scam is never relabelled as genuine."""
    out = [label_transcript(t) for t in texts]
    types = [UNKNOWN if ft in ("F0", UNKNOWN) else ft for ft, _ in out]
    rules = [rule if ft not in ("F0", UNKNOWN) else "no_type_match" for ft, rule in out]
    return types, rules


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
                       "is_synthetic": True, "region": "unknown"})
    return _finish(df, "bothbosu")


# Only the phone-call-style USENIX classes. romance_baiting (dating-app texting) and
# neutral (AI-assistant chat) are NOT phone calls and are never loaded.
USENIX_MAP = {"tax_scam": "F3", "e-commerce": "F4"}


def load_usenix():
    base = RAW / "usenix_romance" / "data"
    rows = []
    for cls, ft in USENIX_MAP.items():
        for path in sorted((base / cls).glob("*.json"), key=lambda p: int(p.stem)):
            conv = json.loads(path.read_text(encoding="utf-8"))["conversation"]
            rows.append({"text": " ".join(t["Statement"] for t in conv), "fraud_type": ft,
                         "scam_type": cls, "is_synthetic": True, "region": "unknown"})
    return _finish(pd.DataFrame(rows), "usenix_romance")


def load_synthetic_own():
    raw = pd.read_csv(SYNTHETIC_OWN_CSV)
    df = pd.DataFrame({"text": raw["text"], "fraud_type": raw["family"], "scam_type": raw["sub_type"],
                       "is_synthetic": True, "region": "us",
                       "group_id": "synthetic_own_" + raw["call_id"].astype(str)})
    return _finish(df, "synthetic_own")


def _read_blocks(path):
    """teeconnie files: one call per blank-line-separated block; scam file numbers them '1.\\t'."""
    blocks = [b.strip() for b in path.read_text(encoding="utf-8").split("\n\n") if b.strip()]
    return [re.sub(r"^\d+\.\s*", "", b) for b in blocks]


def load_kaggle_scam_nonscam():
    base = RAW / "kaggle_scam_nonscam"
    scams, genuine = _read_blocks(base / "English_Scam.txt"), _read_blocks(base / "English_NonScam.txt")
    types, rules = type_known_scams(scams)
    df = pd.DataFrame({
        "text": scams + genuine,
        "fraud_type": types + ["F0"] * len(genuine),
        "label_rule": rules + ["source_label"] * len(genuine),
        "known_label": [1] * len(scams) + [0] * len(genuine),
        "scam_type": ["scam"] * len(scams) + ["non_scam"] * len(genuine),
        "is_synthetic": True, "region": "unknown",
    })
    return _finish(df, "kaggle_scam_nonscam")


def load_youtube_scam():
    raw = pd.read_csv(RAW / "youtube_scam" / "FullTranscriptData.csv", encoding_errors="replace")
    types, rules = type_known_scams(raw["Content"].fillna("").tolist())
    df = pd.DataFrame({
        "text": raw["Content"].fillna(""), "fraud_type": types, "label_rule": rules, "known_label": 1,
        "scam_type": raw["Source"].str.extract(r"ab_channel=([^&]+)")[0].fillna("unknown"),
        "is_synthetic": False,  # real scammer calls recorded by scam-baiters
        "region": "unknown",
        "group_id": "youtube_" + raw["Source"].str.extract(r"v=([^&]+)")[0].fillna(raw["ID"].astype(str)),
    })
    return _finish(df, "youtube_scam")


CT_SCAM = {"scam", "scam_response", "potential_scam", "highly_suspicious"}
CT_GENUINE = {"neutral", "legitimate"}


def load_call_transcripts():
    """65 AI-call-screening conversations, labelled per turn. Conversation label (agreed with user):
    scam if any turn is scam-like, genuine if every turn is neutral/legitimate, otherwise dropped."""
    raw = pd.read_csv(RAW / "call_transcripts" / "BETTER30.csv", encoding_errors="replace")
    raw["L"] = raw["LABEL"].str.strip()
    rows = []
    for cid, g in raw.sort_values(["CONVERSATION_ID", "CONVERSATION_STEP"]).groupby("CONVERSATION_ID"):
        labels = set(g["L"])
        verdict = 1 if labels & CT_SCAM else (0 if labels <= CT_GENUINE else None)
        if verdict is None:
            continue
        turns = g["TEXT"].fillna("").str.replace(r"\[Step:\s*\d+\]", " ", regex=True)
        turns = turns.str.replace(r"\.\.\.", " ", regex=True)
        rows.append({"text": " ".join(turns), "known_label": verdict, "group_id": f"call_transcripts_{cid}"})
    df = pd.DataFrame(rows)
    types, rules = type_known_scams(df["text"].tolist())
    df["fraud_type"] = [t if k == 1 else "F0" for t, k in zip(types, df["known_label"])]
    df["label_rule"] = [r if k == 1 else "source_label" for r, k in zip(rules, df["known_label"])]
    df["scam_type"] = df["known_label"].map({1: "scam", 0: "genuine"})
    df["is_synthetic"], df["region"] = True, "unknown"
    return _finish(df, "call_transcripts")


LOADERS = [load_robocall, load_youtube_scam, load_bothbosu, load_kaggle_scam_nonscam,
           load_call_transcripts, load_usenix, load_synthetic_own]


def load_all():
    return pd.concat([fn() for fn in LOADERS], ignore_index=True)


if __name__ == "__main__":
    df = load_all()
    PROCESSED.mkdir(parents=True, exist_ok=True)
    out = PROCESSED / "raw_merged.csv"
    df.to_csv(out, index=False)
    print(f"{len(df)} rows -> {out}\n")
    print(pd.crosstab(df["source"], df["fraud_type"], margins=True).to_string())
    unk = df[(df["fraud_type"] == UNKNOWN) & (df["label"] == 1)]
    review = unk.sample(min(30, len(unk)), random_state=42)[["id", "source", "text"]]
    review.to_csv(PROCESSED / "untyped_scams_review.csv", index=False)
    print(f"\nscams with no fraud type (UNK, label 1): {len(unk)} -> sample in untyped_scams_review.csv")
