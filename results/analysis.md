# Analysis

## 1. Top TF-IDF features (Test A model)

22 of the 270 top features (30 per class) are format/style tokens (marked *like this* in `top_words.txt`). F0 excerpt:

```
== F0 (6/30 flagged as format/style tokens)
would, *this is*, john, *thanks*, is from, *hi*, new, insurance, wanted, would you, wanted to, xyz, offering, from xyz, the wrong, delivery, you like, *is name*, re offering, just wanted, package, interested, re verified, let us, *name we*, dialed, company, thanks for, business, *wrong number*
```

## 2. Errors (TF-IDF + LR, all tests)

False positives: 1549 total, sample of 20 in `errors_fp.csv` — by source: {'kaggle_scam_nonscam': 7, 'call_transcripts': 5, 'bothbosu': 4, 'synthetic_own': 4}
False negatives: 397 total, sample of 20 in `errors_fn.csv` — by type: {'F4': 6, 'F6': 4, 'F7': 3, 'F3': 3, 'F1': 2, 'F8': 1, 'F2': 1}

## 3. Test A vs Test B gap

| model         |   A F1 |   B F1 (avg unseen sources) |   gap F1 |   A FPR |   B FPR (avg) |   A AUC |   B AUC (avg) |   real-scam recall (B_real) |
|:--------------|-------:|----------------------------:|---------:|--------:|--------------:|--------:|--------------:|----------------------------:|
| embedding_lr  |  0.985 |                       0.746 |    0.238 |   0.027 |         0.201 |   0.997 |         0.807 |                       0.588 |
| keyword_rules |  0.715 |                       0.49  |    0.225 |   0.019 |         0.013 |   0.875 |         0.813 |                       0.222 |
| tfidf_lr      |  0.993 |                       0.738 |    0.256 |   0.03  |         0.75  |   1     |         0.89  |                       0.965 |

## 4. Label-shuffle sanity check (TF-IDF + LR, Test A)

ROC-AUC with shuffled training labels = **0.521 ± 0.080** over 5 shuffles (0.47, 0.46, 0.45, 0.57, 0.66); exact train/test text overlap = 0. PASS — ≈ 0.5, no leakage through the pipeline.
