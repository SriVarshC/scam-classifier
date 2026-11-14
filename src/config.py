"""Shared paths and constants."""
from pathlib import Path

SEED = 42

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"

# Team-generated synthetic calls (committed to the repo root so all teammates share it)
SYNTHETIC_OWN_CSV = ROOT / "synthetic_fraud_calls.csv"

FRAUD_TYPES = {
    "F0": "Not fraud",
    "F1": "Financial impersonation",
    "F2": "Account takeover",
    "F3": "Government impersonation",
    "F4": "Tech support / business impersonation",
    "F5": "Romance / catfishing",
    "F6": "Pig-butchering / investment",
    "F7": "Honeytrap / sextortion",
    "F8": "Family emergency / voice clone",
    "F9": "Prize / job / advance-fee",
}
UNKNOWN = "UNK"  # fraud type not yet assigned (excluded from training/eval)

MIN_WORDS = 10
CHUNK_WORDS = 300       # long conversations are cut into pieces of at most this many words
MAX_CHUNKS = 3          # keep at most this many pieces per conversation (start, middle, end)
NEAR_DUP_THRESHOLD = 0.95
