# Data summary (after cleaning)

## Per source

| source         |   rows |   legit (0) |   fraud (1) |   unlabelled |   mean words |   median words | synthetic   |   raw rows |   dropped short |   added by chunking |   dropped exact dup |   dropped near dup |
|:---------------|-------:|------------:|------------:|-------------:|-------------:|---------------:|:------------|-----------:|----------------:|--------------------:|--------------------:|-------------------:|
| abcd           |  10252 |       10252 |           0 |            0 |          149 |            144 | False       |      10042 |               0 |                 210 |                   0 |                  0 |
| bothbosu       |   2061 |         839 |        1222 |            0 |          188 |            182 | True        |       1600 |               0 |                 465 |                   3 |                  1 |
| robocall       |    608 |           2 |         590 |           16 |           60 |             52 | False       |       1432 |              37 |                   6 |                 676 |                117 |
| synthetic_own  |   2305 |         575 |        1730 |            0 |           79 |             73 | True        |       2340 |               0 |                   0 |                  32 |                  3 |
| usenix_romance |   2369 |         292 |        2077 |            0 |          258 |            268 | True        |       1000 |               0 |                1369 |                   0 |                  0 |

## Source x fraud type

| source         |    F0 |   F1 |   F2 |   F3 |   F4 |   F5 |   F6 |   F7 |   F8 |   F9 |   UNK |   All |
|:---------------|------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|------:|------:|
| abcd           | 10252 |    0 |    0 |    0 |    0 |    0 |    0 |    0 |    0 |    0 |     0 | 10252 |
| bothbosu       |   839 |    0 |    0 |  330 |  619 |    0 |    0 |    0 |    0 |  273 |     0 |  2061 |
| robocall       |     2 |   54 |    0 |  267 |  247 |    0 |    0 |    0 |    0 |   22 |    16 |   608 |
| synthetic_own  |   575 |  360 |  360 |    0 |    0 |    0 |  358 |  297 |  355 |    0 |     0 |  2305 |
| usenix_romance |   292 |    0 |    0 |  592 |  735 |  750 |    0 |    0 |    0 |    0 |     0 |  2369 |
| All            | 11960 |  414 |  360 | 1189 | 1601 |  750 |  358 |  297 |  355 |  295 |    16 | 17595 |

## Real (non-synthetic) rows per fraud type — the only rows allowed in val/test

| fraud_type   |   real rows |
|:-------------|------------:|
| F0           |       10254 |
| F1           |          54 |
| F3           |         267 |
| F4           |         247 |
| F9           |          22 |

**WARNING:** mean length differs > 2x between sources (robocall 60 vs usenix_romance 258 words) — length could become a source shortcut.
