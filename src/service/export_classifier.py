"""Train the service classifier (embeddings + LR on synthetic training calls) and save it as a small file,
so a server (e.g. the Azure VM) does not need the datasets.

Output: src/service/artifacts/classifier.joblib (~30 KB; committed to git).
Usage:  python src/service/export_classifier.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from call_analysis.scoring import CallClassifier  # noqa: E402
from service.pipeline import ARTIFACT  # noqa: E402

if __name__ == "__main__":
    clf = CallClassifier(exclude_ids=[])
    clf.save(ARTIFACT)
    check = CallClassifier(artifact=ARTIFACT)
    text = "please read me the code we sent you and buy gift cards right now"
    assert abs(check.fraud_score(text) - clf.fraud_score(text)) < 1e-9
    print(f"saved {ARTIFACT} ({ARTIFACT.stat().st_size / 1024:.0f} KB); classes={list(check.model.classes_)}")
