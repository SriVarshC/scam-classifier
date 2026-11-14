"""Step 6: end-of-call report per call -> results/call_analysis/reports/<call_id>.json and .md

Built from results/call_analysis/analysis/<call_id>.json (written by scoring.py).
Recommendation follows the risk level (config/scoring.yaml): High -> Reject, Medium -> Warn, verify,
Low -> Take message, Safe -> Allow.

Confidence (in the recommendation) is based on the number and severity of INDEPENDENT red flags
(distinct flag ids):
  High / Medium level: high   if >= 1 critical flag plus >= 1 other flag, or >= 3 flags
                       medium if 2 flags, or 1 critical flag
                       low    otherwise (score driven mostly by the LLM / classifier)
  Low / Safe level:    high   if no red flags and T06 (no requests) holds and the LLM said "low"
                       medium if no red flags
                       low    if some red flags fired but the score stayed below Medium
Usage: python src/call_analysis/report.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from call_analysis import OUT  # noqa: E402
from call_analysis.settings import load as load_settings  # noqa: E402


def confidence(level, red_flags, trust, judgement):
    n = len(red_flags)
    n_crit = sum(f["severity"] == "critical" for f in red_flags)
    if level in ("High", "Medium"):
        if (n_crit >= 1 and n >= 2) or n >= 3:
            return "high"
        if n == 2 or n_crit == 1:
            return "medium"
        return "low"
    if n == 0 and any(t["id"] == "T06" for t in trust) and judgement == "low":
        return "high"
    return "medium" if n == 0 else "low"


def fmt_time(seconds):
    return f"{int(seconds // 60)}:{int(seconds % 60):02d}"


def build_report(a):
    e = a["extraction"]
    level = a["risk_level"]
    return {
        "call_id": a["id"], "source": a["source"], "duration_s": a["duration_s"],
        "duration": fmt_time(a["duration_s"]), "llm_model": a["llm_model"],
        "summary": a["summary"], "live_verdict": a["live_verdict"], "live_reason": a["live_reason"],
        "claimed_identity": e["claimed_identity"],
        "caller_request": e["caller_request"], "payment_method": e["payment_method"],
        "pressure_tactics": e["pressure_tactics"], "llm_reasoning": e["reasoning"],
        "red_flags": [{k: f[k] for k in ("id", "name", "severity", "quote", "timestamp_s", "chunk")}
                      for f in a["red_flags"]],
        "trust_signals": [{k: t[k] for k in ("id", "name", "quote", "timestamp_s")} for t in a["trust_signals"]],
        "risk_score": a["risk_score"], "risk_level": level,
        "score_components": a["score_components"],
        "likely_scam_type": e["likely_scam_type"],
        "recommendation": load_settings()["recommendations"][level],
        "confidence": confidence(level, a["red_flags"], a["trust_signals"], e["llm_risk_judgement"]),
        "score_timeline": [{"chunk": t["chunk"], "time_s": t["time_s"], "risk_score": t["score"],
                            "level": t["level"], "live_verdict": t["llm_verdict"], "live_reason": t["llm_reason"],
                            "new_flags": t["new_flags"]} for t in a["timeline"]],
        "true_label": a["true_label"], "grounding_fixes": e.get("grounding_fixes", []),
        "quotes_verified": a["quotes_verified"],
    }


def to_markdown(r):
    lines = [f"# Call report: {r['call_id']}", "",
             f"**Risk score: {r['risk_score']} / 100 · {r['risk_level']}** — recommendation: "
             f"**{r['recommendation']}** (confidence: {r['confidence']})", "",
             "| | |", "|---|---|",
             f"| Source | {r['source']} |", f"| Duration (simulated) | {r['duration']} |",
             f"| Claimed identity | {r['claimed_identity']} |", f"| Caller wanted | {r['caller_request']} |",
             f"| Payment method | {r['payment_method']} |", f"| Likely scam type | {r['likely_scam_type']} |",
             f"| LLM | {r['llm_model']} |", "",
             f"**Live LLM verdict at the end of the call: {r['live_verdict']}**", "",
             "## Summary (written after the call)", "", r["summary"], "",
             "## Red flags", ""]
    if r["red_flags"]:
        lines += ["| Flag | Severity | Time | Quote |", "|---|---|---|---|"]
        lines += [f"| {f['id']} {f['name']} | {f['severity']} | {fmt_time(f['timestamp_s'])} | “{f['quote']}” |"
                  for f in r["red_flags"]]
    else:
        lines.append("None.")
    lines += ["", "## Trust signals", ""]
    lines += ([f"- {t['id']} {t['name']}" + (f" — “{t['quote']}”" if t["quote"] else "")
               for t in r["trust_signals"]] or ["None."])
    lines += ["", "## Live: risk score and LLM prediction every ~12-15 s", "",
              "| Chunk | Time | Risk score | Level | New flags | Live LLM verdict | Reason |", "|---|---|---|---|---|---|---|"]
    lines += [f"| {t['chunk']} | {fmt_time(t['time_s'])} | {t['risk_score']} | {t['level']} | "
              f"{', '.join(t['new_flags']) or '—'} | {t['live_verdict']} | {t['live_reason']} |"
              for t in r["score_timeline"]]
    lines += ["", f"Final risk score (after end-of-call analysis): {r['risk_score']} — components: "
              f"{r['score_components']}", "",
              f"LLM reasoning: {r['llm_reasoning']}", ""]
    if r["grounding_fixes"]:
        lines += ["Grounding fixes (LLM fields reset to unknown): " + "; ".join(r["grounding_fixes"]), ""]
    lines += ["_The risk score is a weighted sum of rule flags, an LLM judgement and a classifier signal "
              "(config/scoring.yaml). It is not a probability._", ""]
    return "\n".join(lines)


def main():
    (OUT / "reports").mkdir(parents=True, exist_ok=True)
    reports = []
    for path in sorted((OUT / "analysis").glob("*.json")):
        r = build_report(json.loads(path.read_text(encoding="utf-8")))
        (OUT / "reports" / f"{r['call_id']}.json").write_text(json.dumps(r, indent=1), encoding="utf-8")
        (OUT / "reports" / f"{r['call_id']}.md").write_text(to_markdown(r), encoding="utf-8")
        reports.append(r)
    print(f"{len(reports)} reports -> {OUT / 'reports'}")
    return reports


if __name__ == "__main__":
    main()
