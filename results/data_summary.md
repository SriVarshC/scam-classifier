# Data summary (after cleaning)

## Per source

| source              |   rows |   legit (0) |   fraud (1) |   unlabelled |   mean words |   median words | synthetic   |   raw rows |   dropped short |   added by chunking |   dropped exact dup |   dropped near dup |
|:--------------------|-------:|------------:|------------:|-------------:|-------------:|---------------:|:------------|-----------:|----------------:|--------------------:|--------------------:|-------------------:|
| bothbosu            |   2061 |         839 |        1222 |            0 |          188 |            182 | True        |       1600 |               0 |                 465 |                   3 |                  1 |
| call_transcripts    |     69 |          25 |          44 |            0 |          200 |            193 | True        |         59 |               0 |                  10 |                   0 |                  0 |
| kaggle_scam_nonscam |    791 |         400 |         391 |            0 |           45 |             35 | True        |        800 |               0 |                   0 |                   8 |                  1 |
| robocall            |    608 |           2 |         590 |           16 |           60 |             52 | False       |       1432 |              37 |                   6 |                 676 |                117 |
| synthetic_own       |   2305 |         575 |        1730 |            0 |           79 |             73 | True        |       2340 |               0 |                   0 |                  32 |                  3 |
| usenix_romance      |   1327 |           0 |        1327 |            0 |          249 |            248 | True        |        500 |               0 |                 827 |                   0 |                  0 |
| youtube_scam        |    245 |           0 |         245 |            0 |          157 |            158 | False       |        243 |               0 |                   2 |                   0 |                  0 |

## Source x fraud type

| source              |   F0 |   F1 |   F2 |   F3 |   F4 |   F6 |   F7 |   F8 |   F9 |   UNK |   All |
|:--------------------|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|------:|------:|
| bothbosu            |  839 |    0 |    0 |  330 |  619 |    0 |    0 |    0 |  273 |     0 |  2061 |
| call_transcripts    |   25 |    4 |    0 |   11 |    6 |    0 |    0 |    2 |    6 |    15 |    69 |
| kaggle_scam_nonscam |  400 |  119 |    0 |   67 |   47 |    0 |    0 |    0 |   34 |   124 |   791 |
| robocall            |    2 |   54 |    0 |  267 |  247 |    0 |    0 |    0 |   22 |    16 |   608 |
| synthetic_own       |  575 |  360 |  360 |    0 |    0 |  358 |  297 |  355 |    0 |     0 |  2305 |
| usenix_romance      |    0 |    0 |    0 |  592 |  735 |    0 |    0 |    0 |    0 |     0 |  1327 |
| youtube_scam        |    0 |   11 |    0 |   28 |  186 |    0 |    0 |    2 |    0 |    18 |   245 |
| All                 | 1841 |  548 |  360 | 1295 | 1840 |  358 |  297 |  359 |  335 |   173 |  7406 |

## Real (non-synthetic) rows per fraud type — the only rows allowed in val/test

| fraud_type   |   real rows |
|:-------------|------------:|
| F0           |           2 |
| F1           |          65 |
| F3           |         295 |
| F4           |         433 |
| F8           |           2 |
| F9           |          22 |
| UNK          |          18 |

**WARNING:** mean length differs > 2x between sources (kaggle_scam_nonscam 45 vs usenix_romance 249 words) — length could become a source shortcut.
