# Results

Threshold chosen on validation so FPR <= 2%. `first50` = Test C (first 50 words).

## Binary scam detection + fraud-type macro F1

| model   | test                  | variant   |   fpr |   recall |   precision |   f1_binary |   roc_auc |   macro_f1_types |   tn |    fp |   fn |   tp |
|:--------|:----------------------|:----------|------:|---------:|------------:|------------:|----------:|-----------------:|-----:|------:|-----:|-----:|
| deberta | A                     | full      | 0.024 |    1     |       0.983 |       0.992 |     1     |            0.972 |  456 |    11 |    0 |  653 |
| deberta | A                     | first50   | 0.026 |    0.907 |       0.98  |       0.942 |     0.97  |            0.853 |  455 |    12 |   61 |  592 |
| deberta | B_bothbosu            | full      | 0.663 |    0.996 |       0.686 |       0.812 |     0.888 |            0.463 |  282 |   555 |    5 | 1213 |
| deberta | B_bothbosu            | first50   | 0.049 |    0.526 |       0.94  |       0.675 |     0.846 |            0.444 |  796 |    41 |  577 |  641 |
| deberta | B_call_transcripts    | full      | 0.625 |    1     |       0.659 |       0.795 |     0.889 |            0.311 |    9 |    15 |    0 |   29 |
| deberta | B_call_transcripts    | first50   | 0     |    0.69  |       1     |       0.816 |     0.98  |            0.53  |   24 |     0 |    9 |   20 |
| deberta | B_kaggle_scam_nonscam | full      | 0.69  |    0.925 |       0.472 |       0.625 |     0.779 |            0.278 |  124 |   276 |   20 |  247 |
| deberta | B_kaggle_scam_nonscam | first50   | 0.352 |    0.685 |       0.565 |       0.619 |     0.748 |            0.295 |  259 |   141 |   84 |  183 |
| deberta | B_real                | full      | 0.732 |    0.912 |       0.063 |       0.118 |     0.743 |            0.16  | 4026 | 10976 |   72 |  742 |
| deberta | B_real                | first50   | 0.405 |    0.678 |       0.083 |       0.148 |     0.714 |            0.259 | 8925 |  6077 |  262 |  552 |
| deberta | B_synthetic_own       | full      | 0.343 |    0.783 |       0.873 |       0.825 |     0.782 |            0.096 |  378 |   197 |  376 | 1353 |
| deberta | B_synthetic_own       | first50   | 0.257 |    0.63  |       0.88  |       0.734 |     0.707 |            0.112 |  427 |   148 |  640 | 1089 |
| deberta | R                     | full      | 0.025 |    1     |       0.686 |       0.814 |     1     |            0.78  | 2089 |    54 |    0 |  118 |
| deberta | R                     | first50   | 0.021 |    0.941 |       0.716 |       0.813 |     0.988 |            0.761 | 2099 |    44 |    7 |  111 |

## Per fraud type F1 (full transcripts; types absent from a test set are blank)

|                                      |   F0 |     F1 |   F2 |     F3 |     F4 |   F6 |     F7 |     F8 |     F9 |
|:-------------------------------------|-----:|-------:|-----:|-------:|-------:|-----:|-------:|-------:|-------:|
| ('deberta', 'A')                     | 0.99 |   0.96 |    1 |   0.98 |   0.96 |    1 |   0.99 |   0.99 |   0.89 |
| ('deberta', 'B_bothbosu')            | 0.5  | nan    |  nan |   0.73 |   0.54 |  nan | nan    | nan    |   0.08 |
| ('deberta', 'B_call_transcripts')    | 0.55 |   0    |  nan |   0.7  |   0.42 |  nan | nan    |   0    |   0.21 |
| ('deberta', 'B_kaggle_scam_nonscam') | 0.46 |   0.02 |  nan |   0.57 |   0.23 |  nan | nan    | nan    |   0.12 |
| ('deberta', 'B_real')                | 0.42 |   0.07 |  nan |   0.22 |   0.25 |  nan | nan    |   0    |   0    |
| ('deberta', 'B_synthetic_own')       | 0.57 |   0    |    0 | nan    | nan    |    0 |   0    |   0    | nan    |
| ('deberta', 'R')                     | 0.99 |   0.95 |  nan |   0.83 |   0.85 |  nan | nan    | nan    |   0.29 |

Max test support per type: F0=15002, F1=360, F2=359, F3=330, F4=616, F6=358, F7=297, F8=355, F9=272
