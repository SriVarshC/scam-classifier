# Results

Threshold chosen on validation so FPR <= 2%. `first50` = Test C (first 50 words).

## Binary scam detection + fraud-type macro F1

| model         | test                  | variant   |   fpr |   recall |   precision |   f1_binary |   roc_auc |   macro_f1_types |    tn |    fp |   fn |   tp |
|:--------------|:----------------------|:----------|------:|---------:|------------:|------------:|----------:|-----------------:|------:|------:|-----:|-----:|
| keyword_rules | A                     | full      | 0.011 |    0.56  |       0.987 |       0.715 |     0.882 |            0.405 |   462 |     5 |  287 |  366 |
| keyword_rules | A                     | first50   | 0.002 |    0.145 |       0.99  |       0.254 |     0.812 |            0.186 |   466 |     1 |  558 |   95 |
| tfidf_lr      | A                     | full      | 0.028 |    1     |       0.98  |       0.99  |     1     |            0.971 |   454 |    13 |    0 |  653 |
| tfidf_lr      | A                     | first50   | 0.024 |    0.995 |       0.983 |       0.989 |     0.999 |            0.963 |   456 |    11 |    3 |  650 |
| embedding_lr  | A                     | full      | 0.028 |    0.979 |       0.98  |       0.979 |     0.997 |            0.954 |   454 |    13 |   14 |  639 |
| embedding_lr  | A                     | first50   | 0.032 |    0.874 |       0.974 |       0.922 |     0.972 |            0.859 |   452 |    15 |   82 |  571 |
| keyword_rules | B_bothbosu            | full      | 0.002 |    0.696 |       0.998 |       0.82  |     0.983 |            0.693 |   835 |     2 |  370 |  848 |
| keyword_rules | B_bothbosu            | first50   | 0     |    0.258 |       1     |       0.41  |     0.938 |            0.406 |   837 |     0 |  904 |  314 |
| tfidf_lr      | B_bothbosu            | full      | 0.774 |    1     |       0.653 |       0.79  |     0.985 |            0.441 |   189 |   648 |    0 | 1218 |
| tfidf_lr      | B_bothbosu            | first50   | 0.459 |    0.913 |       0.743 |       0.819 |     0.873 |            0.615 |   453 |   384 |  106 | 1112 |
| embedding_lr  | B_bothbosu            | full      | 0.456 |    0.947 |       0.751 |       0.838 |     0.843 |            0.494 |   455 |   382 |   65 | 1153 |
| embedding_lr  | B_bothbosu            | first50   | 0.085 |    0.601 |       0.912 |       0.724 |     0.89  |            0.363 |   766 |    71 |  486 |  732 |
| keyword_rules | B_call_transcripts    | full      | 0.042 |    0.517 |       0.938 |       0.667 |     0.893 |            0.417 |    23 |     1 |   14 |   15 |
| keyword_rules | B_call_transcripts    | first50   | 0     |    0.103 |       1     |       0.188 |     0.848 |            0.159 |    24 |     0 |   26 |    3 |
| tfidf_lr      | B_call_transcripts    | full      | 0.333 |    1     |       0.784 |       0.879 |     1     |            0.308 |    16 |     8 |    0 |   29 |
| tfidf_lr      | B_call_transcripts    | first50   | 0.042 |    0.828 |       0.96  |       0.889 |     0.938 |            0.369 |    23 |     1 |    5 |   24 |
| embedding_lr  | B_call_transcripts    | full      | 0     |    0.828 |       1     |       0.906 |     0.964 |            0.628 |    24 |     0 |    5 |   24 |
| embedding_lr  | B_call_transcripts    | first50   | 0     |    0.517 |       1     |       0.682 |     0.92  |            0.547 |    24 |     0 |   14 |   15 |
| keyword_rules | B_kaggle_scam_nonscam | full      | 0     |    0.079 |       1     |       0.146 |     0.824 |            0.179 |   400 |     0 |  246 |   21 |
| keyword_rules | B_kaggle_scam_nonscam | first50   | 0.002 |    0.139 |       0.974 |       0.243 |     0.802 |            0.22  |   399 |     1 |  230 |   37 |
| tfidf_lr      | B_kaggle_scam_nonscam | full      | 0.992 |    1     |       0.402 |       0.574 |     0.874 |            0.114 |     3 |   397 |    0 |  267 |
| tfidf_lr      | B_kaggle_scam_nonscam | first50   | 0.992 |    1     |       0.402 |       0.574 |     0.843 |            0.113 |     3 |   397 |    0 |  267 |
| embedding_lr  | B_kaggle_scam_nonscam | full      | 0.092 |    0.468 |       0.772 |       0.583 |     0.786 |            0.312 |   363 |    37 |  142 |  125 |
| embedding_lr  | B_kaggle_scam_nonscam | first50   | 0.098 |    0.487 |       0.769 |       0.596 |     0.774 |            0.329 |   361 |    39 |  137 |  130 |
| keyword_rules | B_real                | full      | 0.008 |    0.22  |       0.605 |       0.323 |     0.812 |            0.278 | 14885 |   117 |  635 |  179 |
| keyword_rules | B_real                | first50   | 0     |    0.066 |       0.915 |       0.124 |     0.812 |            0.204 | 14997 |     5 |  760 |   54 |
| tfidf_lr      | B_real                | full      | 0.855 |    0.968 |       0.058 |       0.109 |     0.778 |            0.19  |  2175 | 12827 |   26 |  788 |
| tfidf_lr      | B_real                | first50   | 0.671 |    0.859 |       0.065 |       0.121 |     0.747 |            0.133 |  4935 | 10067 |  115 |  699 |
| embedding_lr  | B_real                | full      | 0.026 |    0.593 |       0.556 |       0.574 |     0.934 |            0.471 | 14616 |   386 |  331 |  483 |
| embedding_lr  | B_real                | first50   | 0.053 |    0.517 |       0.348 |       0.416 |     0.878 |            0.4   | 14214 |   788 |  393 |  421 |
| keyword_rules | B_synthetic_own       | full      | 0.005 |    0.082 |       0.979 |       0.151 |     0.551 |            0.165 |   572 |     3 | 1588 |  141 |
| keyword_rules | B_synthetic_own       | first50   | 0     |    0.025 |       1     |       0.049 |     0.543 |            0.102 |   575 |     0 | 1686 |   43 |
| tfidf_lr      | B_synthetic_own       | full      | 0.56  |    0.854 |       0.821 |       0.837 |     0.764 |            0.078 |   253 |   322 |  252 | 1477 |
| tfidf_lr      | B_synthetic_own       | first50   | 0.461 |    0.776 |       0.835 |       0.805 |     0.718 |            0.087 |   310 |   265 |  387 | 1342 |
| embedding_lr  | B_synthetic_own       | full      | 0.27  |    0.403 |       0.818 |       0.54  |     0.654 |            0.127 |   420 |   155 | 1033 |  696 |
| embedding_lr  | B_synthetic_own       | first50   | 0.259 |    0.373 |       0.812 |       0.511 |     0.622 |            0.137 |   426 |   149 | 1084 |  645 |
| keyword_rules | R                     | full      | 0.008 |    0.178 |       0.538 |       0.268 |     0.805 |            0.313 |  2125 |    18 |   97 |   21 |
| keyword_rules | R                     | first50   | 0.004 |    0.424 |       0.847 |       0.565 |     0.814 |            0.545 |  2134 |     9 |   68 |   50 |
| tfidf_lr      | R                     | full      | 0.021 |    1     |       0.724 |       0.84  |     1     |            0.852 |  2098 |    45 |    0 |  118 |
| tfidf_lr      | R                     | first50   | 0.033 |    0.992 |       0.622 |       0.765 |     0.997 |            0.777 |  2072 |    71 |    1 |  117 |
| embedding_lr  | R                     | full      | 0.023 |    0.983 |       0.699 |       0.817 |     0.999 |            0.751 |  2093 |    50 |    2 |  116 |
| embedding_lr  | R                     | first50   | 0.018 |    0.915 |       0.735 |       0.815 |     0.987 |            0.756 |  2104 |    39 |   10 |  108 |

## Per fraud type F1 (full transcripts; types absent from a test set are blank)

|                                            |   F0 |     F1 |     F2 |     F3 |     F4 |     F6 |     F7 |     F8 |     F9 |
|:-------------------------------------------|-----:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| ('embedding_lr', 'A')                      | 0.97 |   0.89 |   0.98 |   0.96 |   0.96 |   0.97 |   0.99 |   0.99 |   0.88 |
| ('embedding_lr', 'B_bothbosu')             | 0.67 | nan    | nan    |   0.62 |   0.68 | nan    | nan    | nan    |   0.01 |
| ('embedding_lr', 'B_call_transcripts')     | 0.91 |   0.33 | nan    |   0.78 |   0.5  | nan    | nan    |   1    |   0.25 |
| ('embedding_lr', 'B_kaggle_scam_nonscam')  | 0.8  |   0.25 | nan    |   0.4  |   0.11 | nan    | nan    | nan    |   0    |
| ('embedding_lr', 'B_real')                 | 0.98 |   0.6  | nan    |   0.65 |   0.6  | nan    | nan    |   0    |   0    |
| ('embedding_lr', 'B_synthetic_own')        | 0.41 |   0.25 |   0    | nan    | nan    |   0    |   0    |   0.1  | nan    |
| ('embedding_lr', 'R')                      | 0.99 |   0.8  | nan    |   0.92 |   0.83 | nan    | nan    | nan    |   0.21 |
| ('keyword_rules', 'A')                     | 0.76 |   0.16 |   0    |   0.8  |   0.9  |   0.26 |   0    |   0.4  |   0.36 |
| ('keyword_rules', 'B_bothbosu')            | 0.82 | nan    | nan    |   0.75 |   0.86 | nan    | nan    | nan    |   0.35 |
| ('keyword_rules', 'B_call_transcripts')    | 0.75 |   0    | nan    |   0.5  |   0.5  | nan    | nan    |   0.5  |   0.25 |
| ('keyword_rules', 'B_kaggle_scam_nonscam') | 0.76 |   0.03 | nan    |   0.06 |   0.04 | nan    | nan    | nan    |   0    |
| ('keyword_rules', 'B_real')                | 0.98 |   0    | nan    |   0.24 |   0.45 | nan    | nan    |   0    |   0    |
| ('keyword_rules', 'B_synthetic_own')       | 0.42 |   0.22 |   0    | nan    | nan    |   0    |   0    |   0.36 | nan    |
| ('keyword_rules', 'R')                     | 0.97 |   0    | nan    |   0.16 |   0.43 | nan    | nan    | nan    |   0    |
| ('tfidf_lr', 'A')                          | 0.99 |   0.9  |   1    |   0.96 |   0.97 |   1    |   1    |   0.99 |   0.93 |
| ('tfidf_lr', 'B_bothbosu')                 | 0.37 | nan    | nan    |   0.8  |   0.59 | nan    | nan    | nan    |   0.01 |
| ('tfidf_lr', 'B_call_transcripts')         | 0.8  |   0    | nan    |   0.73 |   0.32 | nan    | nan    |   0    |   0    |
| ('tfidf_lr', 'B_kaggle_scam_nonscam')      | 0.01 |   0    | nan    |   0.38 |   0.14 | nan    | nan    | nan    |   0.04 |
| ('tfidf_lr', 'B_real')                     | 0.25 |   0.53 | nan    |   0.13 |   0.06 | nan    | nan    |   0    |   0.16 |
| ('tfidf_lr', 'B_synthetic_own')            | 0.47 |   0    |   0    | nan    | nan    |   0    |   0    |   0    | nan    |
| ('tfidf_lr', 'R')                          | 0.99 |   0.91 | nan    |   0.93 |   0.76 | nan    | nan    | nan    |   0.67 |

Max test support per type: F0=15002, F1=360, F2=359, F3=330, F4=616, F6=358, F7=297, F8=355, F9=272
