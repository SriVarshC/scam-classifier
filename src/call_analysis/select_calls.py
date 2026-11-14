"""Step 1: pick the 10 demo calls (SEED = 42) -> results/call_analysis/selected_calls.csv

  4 real scam calls      : 2 robocall (with audio on disk) + 2 youtube_scam
  3 synthetic scam calls : F1 bank (synthetic_own), F3 government (bothbosu ssn), F4 tech support (bothbosu support)
  3 genuine calls        : the 2 real genuine calls (robocall, F0) + 1 synthetic genuine bank call
                           (synthetic_own genuine_fraud_alert)

Only calls that survived cleaning/dedup and have a fraud type are eligible. Real scams need >= 40 words
so the simulated stream has more than one chunk. If any category is short, this script stops loudly.

Usage: python src/call_analysis/select_calls.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # make src/ importable when run as a script

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from call_analysis import OUT  # noqa: E402
from config import PROCESSED, RAW, SEED, UNKNOWN

MIN_REAL_SCAM_WORDS = 40


def eligible_calls():
    merged = pd.read_csv(PROCESSED / "merged.csv")
    merged["base_id"] = merged["id"].str.replace(r"_c\d+$", "", regex=True)
    ok = set(merged[(merged["label"] >= 0) & (merged["fraud_type"] != UNKNOWN)]["base_id"])
    raw = pd.read_csv(PROCESSED / "raw_merged.csv")
    raw = raw[raw["id"].isin(ok)].copy()
    raw["n_words"] = raw["text"].str.split().str.len()
    return raw


def pick(pool, n, name, rng):
    if len(pool) < n:
        raise SystemExit(f"STOP: category '{name}' has only {len(pool)} eligible calls, needs {n}.")
    return pool.iloc[rng.choice(len(pool), size=n, replace=False)].assign(category=name)


def robocall_audio_ids():
    """Robocall ids whose audio file exists (loader numbers robocall rows in metadata.csv order)."""
    meta = pd.read_csv(RAW / "robocall" / "metadata.csv")
    exists = meta["file_name"].map(lambda f: (RAW / "robocall" / f).exists())
    return {f"robocall_{i:05d}" for i in meta.index[exists]}


def main():
    rng = np.random.default_rng(SEED)
    calls = eligible_calls()
    real, synth = calls[~calls["is_synthetic"]], calls[calls["is_synthetic"]]
    audio_ids = robocall_audio_ids()

    real_scam = real[(real["label"] == 1) & (real["n_words"] >= MIN_REAL_SCAM_WORDS)]
    groups = [
        pick(real_scam[(real_scam["source"] == "robocall") & real_scam["id"].isin(audio_ids)],
             2, "real scam (robocall)", rng),
        pick(real_scam[real_scam["source"] == "youtube_scam"], 2, "real scam (youtube)", rng),
        pick(synth[(synth["source"] == "synthetic_own") & (synth["fraud_type"] == "F1")],
             1, "synthetic scam: bank (F1)", rng),
        pick(synth[(synth["source"] == "bothbosu") & (synth["scam_type"] == "ssn")],
             1, "synthetic scam: government (F3)", rng),
        pick(synth[(synth["source"] == "bothbosu") & (synth["scam_type"] == "support")],
             1, "synthetic scam: tech support (F4)", rng),
    ]
    real_genuine = real[real["label"] == 0]
    if len(real_genuine) != 2:
        raise SystemExit(f"STOP: expected the 2 real genuine calls, found {len(real_genuine)}.")
    groups.append(real_genuine.assign(category="real genuine (robocall, rule-labelled F0)"))
    groups.append(pick(synth[(synth["source"] == "synthetic_own") & (synth["scam_type"] == "genuine_fraud_alert")],
                       1, "synthetic genuine: bank", rng))

    sel = pd.concat(groups)
    out = pd.DataFrame({
        "id": sel["id"], "source": sel["source"],
        "true_label": sel["label"].map({1: "scam", 0: "genuine"}),
        "scam_type": sel["fraud_type"] + " / " + sel["scam_type"].astype(str),
        "is_synthetic": sel["is_synthetic"], "n_words": sel["n_words"], "category": sel["category"],
        "note": np.where(sel["category"].str.startswith("real genuine"),
                         "FTC illegal-robocall dataset; labelled genuine by keyword rule - weak genuine example", ""),
    })
    OUT.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT / "selected_calls.csv", index=False)
    print(out.to_string(index=False))
    return out


if __name__ == "__main__":
    main()
