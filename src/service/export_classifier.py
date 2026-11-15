"""Train the service classifier (embeddings + LR) and save it as a small file, so a server
(e.g. the Azure VM) does not need the datasets.

Default training split "R" (2026-11-15): real calls - incl. 10.7k real genuine CallCenterEN pieces - plus
synthetic calls capped at 30%. On held-out real calls (Test R) this model had FPR 2.3% / recall 98%.
"B_real" = the earlier synthetic-only model.

Output: src/service/artifacts/classifier.joblib (committed to git).
Usage:  python src/service/export_classifier.py [--split R|B_real]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from call_analysis.scoring import CallClassifier  # noqa: E402
from service.pipeline import ARTIFACT  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", default="R", choices=["R", "B_real"])
    args = ap.parse_args()
    clf = CallClassifier(exclude_ids=[], split=args.split)
    clf.save(ARTIFACT)
    check = CallClassifier(artifact=ARTIFACT)
    text = "please read me the code we sent you and buy gift cards right now"
    assert abs(check.fraud_score(text) - clf.fraud_score(text)) < 1e-9
    print(f"saved {ARTIFACT} ({ARTIFACT.stat().st_size / 1024:.0f} KB); split={args.split}; "
          f"classes={list(check.model.classes_)}")
