# Shortcut check (before training)

Labelled rows: 7390

## 1. Label x source x real/synthetic

|                                      |   genuine (0) |   scam (1) |   All |
|:-------------------------------------|--------------:|-----------:|------:|
| ('bothbosu', 'synthetic')            |           839 |       1222 |  2061 |
| ('call_transcripts', 'synthetic')    |            25 |         44 |    69 |
| ('kaggle_scam_nonscam', 'synthetic') |           400 |        391 |   791 |
| ('robocall', 'real')                 |             2 |        590 |   592 |
| ('synthetic_own', 'synthetic')       |           575 |       1730 |  2305 |
| ('usenix_romance', 'synthetic')      |             0 |       1327 |  1327 |
| ('youtube_scam', 'real')             |             0 |        245 |   245 |
| ('All', '')                          |          1841 |       5549 |  7390 |

## 2. Real vs synthetic per label

| label_name   |   real |   synthetic |   All |
|:-------------|-------:|------------:|------:|
| genuine (0)  |      2 |        1839 |  1841 |
| scam (1)     |    835 |        4714 |  5549 |
| All          |    837 |        6553 |  7390 |

Share of each label (%):

| label_name   |   real |   synthetic |
|:-------------|-------:|------------:|
| genuine (0)  |    0.1 |        99.9 |
| scam (1)     |   15   |        85   |

**⚠️ WARNING — real/synthetic shortcut:** 99.8% of real rows are scams (837 rows). A model can learn "real recording → scam" instead of scam language.

**⚠️ WARNING — single-label source:** `usenix_romance` is 100% scam (1327 rows, 18% of data) — its style can stand in for the label.

**⚠️ WARNING — single-label source:** `youtube_scam` is 100% scam (245 rows, 3% of data) — its style can stand in for the label.

## 3. Transcript length (words)

Per label:

| label_name   |   count |   mean |   median |
|:-------------|--------:|-------:|---------:|
| genuine (0)  |    1841 |    110 |       72 |
| scam (1)     |    5549 |    148 |      151 |

Per label x real/synthetic:

|                              |   count |   mean |   median |
|:-----------------------------|--------:|-------:|---------:|
| ('genuine (0)', 'real')      |       2 |     14 |       14 |
| ('genuine (0)', 'synthetic') |    1839 |    110 |       72 |
| ('scam (1)', 'real')         |     835 |     89 |       64 |
| ('scam (1)', 'synthetic')    |    4714 |    158 |      163 |

Per source:

| source              |   count |   mean |   median |
|:--------------------|--------:|-------:|---------:|
| bothbosu            |    2061 |    188 |      182 |
| call_transcripts    |      69 |    200 |      193 |
| kaggle_scam_nonscam |     791 |     45 |       35 |
| robocall            |     592 |     60 |       53 |
| synthetic_own       |    2305 |     79 |       73 |
| usenix_romance      |    1327 |    249 |      248 |
| youtube_scam        |     245 |    157 |      158 |

Per source x label:

| source              |   genuine (0) |   scam (1) |
|:--------------------|--------------:|-----------:|
| bothbosu            |         185   |        182 |
| call_transcripts    |         194   |        191 |
| kaggle_scam_nonscam |          29   |         46 |
| robocall            |          14.5 |         53 |
| synthetic_own       |          58   |         79 |
| usenix_romance      |         nan   |        248 |
| youtube_scam        |         nan   |        158 |

**⚠️ WARNING — length shortcut:** median length differs by 2.1x between labels (genuine (0) 72, scam (1) 151 words).

**⚠️ WARNING — source length gap:** kaggle_scam_nonscam averages 45 words vs usenix_romance 249 words.
