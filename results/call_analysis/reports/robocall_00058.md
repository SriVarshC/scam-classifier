# Call report: robocall_00058

**Risk score: 59 / 100 · Medium** — recommendation: **Warn, verify** (confidence: medium)

| | |
|---|---|
| Source | robocall |
| Duration (simulated) | 0:16 |
| Claimed identity | legal department |
| Caller wanted | press 1 to connect with the next available officer |
| Payment method | unknown |
| Likely scam type | government impersonation |
| LLM | ollama:qwen2.5:7b |

**Live LLM verdict at the end of the call: unclear**

## Summary (written after the call)

The caller claimed to be from a legal department and informed the person that their social security number was involved in fraudulent activities. They asked the person to press 1 to connect with an officer.

## Red flags

| Flag | Severity | Time | Quote |
|---|---|---|---|
| F12 Threats (arrest, lawsuit, frozen/suspended account, deportation) | high | 0:04 | “that there is a legal enforcement action filed on your” |
| F17 Matches a known scam script | high | 0:00 | “from our department is to inform you that there is a legal enforcement action filed on your social security number for fraudulent activities.” |

## Trust signals

None.

## Live: risk score and LLM prediction every ~12-15 s

| Chunk | Time | Risk score | Level | New flags | Live LLM verdict | Reason |
|---|---|---|---|---|---|---|
| 0 | 0:09 | 60 | Medium | F12, F17 | unclear | The call mentions a legal enforcement action but does not yet show clear fraud signs. |
| 1 | 0:16 | 59 | Medium | — | unclear | Not enough information to determine if it is a scam. |

Final risk score (after end-of-call analysis): 59 — components: {'flags': 50, 'llm': 0, 'trust': 0, 'classifier': 9.3, 'raw': 59.3}

LLM reasoning: The call involves a legal department and mentions fraudulent activities, which are common tactics in government impersonation scams.

_The risk score is a weighted sum of rule flags, an LLM judgement and a classifier signal (config/scoring.yaml). It is not a probability._
