# Split summary (Option 1 tests A / B_*: train on synthetic only; Test R: real val/test)

## Test A — synthetic, in-distribution

| split   |   rows |   real % |   scam % |   genuine |   F0 |   F1 |   F2 |   F3 |   F4 |   F6 |   F7 |   F8 |   F9 | sources                                                                                       |
|:--------|-------:|---------:|---------:|----------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|:----------------------------------------------------------------------------------------------|
| train   |   5597 |        0 |     58.3 |      2336 | 2336 |  345 |  256 |  711 | 1004 |  256 |  212 |  255 |  222 | bothbosu, call_transcripts, harper_valley, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| val     |   1120 |        0 |     58.2 |       468 |  468 |   69 |   51 |  142 |  200 |   51 |   43 |   51 |   45 | bothbosu, call_transcripts, harper_valley, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| test    |   1120 |        0 |     58.3 |       467 |  467 |   69 |   52 |  143 |  200 |   51 |   42 |   51 |   45 | bothbosu, call_transcripts, harper_valley, kaggle_scam_nonscam, synthetic_own, usenix_romance |

## Test B_real — trained on synthetic, tested on all real calls

| split   |   rows |   real % |   scam % |   genuine |    F0 |   F1 |   F2 |   F3 |   F4 |   F6 |   F7 |   F8 |   F9 | sources                                                                                       |
|:--------|-------:|---------:|---------:|----------:|------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|:----------------------------------------------------------------------------------------------|
| train   |   6717 |        0 |     58.3 |      2804 |  2804 |  414 |  307 |  853 | 1204 |  307 |  255 |  306 |  267 | bothbosu, call_transcripts, harper_valley, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| val     |   1120 |        0 |     58.3 |       467 |   467 |   69 |   52 |  143 |  200 |   51 |   42 |   51 |   45 | bothbosu, call_transcripts, harper_valley, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| test    |  15816 |      100 |      5.1 |     15002 | 15002 |   65 |    0 |  293 |  431 |    0 |    0 |    2 |   23 | callcenter_en, robocall, youtube_scam                                                         |

## Test B_bothbosu — bothbosu never seen in training

| split   |   rows |   real % |   scam % |   genuine |   F0 |   F1 |   F2 |   F3 |   F4 |   F6 |   F7 |   F8 |   F9 | sources                                                                             |
|:--------|-------:|---------:|---------:|----------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|:------------------------------------------------------------------------------------|
| train   |   4956 |        0 |     57.9 |      2087 | 2087 |  414 |  308 |  570 |  676 |  307 |  254 |  306 |   34 | call_transcripts, harper_valley, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| val     |    826 |        0 |     58   |       347 |  347 |   69 |   51 |   96 |  112 |   51 |   43 |   51 |    6 | call_transcripts, harper_valley, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| test    |   2055 |        0 |     59.3 |       837 |  837 |    0 |    0 |  330 |  616 |    0 |    0 |    0 |  272 | bothbosu                                                                            |

## Test B_call_transcripts — call_transcripts never seen in training

| split   |   rows |   real % |   scam % |   genuine |   F0 |   F1 |   F2 |   F3 |   F4 |   F6 |   F7 |   F8 |   F9 | sources                                                                     |
|:--------|-------:|---------:|---------:|----------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|:----------------------------------------------------------------------------|
| train   |   6671 |        0 |     58.3 |      2783 | 2783 |  410 |  308 |  844 | 1198 |  307 |  255 |  304 |  262 | bothbosu, harper_valley, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| val     |   1113 |        0 |     58.3 |       464 |  464 |   69 |   51 |  141 |  200 |   51 |   42 |   51 |   44 | bothbosu, harper_valley, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| test    |     53 |        0 |     54.7 |        24 |   24 |    4 |    0 |   11 |    6 |    0 |    0 |    2 |    6 | call_transcripts                                                            |

## Test B_kaggle_scam_nonscam — kaggle_scam_nonscam never seen in training

| split   |   rows |   real % |   scam % |   genuine |   F0 |   F1 |   F2 |   F3 |   F4 |   F6 |   F7 |   F8 |   F9 | sources                                                                  |
|:--------|-------:|---------:|---------:|----------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|:-------------------------------------------------------------------------|
| train   |   6145 |        0 |     60   |      2460 | 2460 |  312 |  308 |  796 | 1163 |  307 |  254 |  306 |  239 | bothbosu, call_transcripts, harper_valley, synthetic_own, usenix_romance |
| val     |   1025 |        0 |     59.9 |       411 |  411 |   52 |   51 |  133 |  194 |   51 |   43 |   51 |   39 | bothbosu, call_transcripts, harper_valley, synthetic_own, usenix_romance |
| test    |    667 |        0 |     40   |       400 |  400 |  119 |    0 |   67 |   47 |    0 |    0 |    0 |   34 | kaggle_scam_nonscam                                                      |

## Test B_synthetic_own — synthetic_own never seen in training

| split   |   rows |   real % |   scam % |   genuine |   F0 |   F1 |   F2 |   F3 |   F4 |   F6 |   F7 |   F8 |   F9 | sources                                                                        |
|:--------|-------:|---------:|---------:|----------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|:-------------------------------------------------------------------------------|
| train   |   4742 |        0 |     51.3 |      2311 | 2311 |  105 |    0 |  853 | 1204 |    0 |    0 |    1 |  268 | bothbosu, call_transcripts, harper_valley, kaggle_scam_nonscam, usenix_romance |
| val     |    791 |        0 |     51.3 |       385 |  385 |   18 |    0 |  143 |  200 |    0 |    0 |    1 |   44 | bothbosu, call_transcripts, harper_valley, kaggle_scam_nonscam, usenix_romance |
| test    |   2304 |        0 |     75   |       575 |  575 |  360 |  359 |    0 |    0 |  358 |  297 |  355 |    0 | synthetic_own                                                                  |

## Test R — real val/test; train = real train fold + synthetic (30% of train)

| split   |   rows |   real % |   scam % |   genuine |    F0 |   F1 |   F2 |   F3 |   F4 |   F6 |   F7 |   F8 |   F9 | sources                                                                                                                              |
|:--------|-------:|---------:|---------:|----------:|------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|:-------------------------------------------------------------------------------------------------------------------------------------|
| train   |  16134 |       70 |     21.1 |     12736 | 12736 |  345 |  222 |  818 | 1176 |  221 |  183 |  222 |  211 | bothbosu, call_transcripts, callcenter_en, harper_valley, kaggle_scam_nonscam, robocall, synthetic_own, usenix_romance, youtube_scam |
| val     |   2260 |      100 |      5.2 |      2143 |  2143 |    8 |    0 |   46 |   61 |    0 |    0 |    0 |    2 | callcenter_en, robocall, youtube_scam                                                                                                |
| test    |   2261 |      100 |      5.2 |      2143 |  2143 |   10 |    0 |   44 |   61 |    0 |    0 |    0 |    3 | callcenter_en, robocall, youtube_scam                                                                                                |

Test C: evaluate.py truncates every test set above to its first 50 words.
