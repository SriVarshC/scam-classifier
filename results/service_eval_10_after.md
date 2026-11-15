# Live service on real calls (Test R, never seen by any model)

10 calls sent, 0 errors. Median time 4.7s; LLM backend: {'gpu': 10}

## Genuine calls (CallCenterEN): n=5

| service label | % |
|---|---|
| not_fraud | 80.0 |
| uncertain | 20.0 |

Risk level: Safe 80.0%, Low 20.0%
LLM verdict: not scam 80.0%, scam 20.0%

Genuine calls not labelled not_fraud, by domain:

| scam_type   | flagged   |
|-------------|-----------|

Red flags on those calls: {'F20': 1, 'F21': 1}

## Real scam calls (robocall + youtube_scam): n=5

| service label | % |
|---|---|
| uncertain | 40.0 |
| fraud | 40.0 |
| not_fraud | 20.0 |

Risk level: Safe 60.0%, High 20.0%, Medium 20.0%
LLM verdict: scam 80.0%, not scam 20.0%
