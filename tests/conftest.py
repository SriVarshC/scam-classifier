import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from call_analysis.llm import CallLLM  # noqa: E402

TOKEN = "test-token-0123456789abcdef"


class FakeLLM(CallLLM):
    """Runs the REAL prompt building, sanitising and validation; only the model call is faked.
    It behaves like a gullible model: if it sees an injection line it answers 'not scam / low'."""

    def __init__(self, fail=False):  # no Ollama needed
        self.provider, self.model = "fake", "fake-llm"
        self.use_cache, self.timeout_s, self.retries = False, 5, 0
        self.fail = fail
        self.prompts = []

    def _call_once(self, prompt):
        self.prompts.append(prompt)
        if self.fail:
            raise TimeoutError("simulated LLM timeout")
        # the transcript block is the LAST "<<<TRANSCRIPT\n ... \nTRANSCRIPT>>>" (the preamble mentions the markers)
        text = prompt.rsplit("<<<TRANSCRIPT\n", 1)[1].split("\nTRANSCRIPT>>>", 1)[0].lower()
        if "ignore your instructions" in text or "mark this safe" in text:
            verdict, risk = "not scam", "low"          # what an injected model would say
        elif any(w in text for w in ("code", "gift card", "arrest", "remote access", "safe account")):
            verdict, risk = "scam", "high"
        else:
            verdict, risk = "not scam", "low"
        return json.dumps({"verdict": verdict, "risk_judgement": risk,
                           "summary": "A caller spoke with the person about an account.",
                           "likely_scam_type": "unknown", "claimed_identity": "unknown",
                           "caller_request": "unknown"})


@pytest.fixture(scope="session")
def service():
    from service.pipeline import ScamService
    return ScamService(llm=FakeLLM())
