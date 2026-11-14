# Call report: youtube_scam_00113

**Risk score: 14 / 100 · Safe** — recommendation: **Allow** (confidence: low)

| | |
|---|---|
| Source | youtube_scam |
| Duration (simulated) | 1:05 |
| Claimed identity | unknown |
| Caller wanted | unknown |
| Payment method | unknown |
| Likely scam type | tech support / business impersonation |
| LLM | ollama:qwen2.5:7b |

**Live LLM verdict at the end of the call: scam**

## Summary (written after the call)

The caller claimed to be from a company and said the person would receive a refund of $399.99 because the service was no longer needed. The caller did not ask for any payment or action from the person.

## Red flags

| Flag | Severity | Time | Quote |
|---|---|---|---|
| F25 Too good to be true (prize, won, refund, guaranteed) | medium | 0:14 | “is giving you a refund of 399 which you” |

## Trust signals

- T06 No request for money, codes or personal data during the whole call

## Live: risk score and LLM prediction every ~12-15 s

| Chunk | Time | Risk score | Level | New flags | Live LLM verdict | Reason |
|---|---|---|---|---|---|---|
| 0 | 0:12 | 0 | Safe | — | not scam | The conversation so far appears to be a friendly, general exchange. |
| 1 | 0:24 | 14 | Safe | F25 | scam | The caller is offering a refund and suggesting subscription, which are unusual and may indicate a scam. |
| 2 | 0:32 | 21 | Low | — | scam | The caller is offering a refund for a service that was paid for in the past, which is a common tactic in refund scams. |
| 3 | 0:44 | 23 | Low | — | scam | The caller is offering a refund for a service not needed anymore, which is a common scam tactic. |
| 4 | 0:56 | 28 | Low | — | scam | The caller is offering a refund for a service that the callee is not aware of, which is a common tactic in refund scams. |
| 5 | 1:05 | 29 | Low | — | scam | The caller is offering a refund for a service that the recipient is not aware of and has not subscribed to, which is a common tactic in scam calls. |

Final risk score (after end-of-call analysis): 14 — components: {'flags': 10, 'llm': 10, 'trust': -15, 'classifier': 8.7, 'raw': 13.7}

LLM reasoning: The call involves a refund offer and claims of past services, which are common tactics in tech support scams.

_The risk score is a weighted sum of rule flags, an LLM judgement and a classifier signal (config/scoring.yaml). It is not a probability._
