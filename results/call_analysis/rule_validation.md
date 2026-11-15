# Rule changes v1 -> v2, checked on HELD-OUT calls

The 10 demo calls are **excluded**. Up to 200 calls per group (random, seed 42). Rules only, no LLM.
Produced by `python src/call_analysis/validate_rules.py` (v1 = rules before the user-approved changes).

Changes in v2: F01 more one-time-code / PIN phrasings ("sent * code", "the PIN", "need * PIN"...),
F20 + "quickly"/"hurry", T06 not awarded when a high or critical flag fired, F17 + a customs-seizure script.


## Rules: v1 (before)

| group                                                    | kind                     |   calls | F01 one-time code/PIN   | any critical   | any high or critical   | F20 urgency   | F17 scam script   | T06 awarded   |
|:---------------------------------------------------------|:-------------------------|--------:|:------------------------|:---------------|:-----------------------|:--------------|:------------------|:--------------|
| synthetic bank OTP-theft scams (synthetic_own otp_theft) | scam (higher = better)   |     127 | 44%                     | 44%            | 44%                    | 0%            | 0%                | 31%           |
| synthetic bank scams, all F1 (synthetic_own)             | scam (higher = better)   |     200 | 15%                     | 39%            | 50%                    | 0%            | 13%               | 12%           |
| real robocall scams                                      | scam (higher = better)   |     200 | 0%                      | 0%             | 48%                    | 8%            | 38%               | 80%           |
| real YouTube scam calls                                  | scam (higher = better)   |     200 | 0%                      | 4%             | 22%                    | 33%           | 9%                | 66%           |
| synthetic genuine bank calls (synthetic_own F0)          | genuine (lower = better) |     200 | 17%                     | 17%            | 17%                    | 0%            | 0%                | 68%           |
| synthetic genuine calls (bothbosu F0)                    | genuine (lower = better) |     200 | 0%                      | 0%             | 29%                    | 6%            | 0%                | 80%           |
| synthetic genuine calls (kaggle non-scam)                | genuine (lower = better) |     200 | 0%                      | 0%             | 6%                     | 1%            | 0%                | 98%           |

## Rules: v2 (after)

| group                                                    | kind                     |   calls | F01 one-time code/PIN   | any critical   | any high or critical   | F20 urgency   | F17 scam script   | T06 awarded   |
|:---------------------------------------------------------|:-------------------------|--------:|:------------------------|:---------------|:-----------------------|:--------------|:------------------|:--------------|
| synthetic bank OTP-theft scams (synthetic_own otp_theft) | scam (higher = better)   |     127 | 78%                     | 78%            | 78%                    | 18%           | 0%                | 9%            |
| synthetic bank scams, all F1 (synthetic_own)             | scam (higher = better)   |     200 | 26%                     | 50%            | 60%                    | 6%            | 13%               | 4%            |
| real robocall scams                                      | scam (higher = better)   |     200 | 0%                      | 0%             | 49%                    | 8%            | 39%               | 37%           |
| real YouTube scam calls                                  | scam (higher = better)   |     200 | 1%                      | 4%             | 22%                    | 35%           | 9%                | 56%           |
| synthetic genuine bank calls (synthetic_own F0)          | genuine (lower = better) |     200 | 17%                     | 17%            | 17%                    | 0%            | 0%                | 68%           |
| synthetic genuine calls (bothbosu F0)                    | genuine (lower = better) |     200 | 0%                      | 0%             | 29%                    | 14%           | 0%                | 62%           |
| synthetic genuine calls (kaggle non-scam)                | genuine (lower = better) |     200 | 0%                      | 0%             | 6%                     | 3%            | 0%                | 93%           |


## What this shows
- **F01 on one-time-code theft scams: 44% -> 78%.** The added phrasings generalise beyond the demo call.
- **T06 ("no requests") on real robocall scams: 80% -> 37%.** Threatening robocalls are no longer rewarded
  for only saying "press one". On genuine BothBosu calls T06 also drops (80% -> 62%) because some of them
  trigger high flags (see below).
- **F17 (scam script) on real robocalls: 38% -> 39%** - the customs script adds little.
- **Cost:** F20 urgency on genuine BothBosu calls 6% -> 14% ("quickly"). No other genuine-call rate went up.

## Problem found (present in v1 AND v2, not fixed - needs a decision)
**17% of genuine synthetic bank calls trigger the critical flag F01.** Two causes:
1. Negations: *"we will never ask you for your PIN, password or a one-time code"* - a reassuring statement
   that the rule reads as a request.
2. Codes the bank *sends* without asking for them back: *"I'll send a verification code to the number we
   have"*, *"I'm sending a passcode to your current number"*. The scam pattern is asking you to READ the code back.
Also 29% of genuine BothBosu calls get a high/critical flag (mostly F12 threat words / F14 in insurance and
delivery calls). With the current weights a single critical flag (40) is not enough for High on its own.


## 2026-11-15: F01 v3 (digit-code wordings + not-secret codes), held-out calls incl. REAL genuine calls

Trigger: live two-speaker test missed "Read me the six digit code we texted you". Max 600 calls per group, seed 42.

### Rules: before (v2 + teammate F01 gate)

| group                                                            | kind                     |   calls | F01 one-time code/PIN   | any critical   | any high or critical   | F20 urgency   | F17 scam script   | T06 awarded   |
|:-----------------------------------------------------------------|:-------------------------|--------:|:------------------------|:---------------|:-----------------------|:--------------|:------------------|:--------------|
| synthetic bank OTP-theft scams (synthetic_own otp_theft)         | scam (higher = better)   |     127 | 78%                     | 78%            | 78%                    | 18%           | 0%                | 9%            |
| synthetic bank scams, all F1 (synthetic_own)                     | scam (higher = better)   |     359 | 28%                     | 50%            | 59%                    | 6%            | 0%                | 3%            |
| real robocall scams                                              | scam (higher = better)   |     600 | 0%                      | 0%             | 31%                    | 11%           | 0%                | 50%           |
| real YouTube scam calls                                          | scam (higher = better)   |     223 | 0%                      | 4%             | 15%                    | 33%           | 0%                | 58%           |
| synthetic genuine bank calls (synthetic_own F0)                  | genuine (lower = better) |     599 | 0%                      | 0%             | 0%                     | 0%            | 0%                | 82%           |
| synthetic genuine calls (bothbosu F0)                            | genuine (lower = better) |     600 | 0%                      | 0%             | 27%                    | 15%           | 0%                | 62%           |
| synthetic genuine calls (kaggle non-scam)                        | genuine (lower = better) |     400 | 0%                      | 0%             | 6%                     | 4%            | 0%                | 92%           |
| REAL genuine customer-service calls (callcenter_en)              | genuine (lower = better) |     600 | 2%                      | 4%             | 42%                    | 70%           | 0%                | 20%           |
| acted genuine bank calls: cards, PINs, passwords (harper_valley) | genuine (lower = better) |     600 | 0%                      | 0%             | 1%                     | 1%            | 0%                | 78%           |


### Rules: after (v3 F01 phrases + not-secret codes)

| group                                                            | kind                     |   calls | F01 one-time code/PIN   | any critical   | any high or critical   | F20 urgency   | F17 scam script   | T06 awarded   |
|:-----------------------------------------------------------------|:-------------------------|--------:|:------------------------|:---------------|:-----------------------|:--------------|:------------------|:--------------|
| synthetic bank OTP-theft scams (synthetic_own otp_theft)         | scam (higher = better)   |     127 | 79%                     | 79%            | 79%                    | 18%           | 0%                | 9%            |
| synthetic bank scams, all F1 (synthetic_own)                     | scam (higher = better)   |     359 | 28%                     | 50%            | 60%                    | 6%            | 0%                | 3%            |
| real robocall scams                                              | scam (higher = better)   |     600 | 0%                      | 0%             | 31%                    | 11%           | 0%                | 50%           |
| real YouTube scam calls                                          | scam (higher = better)   |     223 | 0%                      | 4%             | 16%                    | 33%           | 0%                | 58%           |
| synthetic genuine bank calls (synthetic_own F0)                  | genuine (lower = better) |     599 | 0%                      | 0%             | 0%                     | 0%            | 0%                | 82%           |
| synthetic genuine calls (bothbosu F0)                            | genuine (lower = better) |     600 | 0%                      | 0%             | 27%                    | 15%           | 0%                | 62%           |
| synthetic genuine calls (kaggle non-scam)                        | genuine (lower = better) |     400 | 0%                      | 0%             | 6%                     | 4%            | 0%                | 92%           |
| REAL genuine customer-service calls (callcenter_en)              | genuine (lower = better) |     600 | 2%                      | 4%             | 42%                    | 70%           | 0%                | 20%           |
| acted genuine bank calls: cards, PINs, passwords (harper_valley) | genuine (lower = better) |     600 | 0%                      | 0%             | 1%                     | 1%            | 0%                | 78%           |
