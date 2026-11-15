"""Check rule changes on HELD-OUT calls (never the 10 demo calls) -> results/call_analysis/rule_validation.md

Rules only (no LLM). For each group of held-out calls it reports how often each kind of flag fires, so a
rule change can be judged on calls it was not designed on:
  * scam groups: higher is better (recall of the rule);
  * genuine groups: lower is better (false alarms).
Usage: python src/call_analysis/validate_rules.py [--flags-module path/to/flags.py] [--label v2]
"""
import argparse
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from call_analysis import OUT  # noqa: E402
from call_analysis.chunking import chunk_call, normalise  # noqa: E402
from config import PROCESSED  # noqa: E402

GROUPS = {  # name: (filter on raw_merged rows, is_scam)
    "synthetic bank OTP-theft scams (synthetic_own otp_theft)":
        (lambda d: (d.source == "synthetic_own") & (d.scam_type == "otp_theft"), True),
    "synthetic bank scams, all F1 (synthetic_own)":
        (lambda d: (d.source == "synthetic_own") & (d.fraud_type == "F1"), True),
    "real robocall scams": (lambda d: (d.source == "robocall") & (d.label == 1), True),
    "real YouTube scam calls": (lambda d: (d.source == "youtube_scam") & (d.label == 1), True),
    "synthetic genuine bank calls (synthetic_own F0)":
        (lambda d: (d.source == "synthetic_own") & (d.label == 0), False),
    "synthetic genuine calls (bothbosu F0)": (lambda d: (d.source == "bothbosu") & (d.label == 0), False),
    "synthetic genuine calls (kaggle non-scam)":
        (lambda d: (d.source == "kaggle_scam_nonscam") & (d.label == 0), False),
    # added 2026-11-15: REAL genuine calls (no speaker labels -> every line is checked = worst case)
    "REAL genuine customer-service calls (callcenter_en)":
        (lambda d: (d.source == "callcenter_en") & (d.label == 0), False),
    "acted genuine bank calls: cards, PINs, passwords (harper_valley)":
        (lambda d: (d.source == "harper_valley") & (d.label == 0), False),
}


def load_flags_module(path):
    spec = importlib.util.spec_from_file_location("flags_under_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rates(flags_mod, df, use_script=False, matcher=None):
    out = {"calls": len(df), "F01 one-time code/PIN": 0, "any critical": 0, "any high or critical": 0,
           "F20 urgency": 0, "F17 scam script": 0, "T06 awarded": 0}
    for row in df.itertuples():
        call = {"id": row.id, "transcript": normalise(row.text), "chunks": chunk_call(row.text, row.source)}
        found = [f for ch in call["chunks"] for f in flags_mod.rule_flags_in_chunk(ch)]
        if use_script:
            found += [h for h in (matcher.in_chunk(ch) for ch in call["chunks"]) if h][:1]
        ids = {f["id"] for f in found}
        sev = {f["severity"] for f in found}
        reds = [f for f in found if f["severity"] != "trust"]
        out["F01 one-time code/PIN"] += "F01" in ids
        out["any critical"] += "critical" in sev
        out["any high or critical"] += bool(sev & {"critical", "high"})
        out["F20 urgency"] += "F20" in ids
        out["F17 scam script"] += "F17" in ids
        out["T06 awarded"] += flags_mod.t06_holds(call, reds) is not None
    n = max(out["calls"], 1)
    return {k: (v if k == "calls" else f"{100 * v / n:.0f}%") for k, v in out.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--flags-module", default=str(Path(__file__).with_name("flags.py")))
    ap.add_argument("--label", default="current")
    ap.add_argument("--with-script", action="store_true", help="also run F17 (embeddings) on the scam groups")
    ap.add_argument("--max-per-group", type=int, default=400)
    args = ap.parse_args()
    flags_mod = load_flags_module(args.flags_module)
    matcher = flags_mod.ScriptMatcher() if args.with_script else None
    demo = set(pd.read_csv(OUT / "selected_calls.csv")["id"])
    raw = pd.read_csv(PROCESSED / "raw_merged.csv")
    raw = raw[(raw.fraud_type != "UNK") & (raw.label >= 0) & ~raw.id.isin(demo)]  # held-out only
    rows = []
    for name, (filt, is_scam) in GROUPS.items():
        df = raw[filt(raw)].sample(frac=1, random_state=42).head(args.max_per_group)
        rows.append({"group": name, "kind": "scam (higher = better)" if is_scam else "genuine (lower = better)",
                     **rates(flags_mod, df, use_script=args.with_script and is_scam, matcher=matcher)})
    table = pd.DataFrame(rows)
    print(f"\n### Rules: {args.label}\n")
    print(table.to_markdown(index=False))
    return table


if __name__ == "__main__":
    main()
