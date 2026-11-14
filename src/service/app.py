"""Scam-detection microservice (FastAPI, JSON only).

Contract with the team's transcription API (call_audio_starter, branch feature/authenticated-audio-api):
  POST /v1/classify   {"request_id": "...", "text": "<transcribed call>"}
  -> 200 {"request_id": "...", "classes": ["fraud", "risk_level:high", ...], "summary": "...", ...extra}
  The transcription API keeps only `classes` and `summary` (extra fields are ignored there).

Environment:
  SCAM_SERVICE_TOKEN          required Bearer token (generate: python -c "import secrets;print(secrets.token_urlsafe(32))")
                              -> give the same value to the transcription API as CLASSIFIER_API_TOKEN
  SCAM_SERVICE_ALLOW_NO_TOKEN=1   local development only: run without a token
  SCAM_LLM_TIMEOUT_SECONDS    LLM deadline (default 20; the transcription API waits 30 s in total)
  SCAM_MAX_TEXT_CHARS         max transcript length (default 20000)
  CALL_LLM_PROVIDER / CALL_LLM_MODEL / CALL_LLM_API_URL / CALL_LLM_API_KEY   LLM selection (see llm.py)

Run:  python -m uvicorn service.app:create_app --factory --app-dir src --host 127.0.0.1 --port 8100
Privacy: transcripts are processed in memory only - no logging of text, no disk cache.
"""
import hmac
import os
import sys
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import Depends, FastAPI, Header, HTTPException, Response  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

MAX_TEXT_CHARS = int(os.environ.get("SCAM_MAX_TEXT_CHARS", "20000"))


class ClassifyRequest(BaseModel):
    request_id: str = Field(default_factory=lambda: uuid.uuid4().hex, min_length=1, max_length=200)
    text: str = Field(min_length=1, max_length=MAX_TEXT_CHARS)


def create_app(service=None, token=None):
    token = token if token is not None else os.environ.get("SCAM_SERVICE_TOKEN", "")
    allow_no_token = os.environ.get("SCAM_SERVICE_ALLOW_NO_TOKEN") == "1"
    if not token and not allow_no_token:
        raise RuntimeError("Set SCAM_SERVICE_TOKEN (or SCAM_SERVICE_ALLOW_NO_TOKEN=1 for local development).")
    if token and len(token) < 16:
        raise RuntimeError("SCAM_SERVICE_TOKEN is too short (use at least 16 random characters).")

    state = {"service": service}

    def get_service():
        if state["service"] is None:
            from service.pipeline import ScamService
            state["service"] = ScamService()
        return state["service"]

    @asynccontextmanager
    async def lifespan(_app):
        get_service()  # load classifier, script library and LLM before accepting traffic
        yield

    app = FastAPI(title="Scam call classifier", version="1.0", docs_url=None, redoc_url=None, lifespan=lifespan)

    def check_auth(authorization: str = Header(default="")):
        if not token:
            return
        scheme, _, given = authorization.partition(" ")
        if scheme.lower() != "bearer" or not hmac.compare_digest(given.encode(), token.encode()):
            raise HTTPException(status_code=401, detail="Missing or invalid Bearer token")

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.get("/v1/status", dependencies=[Depends(check_auth)])
    def status():
        svc = get_service()
        return {"llm_model": svc.llm_name, "llm_available": svc.llm is not None,
                "llm_error": svc.llm_error, "max_text_chars": MAX_TEXT_CHARS}

    @app.post("/v1/classify", dependencies=[Depends(check_auth)])
    def classify(req: ClassifyRequest, response: Response, x_request_id: str = Header(default="")):
        text = req.text.strip()
        if not text:
            raise HTTPException(status_code=422, detail="Empty transcript")
        request_id = req.request_id or x_request_id or uuid.uuid4().hex
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Request-ID"] = request_id
        try:
            return get_service().analyze(text, request_id)
        except AssertionError:  # an evidence quote failed verification - never return unverified evidence
            raise HTTPException(status_code=500, detail="Internal evidence check failed")

    return app
