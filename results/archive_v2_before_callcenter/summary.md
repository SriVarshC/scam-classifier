# Results

Threshold chosen on validation so FPR <= 2%. `first50` = Test C (first 50 words).

## Binary scam detection + fraud-type macro F1

| model         | test                  | variant   |   fpr |   recall |   precision |   f1_binary |   roc_auc |   macro_f1_types |   tn |   fp |   fn |   tp |
|:--------------|:----------------------|:----------|------:|---------:|------------:|------------:|----------:|-----------------:|-----:|-----:|-----:|-----:|
| keyword_rules | A                     | full      | 0.019 |    0.561 |       0.987 |       0.715 |     0.875 |            0.374 |  258 |    5 |  287 |  367 |
| keyword_rules | A                     | first50   | 0     |    0.287 |       1     |       0.447 |     0.829 |            0.281 |  263 |    0 |  466 |  188 |
| tfidf_lr      | A                     | full      | 0.03  |    0.998 |       0.988 |       0.993 |     1     |            0.976 |  255 |    8 |    1 |  653 |
| tfidf_lr      | A                     | first50   | 0.034 |    0.988 |       0.986 |       0.987 |     0.999 |            0.957 |  254 |    9 |    8 |  646 |
| embedding_lr  | A                     | full      | 0.027 |    0.98  |       0.989 |       0.985 |     0.997 |            0.965 |  256 |    7 |   13 |  641 |
| embedding_lr  | A                     | first50   | 0.027 |    0.846 |       0.988 |       0.911 |     0.975 |            0.854 |  256 |    7 |  101 |  553 |
| keyword_rules | B_bothbosu            | full      | 0.006 |    0.814 |       0.995 |       0.896 |     0.983 |            0.768 |  834 |    5 |  227 |  995 |
| keyword_rules | B_bothbosu            | first50   | 0     |    0.252 |       1     |       0.403 |     0.933 |            0.404 |  839 |    0 |  914 |  308 |
| tfidf_lr      | B_bothbosu            | full      | 0.968 |    1     |       0.601 |       0.751 |     0.976 |            0.365 |   27 |  812 |    0 | 1222 |
| tfidf_lr      | B_bothbosu            | first50   | 0.779 |    0.997 |       0.651 |       0.787 |     0.889 |            0.542 |  185 |  654 |    4 | 1218 |
| embedding_lr  | B_bothbosu            | full      | 0.435 |    0.917 |       0.754 |       0.827 |     0.83  |            0.505 |  474 |  365 |  102 | 1120 |
| embedding_lr  | B_bothbosu            | first50   | 0.131 |    0.547 |       0.859 |       0.668 |     0.836 |            0.336 |  729 |  110 |  554 |  668 |
| keyword_rules | B_call_transcripts    | full      | 0.04  |    0.517 |       0.938 |       0.667 |     0.894 |            0.419 |   24 |    1 |   14 |   15 |
| keyword_rules | B_call_transcripts    | first50   | 0     |    0.172 |       1     |       0.294 |     0.849 |            0.184 |   25 |    0 |   24 |    5 |
| tfidf_lr      | B_call_transcripts    | full      | 0.48  |    1     |       0.707 |       0.829 |     0.999 |            0.283 |   13 |   12 |    0 |   29 |
| tfidf_lr      | B_call_transcripts    | first50   | 0.16  |    0.828 |       0.857 |       0.842 |     0.946 |            0.345 |   21 |    4 |    5 |   24 |
| embedding_lr  | B_call_transcripts    | full      | 0     |    0.724 |       1     |       0.84  |     0.945 |            0.572 |   25 |    0 |    8 |   21 |
| embedding_lr  | B_call_transcripts    | first50   | 0     |    0.552 |       1     |       0.711 |     0.883 |            0.587 |   25 |    0 |   13 |   16 |
| keyword_rules | B_kaggle_scam_nonscam | full      | 0.002 |    0.142 |       0.974 |       0.248 |     0.824 |            0.226 |  399 |    1 |  229 |   38 |
| keyword_rules | B_kaggle_scam_nonscam | first50   | 0.002 |    0.232 |       0.984 |       0.376 |     0.802 |            0.273 |  399 |    1 |  205 |   62 |
| tfidf_lr      | B_kaggle_scam_nonscam | full      | 1     |    1     |       0.4   |       0.572 |     0.864 |            0.102 |    0 |  400 |    0 |  267 |
| tfidf_lr      | B_kaggle_scam_nonscam | first50   | 0.97  |    0.996 |       0.407 |       0.578 |     0.832 |            0.116 |   12 |  388 |    1 |  266 |
| embedding_lr  | B_kaggle_scam_nonscam | full      | 0.058 |    0.464 |       0.844 |       0.599 |     0.792 |            0.312 |  377 |   23 |  143 |  124 |
| embedding_lr  | B_kaggle_scam_nonscam | first50   | 0.068 |    0.468 |       0.822 |       0.597 |     0.782 |            0.329 |  373 |   27 |  142 |  125 |
| keyword_rules | B_real                | full      | 0     |    0.222 |       1     |       0.363 |     0.865 |            0.121 |    2 |    0 |  636 |  181 |
| keyword_rules | B_real                | first50   | 0     |    0.182 |       1     |       0.308 |     0.825 |            0.125 |    2 |    0 |  668 |  149 |
| tfidf_lr      | B_real                | full      | 0     |    0.965 |       1     |       0.982 |     0.989 |            0.409 |    2 |    0 |   29 |  788 |
| tfidf_lr      | B_real                | first50   | 0     |    0.903 |       1     |       0.949 |     0.963 |            0.373 |    2 |    0 |   79 |  738 |
| embedding_lr  | B_real                | full      | 0     |    0.588 |       1     |       0.74  |     0.979 |            0.344 |    2 |    0 |  337 |  480 |
| embedding_lr  | B_real                | first50   | 0     |    0.506 |       1     |       0.672 |     0.965 |            0.31  |    2 |    0 |  404 |  413 |
| keyword_rules | B_synthetic_own       | full      | 0.005 |    0.082 |       0.979 |       0.15  |     0.551 |            0.165 |  572 |    3 | 1589 |  141 |
| keyword_rules | B_synthetic_own       | first50   | 0.096 |    0.187 |       0.855 |       0.307 |     0.543 |            0.206 |  520 |   55 | 1406 |  324 |
| tfidf_lr      | B_synthetic_own       | full      | 0.551 |    0.788 |       0.811 |       0.799 |     0.722 |            0.072 |  258 |  317 |  367 | 1363 |
| tfidf_lr      | B_synthetic_own       | first50   | 0.477 |    0.71  |       0.818 |       0.76  |     0.677 |            0.091 |  301 |  274 |  502 | 1228 |
| embedding_lr  | B_synthetic_own       | full      | 0.311 |    0.62  |       0.857 |       0.719 |     0.661 |            0.228 |  396 |  179 |  658 | 1072 |
| embedding_lr  | B_synthetic_own       | first50   | 0.306 |    0.543 |       0.842 |       0.661 |     0.607 |            0.196 |  399 |  176 |  790 |  940 |

## Per fraud type F1 (full transcripts; types absent from a test set are blank)

|                                            |   F0 |     F1 |     F2 |     F3 |     F4 |     F6 |   F7 |     F8 |     F9 |
|:-------------------------------------------|-----:|-------:|-------:|-------:|-------:|-------:|-----:|-------:|-------:|
| ('embedding_lr', 'A')                      | 0.96 |   0.91 |   0.97 |   0.99 |   0.95 |   1    |    1 |   1    |   0.91 |
| ('embedding_lr', 'B_bothbosu')             | 0.67 | nan    | nan    |   0.68 |   0.66 | nan    |  nan | nan    |   0    |
| ('embedding_lr', 'B_call_transcripts')     | 0.86 |   0.33 | nan    |   0.71 |   0.53 | nan    |  nan |   1    |   0    |
| ('embedding_lr', 'B_kaggle_scam_nonscam')  | 0.82 |   0.23 | nan    |   0.4  |   0.11 | nan    |  nan | nan    |   0    |
| ('embedding_lr', 'B_real')                 | 0.01 |   0.64 | nan    |   0.8  |   0.61 | nan    |  nan |   0    |   0    |
| ('embedding_lr', 'B_synthetic_own')        | 0.49 |   0.25 |   0    | nan    | nan    |   0    |    0 |   0.63 | nan    |
| ('keyword_rules', 'A')                     | 0.64 |   0.16 |   0    |   0.87 |   0.88 |   0.04 |    0 |   0.38 |   0.39 |
| ('keyword_rules', 'B_bothbosu')            | 0.88 | nan    | nan    |   0.81 |   0.9  | nan    |  nan | nan    |   0.49 |
| ('keyword_rules', 'B_call_transcripts')    | 0.76 |   0    | nan    |   0.5  |   0.5  | nan    |  nan |   0.5  |   0.25 |
| ('keyword_rules', 'B_kaggle_scam_nonscam') | 0.78 |   0.15 | nan    |   0.08 |   0.12 | nan    |  nan | nan    |   0    |
| ('keyword_rules', 'B_real')                | 0.01 |   0    | nan    |   0.26 |   0.46 | nan    |  nan |   0    |   0    |
| ('keyword_rules', 'B_synthetic_own')       | 0.42 |   0.22 |   0    | nan    | nan    |   0    |    0 |   0.36 | nan    |
| ('tfidf_lr', 'A')                          | 0.98 |   0.94 |   1    |   0.98 |   0.96 |   1    |    1 |   1    |   0.93 |
| ('tfidf_lr', 'B_bothbosu')                 | 0.06 | nan    | nan    |   0.82 |   0.57 | nan    |  nan | nan    |   0.01 |
| ('tfidf_lr', 'B_call_transcripts')         | 0.68 |   0    | nan    |   0.73 |   0.29 | nan    |  nan |   0    |   0    |
| ('tfidf_lr', 'B_kaggle_scam_nonscam')      | 0    |   0    | nan    |   0.34 |   0.13 | nan    |  nan | nan    |   0.04 |
| ('tfidf_lr', 'B_real')                     | 0.12 |   0.45 | nan    |   0.84 |   0.8  | nan    |  nan |   0    |   0.24 |
| ('tfidf_lr', 'B_synthetic_own')            | 0.43 |   0    |   0    | nan    | nan    |   0    |    0 |   0    | nan    |

Max test support per type: F0=839, F1=360, F2=360, F3=330, F4=619, F6=358, F7=297, F8=355, F9=273
