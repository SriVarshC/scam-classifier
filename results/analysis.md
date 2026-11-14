# Analysis

## 1. Top TF-IDF features (Test A model)

33 of the 300 top features (30 per class) are format/style tokens (marked *like this* in `top_words.txt`). F0 excerpt:

```
== F0 (14/30 flagged as format/style tokens)
help, *help you*, *ok*, *thanks*, *can help*, *id*, *great*, *anything else*, else, order, *name*, may, *thank*, *thank you*, anything, how, day, today, you with, *hi*, can, *there anything*, *is there*, *order id*, you today, account id, have, would, how can, hello
```

## 2. Errors (TF-IDF + LR, all tests)

False positives: 9589 total, sample of 20 in `errors_fp.csv` — by source: {'abcd': 19, 'robocall': 1}
False negatives: 33 total, sample of 20 in `errors_fn.csv` — by type: {'F4': 13, 'F3': 6, 'F9': 1}

## 3. Test A vs Test B gap

| model         |   A F1 |   B F1 (avg) |   gap F1 |   A FPR |   B FPR (avg) |   A AUC |   B AUC (avg) |
|:--------------|-------:|-------------:|---------:|--------:|--------------:|--------:|--------------:|
| embedding_lr  |  0.86  |        0.435 |    0.424 |   0.023 |         0.124 |   1     |         0.966 |
| keyword_rules |  0     |        0.044 |   -0.044 |   0.021 |         0.076 |   0.577 |         0.581 |
| tfidf_lr      |  0.878 |        0.496 |    0.382 |   0.02  |         0.467 |   1     |         0.998 |

## 4. Label-shuffle sanity check (TF-IDF + LR, Test A)

ROC-AUC with shuffled training labels = **0.557 ± 0.066** over 5 shuffles (0.63, 0.52, 0.45, 0.62, 0.56); exact train/test text overlap = 0. PASS — ≈ 0.5, no leakage through the pipeline.
