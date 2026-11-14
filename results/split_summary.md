# Split summary (Option 1: train on synthetic only)

## Test A — synthetic, in-distribution

| split   |   rows |   real % |   scam % |   genuine |   F0 |   F1 |   F2 |   F3 |   F4 |   F6 |   F7 |   F8 |   F9 | sources                                                                        |
|:--------|-------:|---------:|---------:|----------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|:-------------------------------------------------------------------------------|
| train   |   4580 |        0 |     71.3 |      1313 | 1313 |  345 |  257 |  714 | 1005 |  256 |  212 |  255 |  223 | bothbosu, call_transcripts, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| val     |    917 |        0 |     71.3 |       263 |  263 |   69 |   52 |  143 |  201 |   51 |   42 |   51 |   45 | bothbosu, call_transcripts, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| test    |    917 |        0 |     71.3 |       263 |  263 |   69 |   51 |  143 |  201 |   51 |   43 |   51 |   45 | bothbosu, call_transcripts, kaggle_scam_nonscam, synthetic_own, usenix_romance |

## Test B_real — trained on synthetic, tested on all real calls

| split   |   rows |   real % |   scam % |   genuine |   F0 |   F1 |   F2 |   F3 |   F4 |   F6 |   F7 |   F8 |   F9 | sources                                                                        |
|:--------|-------:|---------:|---------:|----------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|:-------------------------------------------------------------------------------|
| train   |   5497 |        0 |     71.3 |      1576 | 1576 |  414 |  309 |  857 | 1206 |  307 |  254 |  306 |  268 | bothbosu, call_transcripts, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| val     |    917 |        0 |     71.3 |       263 |  263 |   69 |   51 |  143 |  201 |   51 |   43 |   51 |   45 | bothbosu, call_transcripts, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| test    |    819 |      100 |     99.8 |         2 |    2 |   65 |    0 |  295 |  433 |    0 |    0 |    2 |   22 | robocall, youtube_scam                                                         |

## Test B_bothbosu — bothbosu never seen in training

| split   |   rows |   real % |   scam % |   genuine |   F0 |   F1 |   F2 |   F3 |   F4 |   F6 |   F7 |   F8 |   F9 | sources                                                              |
|:--------|-------:|---------:|---------:|----------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|:---------------------------------------------------------------------|
| train   |   3731 |        0 |     77   |       857 |  857 |  414 |  308 |  575 |  675 |  307 |  255 |  306 |   34 | call_transcripts, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| val     |    622 |        0 |     77   |       143 |  143 |   69 |   52 |   95 |  113 |   51 |   42 |   51 |    6 | call_transcripts, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| test    |   2061 |        0 |     59.3 |       839 |  839 |    0 |    0 |  330 |  619 |    0 |    0 |    0 |  273 | bothbosu                                                             |

## Test B_call_transcripts — call_transcripts never seen in training

| split   |   rows |   real % |   scam % |   genuine |   F0 |   F1 |   F2 |   F3 |   F4 |   F6 |   F7 |   F8 |   F9 | sources                                                      |
|:--------|-------:|---------:|---------:|----------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|:-------------------------------------------------------------|
| train   |   5451 |        0 |     71.5 |      1555 | 1555 |  411 |  308 |  847 | 1200 |  307 |  255 |  305 |  263 | bothbosu, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| val     |    909 |        0 |     71.5 |       259 |  259 |   68 |   52 |  142 |  201 |   51 |   42 |   50 |   44 | bothbosu, kaggle_scam_nonscam, synthetic_own, usenix_romance |
| test    |     54 |        0 |     53.7 |        25 |   25 |    4 |    0 |   11 |    6 |    0 |    0 |    2 |    6 | call_transcripts                                             |

## Test B_kaggle_scam_nonscam — kaggle_scam_nonscam never seen in training

| split   |   rows |   real % |   scam % |   genuine |   F0 |   F1 |   F2 |   F3 |   F4 |   F6 |   F7 |   F8 |   F9 | sources                                                   |
|:--------|-------:|---------:|---------:|----------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|:----------------------------------------------------------|
| train   |   4925 |        0 |     74.9 |      1234 | 1234 |  312 |  308 |  800 | 1165 |  307 |  254 |  306 |  239 | bothbosu, call_transcripts, synthetic_own, usenix_romance |
| val     |    822 |        0 |     75.1 |       205 |  205 |   52 |   52 |  133 |  195 |   51 |   43 |   51 |   40 | bothbosu, call_transcripts, synthetic_own, usenix_romance |
| test    |    667 |        0 |     40   |       400 |  400 |  119 |    0 |   67 |   47 |    0 |    0 |    0 |   34 | kaggle_scam_nonscam                                       |

## Test B_synthetic_own — synthetic_own never seen in training

| split   |   rows |   real % |   scam % |   genuine |   F0 |   F1 |   F2 |   F3 |   F4 |   F6 |   F7 |   F8 |   F9 | sources                                                         |
|:--------|-------:|---------:|---------:|----------:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|-----:|:----------------------------------------------------------------|
| train   |   3522 |        0 |     69.2 |      1084 | 1084 |  105 |    0 |  857 | 1206 |    0 |    0 |    2 |  268 | bothbosu, call_transcripts, kaggle_scam_nonscam, usenix_romance |
| val     |    587 |        0 |     69.3 |       180 |  180 |   18 |    0 |  143 |  201 |    0 |    0 |    0 |   45 | bothbosu, call_transcripts, kaggle_scam_nonscam, usenix_romance |
| test    |   2305 |        0 |     75.1 |       575 |  575 |  360 |  360 |    0 |    0 |  358 |  297 |  355 |    0 | synthetic_own                                                   |

Test C: evaluate.py truncates every test set above to its first 50 words.
