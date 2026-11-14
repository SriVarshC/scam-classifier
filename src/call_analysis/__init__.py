"""Call analysis: simulated live transcript, red flags, running summary, risk score, reports, ranking.

All outputs go to results/call_analysis/. Phone calls only (see CLAUDE.md ground rule 0).
"""
import sys
from pathlib import Path

# Make src/ importable (config.py etc.) when modules are run as scripts.
SRC = Path(__file__).resolve().parents[1]
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from config import RESULTS  # noqa: E402

OUT = RESULTS / "call_analysis"
