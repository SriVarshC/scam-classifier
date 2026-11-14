# Call ranking (highest risk first)

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

_Risk score = weighted rules + LLM judgement + classifier signal (config/scoring.yaml); not a probability._
