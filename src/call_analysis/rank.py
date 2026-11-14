"""Step 7: rank the calls (highest risk first) and evaluate against the true labels.

-> results/call_analysis/ranking.csv, ranking.md, evaluation.md
Ties are broken by number of distinct red flags, then call id, so the ranking is deterministic.
Usage: python src/call_analysis/rank.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402

from call_analysis import OUT  # noqa: E402
from call_analysis.report import fmt_time  # noqa: E402
from call_analysis.settings import load as load_settings  # noqa: E402

SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2}


def load_reports():
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((OUT / "reports").glob("*.json"))]


def top_flags(r, n=2):
    flags = sorted(r["red_flags"], key=lambda f: (SEVERITY_ORDER[f["severity"]], f["timestamp_s"]))
    return ", ".join(f"{f['id']} {f['name'].split(' (')[0]}" for f in flags[:n]) or "—"


def ranking_table(reports):
    rows = [{"call_id": r["call_id"], "risk_score": r["risk_score"], "level": r["risk_level"],
             "likely_type": r["likely_scam_type"], "top_2_flags": top_flags(r),
             "recommendation": r["recommendation"], "live_llm_verdict": r["live_verdict"],
             "true_label": r["true_label"],
             "_n_flags": len(r["red_flags"])} for r in reports]
    df = pd.DataFrame(rows).sort_values(["risk_score", "_n_flags", "call_id"], ascending=[False, False, True])
    df.insert(0, "rank", range(1, len(df) + 1))
    return df.drop(columns="_n_flags").reset_index(drop=True)


def first_high(r):
    for t in r["score_timeline"]:
        if t["level"] == "High":
            return f"chunk {t['chunk']} at {fmt_time(t['time_s'])}"
    return "only after end-of-call analysis" if r["risk_level"] == "High" else "never reached High"


def evaluation(df, reports):
    by_id = {r["call_id"]: r for r in reports}
    scams, genuine = df[df["true_label"] == "scam"], df[df["true_label"] == "genuine"]
    violations = [(g.call_id, g.rank, s.call_id, s.rank) for g in genuine.itertuples()
                  for s in scams.itertuples() if g.rank < s.rank]
    top3 = df.head(3)
    high_genuine = genuine[genuine["level"] == "High"]
    n_quotes = sum(1 for r in reports for f in r["red_flags"] + r["trust_signals"] if f["quote"])
    n_verified = n_quotes if all(r["quotes_verified"] for r in reports) else 0
    md = ["# Call analysis — evaluation", "",
          "> **This is a demo on 10 calls, not proof of accuracy.** Ten hand-picked calls cannot measure "
          "false-alarm rates; several are synthetic, and the two \"real genuine\" calls are short robocalls from "
          "an FTC illegal-robocall dataset that a keyword rule labelled genuine.", "",
          f"LLM: {reports[0]['llm_model']}. Weights: config/scoring.yaml. The risk score is not a probability.", "",
          "> **Rules v2 — not a blind result.** After the first run on these 10 calls, the user approved four rule "
          "changes (more one-time-code/PIN phrasings in F01, \"quickly\"/\"hurry\" in F20, no T06 when a high or "
          "critical flag fired, a customs-seizure script for F17). Because they were made after seeing these calls, "
          "this evaluation is no longer blind; the changes were checked on held-out calls instead "
          "(see `rule_validation.md`).", "",
          "Live process: every ~12-15 s (one chunk) the LLM predicts scam / not scam from the transcript so far; "
          "the summary is written after the call.", "",
          "## 1. Are all scams ranked above all genuine calls?", "",
          ("**Yes.**" if not violations else f"**No — {len(violations)} violation(s):**")]
    md += [f"- genuine `{g}` (rank {gr}) is above scam `{s}` (rank {sr})" for g, gr, s, sr in violations]
    md += ["", "## 2. Are the top 3 all scams?", "",
           ("**Yes.**" if (top3["true_label"] == "scam").all() else "**No:** " + ", ".join(
               f"`{c}` ({lab})" for c, lab in zip(top3["call_id"], top3["true_label"]) if lab != "scam")),
           "", "## 3. Is any genuine call rated High?", ""]
    if high_genuine.empty:
        md.append("**No.**")
    for g in high_genuine.itertuples():
        r = by_id[g.call_id]
        md.append(f"- `{g.call_id}` — risk score {g.risk_score}. Flags: "
                  + "; ".join(f"{f['id']} “{f['quote']}”" for f in r["red_flags"])
                  + f". LLM reasoning: {r['llm_reasoning']}")
    md += ["", "## 4. When did each scam first reach High?", "", "| Call | Final risk score | First High |",
           "|---|---|---|"]
    md += [f"| `{s.call_id}` | {s.risk_score} ({s.level}) | {first_high(by_id[s.call_id])} |"
           for s in scams.itertuples()]
    md += ["", "## 5. Quotes verified verbatim in the transcript", "",
           f"**{n_verified} / {n_quotes}** quotes verified (the run fails loudly if any quote is missing).", "",
           "## Ranking", "", df.to_markdown(index=False), ""]
    return "\n".join(md)


def main():
    reports = load_reports()
    df = ranking_table(reports)
    df.to_csv(OUT / "ranking.csv", index=False)
    (OUT / "ranking.md").write_text("# Call ranking (highest risk first)\n\n" + df.to_markdown(index=False) +
                                    "\n\n_Risk score = weighted rules + LLM judgement + classifier signal "
                                    "(config/scoring.yaml); not a probability._\n", encoding="utf-8")
    ev = evaluation(df, reports)
    (OUT / "evaluation.md").write_text(ev, encoding="utf-8")
    print(df.to_string(index=False))
    return df


if __name__ == "__main__":
    load_settings()
    main()
