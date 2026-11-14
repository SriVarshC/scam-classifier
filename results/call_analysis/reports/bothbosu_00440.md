# Call report: bothbosu_00440

**Risk score: 95 / 100 · High** — recommendation: **Reject** (confidence: high)

| | |
|---|---|
| Source | bothbosu |
| Duration (simulated) | 1:18 |
| Claimed identity | Microsoft Technical Support |
| Caller wanted | Remote access to the computer and a one-time fee of $200 |
| Payment method | unknown |
| Likely scam type | tech support / business impersonation |
| LLM | ollama:qwen2.5:7b |

**Live LLM verdict at the end of the call: scam**

## Summary (written after the call)

The caller claimed to be from Microsoft Technical Support and said the person's computer was infected with a virus. The caller asked for remote access to the computer to remove the virus and requested a one-time fee of $200, which the call ended without the person agreeing to.

## Red flags

| Flag | Severity | Time | Quote |
|---|---|---|---|
| F17 Matches a known scam script | high | 0:00 | “Hello, this is John from Microsoft Technical Support. We've received a report that your computer is infected with a virus.” |
| F03 Remote access app request | critical | 0:56 | “you to give me access to your computer remotely.” |

## Trust signals

None.

## Live: risk score and LLM prediction every ~12-15 s

| Chunk | Time | Risk score | Level | New flags | Live LLM verdict | Reason |
|---|---|---|---|---|---|---|
| 0 | 0:15 | 34 | Low | F17 | unclear | Not enough information to determine if it is a scam. |
| 1 | 0:28 | 44 | Medium | — | scam | Caller claims to be from Microsoft Technical Support and mentions suspicious activity without providing evidence. |
| 2 | 0:43 | 44 | Medium | — | scam | Caller claims to be from Microsoft Technical Support and suggests the presence of a virus without providing evidence. |
| 3 | 0:58 | 95 | High | F03 | scam | Caller is asking for remote access to the user's computer. |
| 4 | 1:12 | 95 | High | F03 | scam | Caller is asking for remote access to the user's computer. |
| 5 | 1:18 | 95 | High | — | scam | Caller is asking for remote access to the user's computer and is trying to charge a fee. |

Final risk score (after end-of-call analysis): 95 — components: {'flags': 65, 'llm': 20, 'trust': 0, 'classifier': 9.8, 'raw': 94.8}

LLM reasoning: The caller claimed to be from Microsoft and asked for remote access, which are common tactics in tech support scams. The request for payment also indicates a potential scam.

_The risk score is a weighted sum of rule flags, an LLM judgement and a classifier signal (config/scoring.yaml). It is not a probability._
