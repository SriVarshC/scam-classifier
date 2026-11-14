# Call report: synthetic_own_00149

**Risk score: 79 / 100 · High** — recommendation: **Reject** (confidence: high)

| | |
|---|---|
| Source | synthetic_own |
| Duration (simulated) | 0:29 |
| Claimed identity | Pinecrest Bank |
| Caller wanted | To verify a suspicious charge and reissue a card |
| Payment method | unknown |
| Likely scam type | financial impersonation |
| LLM | ollama:qwen2.5:7b |

**Live LLM verdict at the end of the call: scam**

## Summary (written after the call)

A caller claiming to be from Pinecrest Bank called to verify a suspicious charge of $1,150. The caller asked for a six-digit code for online banking and a PIN to reissue a card. The call ended without the person giving any payment information.

## Red flags

| Flag | Severity | Time | Quote |
|---|---|---|---|
| F01 Asks for one-time code / PIN / password | critical | 0:11 | “We just sent a six-digit code to confirm your identity.” |
| F20 Urgency | medium | 0:20 | “Yes, that's normal. Quickly please, the charge is” |

## Trust signals

None.

## Live: risk score and LLM prediction every ~12-15 s

| Chunk | Time | Risk score | Level | New flags | Live LLM verdict | Reason |
|---|---|---|---|---|---|---|
| 0 | 0:14 | 59 | Medium | F01 | scam | The caller is asking for a six-digit code to confirm identity, which is a common fraud tactic. |
| 1 | 0:29 | 79 | High | F01, F20 | scam | Caller asked for PIN to reissue the card, which is a clear fraud sign. |

Final risk score (after end-of-call analysis): 79 — components: {'flags': 50, 'llm': 20, 'trust': 0, 'classifier': 9.0, 'raw': 79.0}

LLM reasoning: The caller claimed to be from a bank and asked for sensitive information, which are common tactics in financial impersonation scams.

_The risk score is a weighted sum of rule flags, an LLM judgement and a classifier signal (config/scoring.yaml). It is not a probability._
