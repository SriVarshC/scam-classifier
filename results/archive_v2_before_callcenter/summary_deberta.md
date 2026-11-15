# Results

Threshold chosen on validation so FPR <= 2%. `first50` = Test C (first 50 words).

## Binary scam detection + fraud-type macro F1

| model   | test                  | variant   |   fpr |   recall |   precision |   f1_binary |   roc_auc |   macro_f1_types |   tn |   fp |   fn |   tp |
|:--------|:----------------------|:----------|------:|---------:|------------:|------------:|----------:|-----------------:|-----:|-----:|-----:|-----:|
| deberta | A                     | full      | 0.015 |    0.998 |       0.994 |       0.996 |     1     |            0.979 |  259 |    4 |    1 |  653 |
| deberta | A                     | first50   | 0.015 |    0.913 |       0.993 |       0.951 |     0.978 |            0.87  |  259 |    4 |   57 |  597 |
| deberta | B_bothbosu            | full      | 0.728 |    0.984 |       0.663 |       0.792 |     0.902 |            0.493 |  228 |  611 |   20 | 1202 |
| deberta | B_bothbosu            | first50   | 0.327 |    0.681 |       0.752 |       0.715 |     0.756 |            0.402 |  565 |  274 |  390 |  832 |
| deberta | B_call_transcripts    | full      | 0.92  |    0.966 |       0.549 |       0.7   |     0.898 |            0.205 |    2 |   23 |    1 |   28 |
| deberta | B_call_transcripts    | first50   | 0.32  |    1     |       0.784 |       0.879 |     0.979 |            0.481 |   17 |    8 |    0 |   29 |
| deberta | B_kaggle_scam_nonscam | full      | 0.965 |    0.993 |       0.407 |       0.577 |     0.79  |            0.132 |   14 |  386 |    2 |  265 |
| deberta | B_kaggle_scam_nonscam | first50   | 0.962 |    0.978 |       0.404 |       0.572 |     0.775 |            0.09  |   15 |  385 |    6 |  261 |
| deberta | B_real                | full      | 0     |    0.922 |       1     |       0.959 |     0.979 |            0.44  |    2 |    0 |   64 |  753 |
| deberta | B_real                | first50   | 0     |    0.718 |       1     |       0.836 |     0.9   |            0.395 |    2 |    0 |  230 |  587 |
| deberta | B_synthetic_own       | full      | 0.294 |    0.728 |       0.882 |       0.798 |     0.8   |            0.093 |  406 |  169 |  470 | 1260 |
| deberta | B_synthetic_own       | first50   | 0.157 |    0.504 |       0.906 |       0.648 |     0.724 |            0.091 |  485 |   90 |  858 |  872 |

## Per fraud type F1 (full transcripts; types absent from a test set are blank)

|                                      |   F0 |     F1 |   F2 |     F3 |     F4 |   F6 |   F7 |   F8 |     F9 |
|:-------------------------------------|-----:|-------:|-----:|-------:|-------:|-----:|-----:|-----:|-------:|
| ('deberta', 'A')                     | 0.99 |   0.97 |    1 |   0.99 |   0.97 |    1 |    1 |    1 |   0.89 |
| ('deberta', 'B_bothbosu')            | 0.42 | nan    |  nan |   0.8  |   0.68 |  nan |  nan |  nan |   0.07 |
| ('deberta', 'B_call_transcripts')    | 0.14 |   0    |  nan |   0.67 |   0.29 |  nan |  nan |    0 |   0.12 |
| ('deberta', 'B_kaggle_scam_nonscam') | 0.07 |   0.17 |  nan |   0.16 |   0.14 |  nan |  nan |  nan |   0.12 |
| ('deberta', 'B_real')                | 0.06 |   0.69 |  nan |   0.8  |   0.81 |  nan |  nan |    0 |   0.28 |
| ('deberta', 'B_synthetic_own')       | 0.56 |   0    |    0 | nan    | nan    |    0 |    0 |    0 | nan    |

Max test support per type: F0=839, F1=360, F2=360, F3=330, F4=619, F6=358, F7=297, F8=355, F9=273
