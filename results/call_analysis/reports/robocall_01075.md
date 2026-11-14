# Call report: robocall_01075

**Risk score: 76 / 100 · High** — recommendation: **Reject** (confidence: medium)

| | |
|---|---|
| Source | robocall |
| Duration (simulated) | 0:20 |
| Claimed identity | customs and border protection |
| Caller wanted | to press one to talk to an investigation officer |
| Payment method | unknown |
| Likely scam type | government impersonation |
| LLM | ollama:qwen2.5:7b |

**Live LLM verdict at the end of the call: scam**

## Summary (written after the call)

The caller claimed to be from customs and border protection, stating that a package with contraband was seized under the person's name. They instructed the person to press one to speak with an investigation officer to avoid legal consequences.

## Red flags

| Flag | Severity | Time | Quote |
|---|---|---|---|
| F12 Threats (arrest, lawsuit, frozen/suspended account, deportation) | high | 0:05 | “a package has been seized under your name by” |
| F17 Matches a known scam script | high | 0:00 | “The reason of this call is to inform you about a package has been seized under your name by us customs and border protection with contraband of drugs and cash.” |

## Trust signals

None.

## Live: risk score and LLM prediction every ~12-15 s

| Chunk | Time | Risk score | Level | New flags | Live LLM verdict | Reason |
|---|---|---|---|---|---|---|
| 0 | 0:12 | 77 | High | F12, F17 | scam | The caller claims to have seized a package with contraband, which is a common scam tactic. |
| 1 | 0:20 | 76 | High | — | scam | Caller threatens legal consequences and asks to press a number to speak with an investigation officer. |

Final risk score (after end-of-call analysis): 76 — components: {'flags': 50, 'llm': 20, 'trust': 0, 'classifier': 6.4, 'raw': 76.4}

LLM reasoning: The call involves a government agency and an attempt to avoid legal consequences, which are common tactics in government impersonation scams.

_The risk score is a weighted sum of rule flags, an LLM judgement and a classifier signal (config/scoring.yaml). It is not a probability._
