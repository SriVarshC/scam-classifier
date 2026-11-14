# Results

Threshold chosen on validation so FPR <= 2%. `first50` = Test C (first 50 words).

## Binary scam detection + fraud-type macro F1

| model         | test       | variant   |   fpr |   recall |   precision |   f1_binary |   roc_auc |   macro_f1_types |    tn |   fp |   fn |   tp |
|:--------------|:-----------|:----------|------:|---------:|------------:|------------:|----------:|-----------------:|------:|-----:|-----:|-----:|
| keyword_rules | A          | full      | 0.021 |    0     |       0     |       0     |     0.577 |            0.191 |  1433 |   31 |  104 |    0 |
| keyword_rules | A          | first50   | 0.018 |    0.221 |       0.469 |       0.301 |     0.728 |            0.326 |  1438 |   26 |   81 |   23 |
| tfidf_lr      | A          | full      | 0.02  |    1     |       0.782 |       0.878 |     1     |            0.826 |  1435 |   29 |    0 |  104 |
| tfidf_lr      | A          | first50   | 0.02  |    1     |       0.776 |       0.874 |     1     |            0.825 |  1434 |   30 |    0 |  104 |
| embedding_lr  | A          | full      | 0.023 |    1     |       0.754 |       0.86  |     1     |            0.681 |  1430 |   34 |    0 |  104 |
| embedding_lr  | A          | first50   | 0.018 |    1     |       0.794 |       0.885 |     1     |            0.709 |  1437 |   27 |    0 |  104 |
| keyword_rules | B_abcd     | full      | 0.114 |    0.106 |       0.009 |       0.017 |     0.586 |            0.213 |  9085 | 1167 |   93 |   11 |
| keyword_rules | B_abcd     | first50   | 0.014 |    0.221 |       0.137 |       0.169 |     0.73  |            0.281 | 10107 |  145 |   81 |   23 |
| tfidf_lr      | B_abcd     | full      | 0.932 |    1     |       0.011 |       0.021 |     0.996 |            0.419 |   693 | 9559 |    0 |  104 |
| tfidf_lr      | B_abcd     | first50   | 0.798 |    1     |       0.013 |       0.025 |     0.995 |            0.36  |  2067 | 8185 |    0 |  104 |
| embedding_lr  | B_abcd     | full      | 0.246 |    0.913 |       0.036 |       0.07  |     0.937 |            0.418 |  7726 | 2526 |    9 |   95 |
| embedding_lr  | B_abcd     | first50   | 0.238 |    0.923 |       0.038 |       0.073 |     0.942 |            0.394 |  7811 | 2441 |    8 |   96 |
| keyword_rules | B_robocall | full      | 0.039 |    0.041 |       0.296 |       0.072 |     0.577 |            0.196 |  1409 |   57 |  566 |   24 |
| keyword_rules | B_robocall | first50   | 0.018 |    0.207 |       0.824 |       0.331 |     0.715 |            0.336 |  1440 |   26 |  468 |  122 |
| tfidf_lr      | B_robocall | full      | 0.001 |    0.944 |       0.998 |       0.97  |     0.999 |            0.488 |  1465 |    1 |   33 |  557 |
| tfidf_lr      | B_robocall | first50   | 0.005 |    0.942 |       0.986 |       0.964 |     0.998 |            0.49  |  1458 |    8 |   34 |  556 |
| embedding_lr  | B_robocall | full      | 0.001 |    0.669 |       0.997 |       0.801 |     0.995 |            0.535 |  1465 |    1 |  195 |  395 |
| embedding_lr  | B_robocall | first50   | 0.003 |    0.683 |       0.99  |       0.808 |     0.995 |            0.524 |  1462 |    4 |  187 |  403 |

## Per fraud type F1 (full transcripts; types absent from a test set are blank)

|                                 |   F0 |   F1 |   F3 |   F4 |   F9 |
|:--------------------------------|-----:|-----:|-----:|-----:|-----:|
| ('embedding_lr', 'A')           | 0.99 | 0.47 | 0.94 | 0.79 | 0.22 |
| ('embedding_lr', 'B_abcd')      | 0.86 | 0.24 | 0.91 | 0.05 | 0.03 |
| ('embedding_lr', 'B_robocall')  | 0.94 | 0.34 | 0.85 | 0.55 | 0    |
| ('keyword_rules', 'A')          | 0.96 | 0    | 0    | 0    | 0    |
| ('keyword_rules', 'B_abcd')     | 0.94 | 0    | 0.11 | 0.02 | 0    |
| ('keyword_rules', 'B_robocall') | 0.82 | 0    | 0.13 | 0.03 | 0    |
| ('tfidf_lr', 'A')               | 0.99 | 0.89 | 0.94 | 0.81 | 0.5  |
| ('tfidf_lr', 'B_abcd')          | 0.13 | 0.95 | 0.51 | 0.01 | 0.5  |
| ('tfidf_lr', 'B_robocall')      | 0.99 | 0    | 0.78 | 0.67 | 0    |

Max test support per type: F0=10252, F1=54, F3=267, F4=247, F9=22
