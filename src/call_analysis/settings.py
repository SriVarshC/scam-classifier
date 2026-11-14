"""Loads config/scoring.yaml (all tunable weights live there)."""
from functools import lru_cache

import yaml

from config import ROOT

SCORING_YAML = ROOT / "config" / "scoring.yaml"


@lru_cache(maxsize=1)
def load():
    return yaml.safe_load(SCORING_YAML.read_text(encoding="utf-8"))
