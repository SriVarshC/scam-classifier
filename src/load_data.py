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


CALLCENTER_PER_DOMAIN = 600   # balanced sample: Medicare alone is 64% of the 91.7k calls
CALLCENTER_SKIP = {"(reupload)PII_redacted_auto_insurance_script.zip"}  # same 1,749 files as auto_insurance_*
# CallCenterEN redaction tags -> the masks every other source gets from clean.py
CC_NAME_TAGS = {"PERSON_NAME"}
CC_EMAIL_TAGS = {"EMAIL_ADDRESS"}
CC_NUMBER_TAGS = {"PHONE_NUMBER", "MONEY_AMOUNT", "DATE", "TIME", "DURATION", "DATE_INTERVAL", "NUMBER_SEQUENCE",
                  "ACCOUNT_NUMBER", "CREDIT_CARD_NUMBER", "CREDIT_CARD_EXPIRATION", "CREDIT_CARD_CVV",
                  "DATE_OF_BIRTH", "US_SOCIAL_SECURITY_NUMBER", "PASSPORT_NUMBER", "DRIVERS_LICENSE",
                  "HEALTHCARE_NUMBER", "VEHICLE_ID", "PERSON_AGE", "BANKING_INFORMATION", "STATISTICS", "IP_ADDRESS"}
CC_TAG_RE = re.compile(r"\[([A-Z_]+)\]")


def _cc_tags(text):
    """Names -> a token clean.py masks as [NAME]; number-like -> a digit (-> [NUMBER]); email -> an address
    (-> [EMAIL]); every other tag (organization, location, occupation, ...) is left for clean.py to remove."""
    def repl(m):
        tag = m.group(1)
        if tag in CC_NAME_TAGS:
            return " ccpersonnamecc "
        if tag in CC_NUMBER_TAGS:
            return " 0 "
        if tag in CC_EMAIL_TAGS:
            return " x@x "
        return m.group(0)
    return CC_TAG_RE.sub(repl, text)


def load_callcenter_en():
    """CallCenterEN (AIxBlock): real, PII-redacted BPO customer-service calls - all genuine (F0).
    Outbound sales calls count as legal telemarketing (F0). Sampled per domain zip (SEED), read straight
    from the zips (data/raw untouched). No speaker turns in this source."""
    import random
    import zipfile
    from config import SEED
    rng, rows, seen = random.Random(SEED), [], set()
    for z in sorted((RAW / "callcenter_en").glob("*.zip")):
        if z.name in CALLCENTER_SKIP:
            continue
        zf = zipfile.ZipFile(z)
        names = sorted(n for n in zf.namelist() if n.endswith(".json") and "__MACOSX" not in n
                       and not n.rsplit("/", 1)[-1].startswith("._"))
        names = [n for n in names if n.rsplit("/", 1)[-1] not in seen]      # re-uploads overlap other zips
        domain = re.sub(r"[^a-z0-9]+", "_", z.stem.lower().replace("(re-uploaded)", "")).strip("_")
        for n in rng.sample(names, min(CALLCENTER_PER_DOMAIN, len(names))):
            base = n.rsplit("/", 1)[-1]
            seen.add(base)
            try:
                d = json.loads(zf.read(n))
            except ValueError:   # 9 of 61.5k medicare files are empty or truncated in the release
                print(f"[callcenter_en] skipped unreadable file {base}")
                continue
            rows.append({"text": _cc_tags(d.get("text") or ""), "fraud_type": "F0", "scam_type": domain,
                         "is_synthetic": False, "region": "us", "group_id": "callcenter_en_" + base})
    return _finish(pd.DataFrame(rows), "callcenter_en")


HV_NOISE_RE = re.compile(r"\[[a-z ]+\]|<unk>")
# the bank's name incl. ASR variants ("happy/her/helper valley national bank", "harper value national", "harper va")
HV_BANK_RE = re.compile(r"\b(\w+ )?valley national bank\b|\bharper( valley| value| va)?( national)?( bank)?\b")


def load_harper_valley():
    """HarperValleyBank: 1,446 acted (crowd-worker) genuine bank calls -> all F0, synthetic (train only).
    The bank name is replaced by "the bank" and the speakers' names (metadata) are masked in clean.py."""
    base = RAW / "harper_valley" / "data"
    rows = []
    for path in sorted((base / "transcript").glob("*.json")):
        segs = sorted(json.loads(path.read_text(encoding="utf-8")), key=lambda s: s["start_ms"])
        text = " ".join((s.get("human_transcript") or s.get("transcript") or "") for s in segs)
        text = HV_BANK_RE.sub("the bank", HV_NOISE_RE.sub(" ", text))
        meta = json.loads((base / "metadata" / path.name).read_text(encoding="utf-8"))
        names = [meta.get("caller", {}).get("metadata", {}).get("first and last name", ""),
                 meta.get("agent", {}).get("metadata", {}).get("agent_name", "")]
        tasks = sorted({t.get("task_type", "") for t in meta.get("tasks", []) if isinstance(t, dict)})
        rows.append({"text": text, "fraud_type": "F0", "scam_type": "bank_" + "+".join(tasks).replace(" ", "_"),
                     "is_synthetic": True, "region": "us", "known_names": "|".join(filter(None, names)),
                     "group_id": "harper_valley_" + path.stem})
    return _finish(pd.DataFrame(rows), "harper_valley")


LOADERS = [load_robocall, load_youtube_scam, load_callcenter_en, load_bothbosu, load_kaggle_scam_nonscam,
           load_call_transcripts, load_usenix, load_synthetic_own, load_harper_valley]


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
