# Call analysis — evaluation

> **This is a demo on 10 calls, not proof of accuracy.** Ten hand-picked calls cannot measure false-alarm rates; several are synthetic, and the two "real genuine" calls are short robocalls from an FTC illegal-robocall dataset that a keyword rule labelled genuine.

LLM: ollama:qwen2.5:7b. Weights: config/scoring.yaml. The risk score is not a probability.

> **Rules v2 — not a blind result.** After the first run on these 10 calls, the user approved four rule changes (more one-time-code/PIN phrasings in F01, "quickly"/"hurry" in F20, no T06 when a high or critical flag fired, a customs-seizure script for F17). Because they were made after seeing these calls, this evaluation is no longer blind; the changes were checked on held-out calls instead (see `rule_validation.md`).

Live process: every ~12-15 s (one chunk) the LLM predicts scam / not scam from the transcript so far; the summary is written after the call.

## 1. Are all scams ranked above all genuine calls?

**Yes.**

## 2. Are the top 3 all scams?

**Yes.**

## 3. Is any genuine call rated High?

**No.**

## 4. When did each scam first reach High?

| Call | Final risk score | First High |
|---|---|---|
| `bothbosu_00440` | 95 (High) | chunk 3 at 0:58 |
| `bothbosu_00139` | 90 (High) | chunk 5 at 1:15 |
| `synthetic_own_00149` | 79 (High) | chunk 1 at 0:29 |
| `robocall_01075` | 76 (High) | chunk 0 at 0:12 |
| `youtube_scam_00112` | 68 (Medium) | never reached High |
| `robocall_00058` | 59 (Medium) | never reached High |
| `youtube_scam_00113` | 14 (Safe) | never reached High |

## 5. Quotes verified verbatim in the transcript

**13 / 13** quotes verified (the run fails loudly if any quote is missing).

## Ranking

|   rank | call_id             |   risk_score | level   | likely_type                           | top_2_flags                                                                           | recommendation   | live_llm_verdict   | true_label   |
|-------:|:--------------------|-------------:|:--------|:--------------------------------------|:--------------------------------------------------------------------------------------|:-----------------|:-------------------|:-------------|
|      1 | bothbosu_00440      |           95 | High    | tech support / business impersonation | F03 Remote access app request, F17 Matches a known scam script                        | Reject           | scam               | scam         |
|      2 | bothbosu_00139      |           90 | High    | government impersonation              | F17 Matches a known scam script, F14 Asks for SSN / full card number / account number | Reject           | scam               | scam         |
|      3 | synthetic_own_00149 |           79 | High    | financial impersonation               | F01 Asks for one-time code / PIN / password, F20 Urgency                              | Reject           | scam               | scam         |
|      4 | robocall_01075      |           76 | High    | government impersonation              | F17 Matches a known scam script, F12 Threats                                          | Reject           | scam               | scam         |
|      5 | youtube_scam_00112  |           68 | Medium  | tech support / business impersonation | F03 Remote access app request                                                         | Warn, verify     | scam               | scam         |
|      6 | robocall_00058      |           59 | Medium  | government impersonation              | F17 Matches a known scam script, F12 Threats                                          | Warn, verify     | unclear            | scam         |
|      7 | youtube_scam_00113  |           14 | Safe    | tech support / business impersonation | F25 Too good to be true                                                               | Allow            | scam               | scam         |
|      8 | robocall_00089      |            0 | Safe    | not fraud                             | —                                                                                     | Allow            | not scam           | genuine      |
|      9 | robocall_00958      |            0 | Safe    | unknown                               | —                                                                                     | Allow            | unclear            | genuine      |
|     10 | synthetic_own_00151 |            0 | Safe    | not fraud                             | —                                                                                     | Allow            | not scam           | genuine      |
