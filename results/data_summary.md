# Data summary (after cleaning)

## Per source

| source              |   rows |   legit (0) |   fraud (1) |   unlabelled |   mean words |   median words | synthetic   |   raw rows |   dropped short |   added by chunking |   dropped exact dup |   dropped near dup |
|:--------------------|-------:|------------:|------------:|-------------:|-------------:|---------------:|:------------|-----------:|----------------:|--------------------:|--------------------:|-------------------:|
| bothbosu            |   2055 |         837 |        1218 |            0 |          188 |          182   | True        |       1600 |               0 |                 459 |                   3 |                  1 |
| call_transcripts    |     68 |          24 |          44 |            0 |          202 |          196   | True        |         59 |               0 |                   9 |                   0 |                  0 |
| callcenter_en       |  15000 |       15000 |           0 |            0 |          252 |          259   | False       |       5999 |               3 |                9280 |                 253 |                 23 |
| harper_valley       |   1435 |        1435 |           0 |            0 |           88 |           83   | True        |       1446 |               0 |                   0 |                   3 |                  8 |
| kaggle_scam_nonscam |    791 |         400 |         391 |            0 |           45 |           35   | True        |        800 |               0 |                   0 |                   8 |                  1 |
| robocall            |    606 |           2 |         588 |           16 |           59 |           52   | False       |       1432 |              37 |                   6 |                 676 |                119 |
| synthetic_own       |   2304 |         575 |        1729 |            0 |           78 |           72   | True        |       2340 |               0 |                   0 |                  32 |                  4 |
| usenix_romance      |   1323 |           0 |        1323 |            0 |          250 |          249   | True        |        500 |               0 |                 823 |                   0 |                  0 |
| youtube_scam        |    244 |           0 |         244 |            0 |          157 |          158.5 | False       |        243 |               0 |                   2 |                   1 |                  0 |

## Source x fraud type

| source              |    F0 |   F1 |   F2 |   F3 |   F4 |   F6 |   F7 |   F8 |   F9 |   UNK |   All |
|:--------------------|------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|------:|------:|
| bothbosu            |   837 |    0 |    0 |  330 |  616 |    0 |    0 |    0 |  272 |     0 |  2055 |
| call_transcripts    |    24 |    4 |    0 |   11 |    6 |    0 |    0 |    2 |    6 |    15 |    68 |
| callcenter_en       | 15000 |    0 |    0 |    0 |    0 |    0 |    0 |    0 |    0 |     0 | 15000 |
| harper_valley       |  1435 |    0 |    0 |    0 |    0 |    0 |    0 |    0 |    0 |     0 |  1435 |
| kaggle_scam_nonscam |   400 |  119 |    0 |   67 |   47 |    0 |    0 |    0 |   34 |   124 |   791 |
| robocall            |     2 |   54 |    0 |  265 |  246 |    0 |    0 |    0 |   23 |    16 |   606 |
| synthetic_own       |   575 |  360 |  359 |    0 |    0 |  358 |  297 |  355 |    0 |     0 |  2304 |
| usenix_romance      |     0 |    0 |    0 |  588 |  735 |    0 |    0 |    0 |    0 |     0 |  1323 |
| youtube_scam        |     0 |   11 |    0 |   28 |  185 |    0 |    0 |    2 |    0 |    18 |   244 |
| All                 | 18273 |  548 |  359 | 1289 | 1835 |  358 |  297 |  359 |  335 |   173 | 23826 |

## Real (non-synthetic) rows per fraud type — the only rows allowed in val/test

| fraud_type   |   real rows |
|:-------------|------------:|
| F0           |       15002 |
| F1           |          65 |
| F3           |         293 |
| F4           |         431 |
| F8           |           2 |
| F9           |          23 |
| UNK          |          18 |

**WARNING:** mean length differs > 2x between sources (kaggle_scam_nonscam 45 vs callcenter_en 252 words) — length could become a source shortcut.
