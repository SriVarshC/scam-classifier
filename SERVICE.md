# Scam classifier service (JSON API)

Receives a call transcript, returns whether it looks like a scam plus a plain-language summary.
Built to be called by the team's transcription API (`call_audio_starter`, branch
`feature/authenticated-audio-api`) as its `CLASSIFIER_URL`.

## Endpoints

| Method / path | Auth | Purpose |
|---|---|---|
| GET `/healthz` | none | `{"status": "ok"}` once the models are loaded |
| GET `/v1/status` | Bearer | LLM model in use, whether it is available |
| POST `/v1/classify` | Bearer | classify + summarise one transcript |

### Request

```json
{"request_id": "abc-123", "text": "hi this is mark from the fraud department at your bank ..."}
```

`text` up to 20,000 characters (`SCAM_MAX_TEXT_CHARS`). Header: `Authorization: Bearer <SCAM_SERVICE_TOKEN>`.

### Response (200)

```json
{
  "request_id": "abc-123",
  "classes": ["fraud", "risk_level:high", "risk_score:100", "recommendation:reject",
              "type:financial_impersonation", "llm_verdict:scam",
              "flag:F17", "flag:F02", "flag:F20", "flag:F01", "flag:F13"],
  "summary": "The caller claimed to be from the fraud department at the bank and said they detected a suspicious transfer. They asked the person to read back a verification code and not to tell anyone at the branch about the call.",
  "label": "fraud", "risk_score": 100, "risk_level": "High", "recommendation": "Reject",
  "llm_verdict": "scam", "likely_scam_type": "financial impersonation",
  "red_flags": [{"id": "F01", "name": "Asks for one-time code / PIN / password", "severity": "critical",
                 "quote": "right now i just sent you a verification code please read it back", "timestamp_s": 20.4}],
  "trust_signals": [], "timeline": [{"window": 0, "end_s": 15.2, "risk_score": 75, "level": "High"}],
  "notes": ["Speaker roles are unknown for API text, so flags are checked on every line."]
}
```
(Real output from a local test, shortened.) The transcription API keeps only `classes` and `summary`;
the other fields are for anyone calling this service directly.

**`classes[0]` is the decision:** `fraud`, `uncertain` or `not_fraud`.
- risk level High → `fraud`; Medium → `fraud` if the LLM also says scam, else `uncertain`;
  Low / Safe → `uncertain` if the LLM says scam, else `not_fraud`.
- The other classes are `key:value` details: `risk_level`, `risk_score` (0–100, **not a probability**),
  `recommendation`, `type`, `llm_verdict`, and one `flag:<id>` per red flag.

### Errors
401 missing/wrong token · 422 empty or too-long text · 500 internal evidence check failed.
If the LLM is down or too slow, the service still answers (rules + classifier only), says so in `notes`,
and the summary starts with "Automatic summary unavailable".

## How it decides (fast mode)
1. Splits the text into ~30-word windows (~12–15 s of speech) and runs the red-flag rules on each window
   (every flag carries an exact quote from the text).
2. One LLM call (local Ollama `qwen2.5:7b` by default) gives the verdict, a risk judgement and the summary.
3. Risk score = red flags + LLM judgement + trust signals + a small classifier adjustment
   (`config/scoring.yaml`).

Measured locally (laptop, RTX 3050 Ti 4 GB, model warm): **~14 s per request**. The transcription API
waits 30 s by default (`CLASSIFIER_TIMEOUT_SECONDS`).

## Run locally

```bash
pip install -r requirements.txt
# 1. LLM: start Ollama with the project's model folder (qwen2.5:7b pulled there)
#    PowerShell: $env:OLLAMA_MODELS="d:\HackUmass\scam-classifier\models\ollama"; ollama serve
# 2. token: python -c "import secrets; print(secrets.token_urlsafe(32))"
# 3. service (PowerShell): $env:SCAM_SERVICE_TOKEN="<token>"
python -m uvicorn service.app:create_app --factory --app-dir src --host 127.0.0.1 --port 8100
```

Startup takes ~25 s (classifier + LLM warm-up). Test:

```bash
curl -s -X POST http://127.0.0.1:8100/v1/classify -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" -d '{"request_id":"t1","text":"please read me the code we sent you"}'
```

Tests (fake LLM, no Ollama needed): `python -m pytest tests -q`

## Connecting the transcription API
In the transcription server's environment:
- `CLASSIFIER_URL=https://<public HTTPS address of this service>/v1/classify` — it must be **HTTPS**
  (their server rejects plain http), so a local run needs a tunnel or this service needs hosting.
- `CLASSIFIER_API_TOKEN=<same value as SCAM_SERVICE_TOKEN>` (must differ from their own `SERVICE_API_TOKEN`).

## Privacy and limits
- Transcripts are processed in memory only: no transcript logging, no LLM answer cache, no embedding cache
  on disk in service mode.
- Speaker roles are unknown in API text, so the person's own words can trigger a flag.
- The risk score is not a probability and does not prove fraud. Accuracy was only shown on a 10-call demo
  (see README "Call analysis").
