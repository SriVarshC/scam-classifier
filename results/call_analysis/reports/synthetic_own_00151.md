# Call report: synthetic_own_00151

**Risk score: 0 / 100 · Safe** — recommendation: **Allow** (confidence: high)

| | |
|---|---|
| Source | synthetic_own |
| Duration (simulated) | 0:24 |
| Claimed identity | Tyler from Harborview Credit Union's fraud team |
| Caller wanted | To confirm if the $750 charge was made by the person |
| Payment method | unknown |
| Likely scam type | not fraud |
| LLM | ollama:qwen2.5:7b |

**Live LLM verdict at the end of the call: not scam**

## Summary (written after the call)

A caller identified as Tyler from Harborview Credit Union's fraud team called to inform the person about a $750 charge at a big box store and asked if it was them. The caller blocked the card and said a new one would be mailed.

## Red flags

None.

## Trust signals

- T06 No request for money, codes or personal data during the whole call

## Live: risk score and LLM prediction every ~12-15 s

| Chunk | Time | Risk score | Level | New flags | Live LLM verdict | Reason |
|---|---|---|---|---|---|---|
| 0 | 0:15 | 0 | Safe | — | not scam | Caller is inquiring about a potential fraudulent charge. |
| 1 | 0:24 | 0 | Safe | — | not scam | The caller is from Harborview Credit Union and is confirming a charge, not asking for sensitive information. |

Final risk score (after end-of-call analysis): 0 — components: {'flags': 0, 'llm': 0, 'trust': -15, 'classifier': -2.4, 'raw': -17.4}

LLM reasoning: The call was about a potential fraudulent charge and the credit union's actions, not a scam.

_The risk score is a weighted sum of rule flags, an LLM judgement and a classifier signal (config/scoring.yaml). It is not a probability._
