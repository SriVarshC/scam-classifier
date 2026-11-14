# Call report: youtube_scam_00112

**Risk score: 68 / 100 · Medium** — recommendation: **Warn, verify** (confidence: medium)

| | |
|---|---|
| Source | youtube_scam |
| Duration (simulated) | 1:10 |
| Claimed identity | PayPal |
| Caller wanted | To download remote access software and provide a password |
| Payment method | unknown |
| Likely scam type | tech support / business impersonation |
| LLM | ollama:qwen2.5:7b |

**Live LLM verdict at the end of the call: scam**

## Summary (written after the call)

The caller claimed to be from PayPal and said there was an invoice for Christmas lights. They asked the person to download remote access software and provide a password. The call ended without the person giving any information.

## Red flags

| Flag | Severity | Time | Quote |
|---|---|---|---|
| F03 Remote access app request | critical | 0:51 | “the world's most trusted remote access oh it's remote access” |

## Trust signals

None.

## Live: risk score and LLM prediction every ~12-15 s

| Chunk | Time | Risk score | Level | New flags | Live LLM verdict | Reason |
|---|---|---|---|---|---|---|
| 0 | 0:12 | 2 | Safe | — | unclear | Not enough information to determine if it is a scam. |
| 1 | 0:24 | 5 | Safe | — | unclear | Not enough information to determine if it is a scam. |
| 2 | 0:36 | 5 | Safe | — | not scam | The caller is inquiring about a PayPal invoice for Christmas lights and does not request any personal or financial information. |
| 3 | 0:48 | 6 | Safe | — | unclear | Not enough information to determine if it is a scam. |
| 4 | 1:00 | 58 | Medium | F03 | scam | Caller asked to click on remote access support, which is a common scam tactic. |
| 5 | 1:10 | 68 | Medium | — | scam | Caller is asking for a password and mentioning remote access support, which are common signs of a scam. |

Final risk score (after end-of-call analysis): 68 — components: {'flags': 40, 'llm': 20, 'trust': 0, 'classifier': 8.1, 'raw': 68.1}

LLM reasoning: The caller asked for personal information and suggested downloading software, which are common tactics in tech support scams.

_The risk score is a weighted sum of rule flags, an LLM judgement and a classifier signal (config/scoring.yaml). It is not a probability._
