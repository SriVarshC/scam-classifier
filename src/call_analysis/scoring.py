"""Step 5: live risk score (0-100) recomputed after every chunk. It is a RISK SCORE, not a probability.

  risk score = sum of distinct red-flag weights (critical 40 / high 25 / medium 10)
             + LLM risk judgement (high +20 / medium +10 / low 0) from the LATEST LIVE prediction
               (the LLM predicts scam / not scam every ~12-15 s from the transcript so far)
             - 15 per distinct trust signal (T04 live; T06 only at the end of the call)
             + classifier adjustment = clip((classifier fraud score - 0.5) * 20, -10, +10)
  clamped to 0-100. Levels: High >= 70, Medium 40-69, Low 20-39, Safe < 20. All numbers: config/scoring.yaml.

The classifier is embeddings + logistic regression trained on SYNTHETIC calls only (the Test B_real
training split), with the 10 demo calls removed so none of them is seen in training.

Usage: python src/call_analysis/scoring.py --calls robocall_00058 synthetic_own_00151
       -> results/call_analysis/analysis/<call_id>.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from call_analysis import OUT  # noqa: E402
from call_analysis.flags import ScriptMatcher, rule_flags_in_chunk, t06_holds, verify_quotes  # noqa: E402
from call_analysis.settings import load as load_settings  # noqa: E402
from clean import clean_text  # noqa: E402
from config import PROCESSED  # noqa: E402

SPLITS = PROCESSED / "splits"


def level_for(score):
    for level, lower in sorted(load_settings()["levels"].items(), key=lambda kv: -kv[1]):
        if score >= lower:
            return level
    return "Safe"


def compute_score(flags, trust, judgement, clf_fraud_score):
    """flags/trust: distinct first occurrences. Returns (score, level, components)."""
    cfg = load_settings()
    flag_pts = sum(cfg["severity_weights"][f["severity"]] for f in flags)
    llm_pts = cfg["llm_judgement"].get(judgement, 0) if judgement else 0
    trust_pts = cfg["trust_signal_weight"] * len(trust)
    c = cfg["classifier"]
    clf_pts = 0.0 if clf_fraud_score is None else float(
        np.clip((clf_fraud_score - 0.5) * c["scale"], -c["max_abs"], c["max_abs"]))
    raw = flag_pts + llm_pts + trust_pts + clf_pts
    score = int(round(min(100, max(0, raw))))
    return score, level_for(score), {"flags": flag_pts, "llm": llm_pts, "trust": trust_pts,
                                     "classifier": round(clf_pts, 1), "raw": round(raw, 1)}


class CallClassifier:
    """Embeddings + LR on synthetic training calls (demo calls excluded); fraud score = 1 - P(F0).
    `artifact`: path to a saved, already-trained model (service/artifacts/classifier.joblib) so a server
    does not need the datasets. Without it, the model is trained from data/processed."""

    def __init__(self, exclude_ids=(), artifact=None):
        from models import EmbeddingLR
        if artifact is not None and Path(artifact).exists():
            import joblib
            self.model = EmbeddingLR()
            self.model.clf = joblib.load(artifact)
            self.model.classes_ = self.model.clf.classes_
        else:
            merged = pd.read_csv(PROCESSED / "merged.csv")
            train = pd.read_csv(SPLITS / "B_real_train.csv")[["id"]].merge(merged, on="id")
            base = train["id"].str.replace(r"_c\d+$", "", regex=True)
            train = train[~base.isin(set(exclude_ids))]
            self.model = EmbeddingLR().fit(list(train["text"]), train["fraud_type"].tolist())
        self.f0 = list(self.model.classes_).index("F0")

    def save(self, path):
        import joblib
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model.clf, path)

    def fraud_scores(self, raw_texts):
        """Fraud score for several texts in ONE embedding batch (PERF.md P1-3)."""
        raw_texts = list(raw_texts)
        if not raw_texts:
            return []
        proba = self.model.predict_proba([clean_text(t) for t in raw_texts])
        return (1 - proba[:, self.f0]).tolist()

    def fraud_score(self, raw_text):
        return self.fraud_scores([raw_text])[0]


def render(chunks):
    """Transcript so far as display lines (verbatim segment text)."""
    return "\n".join(f"{s['speaker'] + ': ' if s['speaker'] else ''}{s['text']}"
                     for ch in chunks for s in ch["segments"])


def analyze_call(call, llm, clf, matcher):
    """Live loop: after every chunk (~12-15 s) -> rule flags, LLM scam/not-scam prediction, classifier,
    risk score. After the call -> LLM summary + why it is / is not a scam + extraction."""
    every = load_settings()["llm"]["predict_every_chunks"]
    first = {}            # flag id -> first occurrence (scored once)
    occurrences = []      # every occurrence (for highlighting)
    prediction = {"verdict": "unclear", "risk_judgement": None, "reason": ""}
    timeline = []
    for i, chunk in enumerate(call["chunks"]):
        new = rule_flags_in_chunk(chunk)
        if "F17" not in first:
            hit = matcher.in_chunk(chunk)
            if hit:
                new.append(hit)
        occurrences += new
        for f in new:
            first.setdefault(f["id"], f)
        so_far = call["chunks"][:i + 1]
        if (i + 1) % every == 0 or i == len(call["chunks"]) - 1:
            p = llm.predict(render(so_far))
            if p["risk_judgement"]:
                prediction = p
        clf_score = clf.fraud_score(" ".join(seg["text"] for ch in so_far for seg in ch["segments"]))
        reds = [f for f in first.values() if f["severity"] != "trust"]
        trust = [f for f in first.values() if f["severity"] == "trust"]
        score, level, comp = compute_score(reds, trust, prediction["risk_judgement"], clf_score)
        timeline.append({"chunk": i, "time_s": chunk["end_s"], "score": score, "level": level,
                         "components": comp, "new_flags": [f["id"] for f in new],
                         "llm_verdict": prediction["verdict"], "llm_judgement": prediction["risk_judgement"],
                         "llm_reason": prediction["reason"], "classifier_fraud_score": round(clf_score, 3)})

    # ----- after the call: summary + extraction (analysis only; the score uses the live verdict) -----
    extraction = llm.extract(render(call["chunks"]))
    reds = [f for f in first.values() if f["severity"] != "trust"]
    trust = [f for f in first.values() if f["severity"] == "trust"]
    t06 = t06_holds(call, reds)
    if t06:
        trust.append(t06)
    score, level, comp = compute_score(reds, trust, prediction["risk_judgement"],
                                       timeline[-1]["classifier_fraud_score"])
    verify_quotes(call, occurrences + trust)
    return {"id": call["id"], "source": call["source"], "true_label": call["true_label"],
            "scam_type_true": call["scam_type"], "is_synthetic": call["is_synthetic"],
            "duration_s": call["duration_s"], "llm_model": f"{llm.provider}:{llm.model}",
            "live_verdict": prediction["verdict"], "live_reason": prediction["reason"],
            "summary": extraction["summary"], "extraction": extraction,
            "red_flags": reds, "trust_signals": trust, "flag_occurrences": occurrences,
            "risk_score": score, "risk_level": level, "score_components": comp,
            "timeline": timeline, "quotes_verified": True,
            "n_quotes": sum(1 for f in occurrences + trust if f["id"] != "T06")}


def load_call(call_id):
    return json.loads((OUT / "calls" / f"{call_id}.json").read_text(encoding="utf-8"))


def build_context():
    from call_analysis.llm import CallLLM
    selected = pd.read_csv(OUT / "selected_calls.csv")
    return CallLLM(), CallClassifier(selected["id"]), ScriptMatcher()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calls", nargs="+", help="call ids (default: all selected calls)")
    args = ap.parse_args()
    ids = args.calls or pd.read_csv(OUT / "selected_calls.csv")["id"].tolist()
    llm, clf, matcher = build_context()
    (OUT / "analysis").mkdir(parents=True, exist_ok=True)
    for cid in ids:
        res = analyze_call(load_call(cid), llm, clf, matcher)
        (OUT / "analysis" / f"{cid}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
        print(f"{cid}: risk score {res['risk_score']} ({res['risk_level']}), "
              f"{len(res['red_flags'])} red flags, {len(res['trust_signals'])} trust signals", flush=True)


if __name__ == "__main__":
    main()
