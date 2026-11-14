# CLAUDE.md — Scam Call Classifier Experiment

## What this project is
An experiment to test whether a model can classify phone call **transcripts** as
**scam/spam (label 1)** or **legitimate (label 0)** — and, most importantly, whether it
still works on **unseen data from a different source**.

This classifier will later become *one signal* inside **Gatekeeper**, an AI agent that
screens phone calls for financial fraud. It will never decide alone, so the goal is an
honest, reliable signal with very few false alarms — not a perfect score.

**Scope for now:** text transcripts only. No audio, telephony, live calls or dashboard yet.

## The one question to answer
> If we train on spam and legitimate call transcripts, can the model correctly classify
> calls it has never seen — including calls from a completely different dataset?

**Most important metric:** false positive rate (real calls wrongly called spam). Target ≤ 2%.

---

## Task spec v2 (current — supersedes binary-only parts below)
**Input:** call transcript text. **Output:** fraud type F0–F9. The binary scam/legit label
(`label` = 0 if F0 else 1) is still derived and reported, because FPR is measured on it.

### Fraud labels
| Code | Meaning |
|---|---|
| F0 | Not fraud (includes legal telemarketing, wrong numbers, genuine service calls) |
| F1 | Financial impersonation (bank, Zelle, card issuer) |
| F2 | Account takeover |
| F3 | Government impersonation (IRS, SSA, police) |
| F4 | Tech support / business impersonation (Amazon, Microsoft, refunds) |
| F5 | Romance / catfishing |
| F6 | Pig-butchering / investment |
| F7 | Honeytrap / sextortion |
| F8 | Family emergency / voice clone |
| F9 | Prize / job / advance-fee |

### Models
- **Baseline:** TF-IDF + logistic regression (multi-class).
- **Main model:** fine-tuned DeBERTa (GPU; Colab).
- Keyword rules and embeddings + LR remain as extra baselines.

### Final data mix
| Item | Rule |
|---|---|
| Overall split | 70 / 15 / 15 train / val / test |
| Synthetic share of training set | At most 30% |
| Fraud vs genuine in training | About 50 / 50, balanced with class weights |
| Fraud vs genuine in test | Real-world ratio (mostly genuine) |
| Leakage prevention | Split by call or scam campaign (group k-fold style; e.g. robocall `case_details`) |
| Min training examples per fraud type | 300 (top up with synthetic, training only) |
| Synthetic data in val / test | Never — real data only |

### Good enough
| Metric | Target |
|---|---|
| Macro F1 on real test set | ≥ 0.85 |
| FPR on genuine calls (F0) | < 2% |
| Retrain trigger | Any fraud type F1 < 0.70 → add data and retrain |

### Decisions made
- BothBosu `telemarketing` and `wrong` stay **F0** (fraud-only definition).
- Robocall non-English rows (54 `zh`) are kept and tagged but **excluded from training/eval**.
- Robocall rows need a per-row fraud type; legal-telemarketing robocalls → F0.

### Proposed source → fraud-type mapping (verify during loading)
| Source | Mapping |
|---|---|
| ABCD | all F0 |
| BothBosu | ssn → F3, refund → F4, support → F4, reward → F9; delivery / insurance / telemarketing / wrong → F0 |
| USENIX | romance_baiting → F5, tax_scam → F3, e-commerce → F4, neutral → F0 |
| Robocall | per row (expected mostly F1, F3, F4, F9, some F0) — needs labelling |

---

## Ground rules (always follow)
1. **Never modify files in `data/raw/`.** All processing writes to `data/processed/`.
2. **Inspect before mapping.** Before writing a loader, print each raw file's columns,
   row count, label values and 3 sample rows. Never guess column names.
3. **Deduplicate before splitting.** Exact and near-duplicates (similarity > 0.95) are
   removed *before* any train/validation/test split.
4. **Never tune on test data.** Thresholds, hyperparameters and keyword lists are chosen
   on the validation set only.
5. **Fix random seeds** (`SEED = 42`) everywhere: splits, models, sampling.
6. **Prevent source shortcuts.** Apply the same normalization to every source so the model
   learns scam language, not dataset formatting.
7. **Report honestly.** Always report Test B (leave-one-source-out) next to Test A, plus
   the false positive rate and confusion matrix. Never report accuracy alone.
8. **Ask before** downloading anything over ~1 GB, using a paid API (e.g. the zero-shot
   LLM), or installing GPU-only packages.
9. **No real personal data.** Use only the public datasets listed below or synthetic data.
10. Keep code simple, readable and modular — one responsibility per file.

---

## Datasets (download into `data/raw/<folder>/`)

### Primary dataset plan (v2 — current)
| Order | Folder | Dataset | Type | Fraud types | Train | Val | Test | Link |
|---|---|---|---|---|---|---|---|---|
| 1 | `abcd` | ABCD (genuine customer-service calls) | Real (genuine) | F0 | 70% | 15% | 15% | https://github.com/asappresearch/abcd |
| 2 | `robocall` | Robocall Audio Dataset (scam calls) | Real (scam) | F3, F4, F9 | 60% | 20% | 20% | https://github.com/wspr-ncsu/robocall-audio-dataset |
| 3 | `bothbosu` | BothBosu scam-dialogue | Synthetic (scam + normal) | F1, F4 | 100% | 0% | 0% | https://huggingface.co/datasets/BothBosu/scam-dialogue |
| 4 | `usenix_romance` | USENIX romance-baiting artifact | Synthetic (romance, tax, e-commerce, neutral) | F5, F3, F4, F0 | 100% | 0% | 0% | https://secartifacts.github.io/usenixsec2026/appendix-files/sec26cycle1ae-final154.pdf |
| 5 | `aston_romance` | Aston Romance Fraud Messages | Real (romance) | F5 | 60% | 20% | 20% | https://fold.aston.ac.uk/handle/123456789/38 |
| 6 | `anatomy_scam` | Anatomy of a Scam Call (email the authors; add when received) | Real (scam) | F1, F3, F4, F9 | 60% | 20% | 20% | https://tldr.takara.ai/p/2608.24127 |
| 7 | `synthetic_own` | Own synthetic conversations for the gaps | Synthetic | F2, F6, F7, F8, F1 (Zelle) | 100% | 0% | 0% | — (generated) |

Notes on v2:
- **Synthetic sources are train-only**; validation and test come from real data, so the
  reported numbers measure real-world performance.
- Fraud-type codes: F0 = genuine/legitimate. F1–F9 definitions are TBD — record them in
  `README.md` once fixed, and use them to fill the `scam_type` column.
- ABCD is a large customer-service corpus — check its size before download (rule 8).
- Robocall dataset: use `metadata.csv` → `transcript` only; skip audio. Keep English rows; tag others.
- Robocall, Aston and Anatomy are **scam-only** — never evaluate false positives on them alone;
  pair them with held-out ABCD legitimate calls.
- Aston is text messages, not calls — tag it so results can be reported with and without it.
- Anatomy of a Scam Call: data not yet available (requested from authors). Leave the loader as a stub.
- Record each dataset's licence in `README.md`.

### Optional extra sources (v1 list, Kaggle CLI)
| Folder | Dataset | Labels |
|---|---|---|
| `kaggle_scam_nonscam` | Scam and Non-Scam Call Conversation Dataset (teeconnie) | `scam.txt` = 1, `non_scam.txt` = 0 (~400 each) |
| `youtube_scam` | YouTube Scam Phone Call Transcripts (rivalcults) | all scam = 1 (~243) |
| `call_transcripts` | Call Transcripts Scam Determinations (mealss) | `IS_SCAM_VERDICT` 1/0 (~60) |

Kaggle needs `~/.kaggle/kaggle.json` (present on this machine).

---

## Common format → `data/processed/merged.csv`
| Column | Type | Meaning |
|---|---|---|
| `id` | str | `<source>_<index>` e.g. `bothbosu_00123` |
| `text` | str | cleaned transcript |
| `label` | int | 1 = spam/scam, 0 = legitimate |
| `source` | str | dataset folder name |
| `scam_type` | str | fraud code (F0–F9) or bank, irs, tech_support, grandparent, prize, etc., or `unknown` |
| `is_synthetic` | bool | AI-generated or acted |
| `region` | str | us, uk, india, unknown |
| `n_words` | int | word count after cleaning |

## Cleaning (in `src/clean.py`, in this order)
1. Lowercase; remove punctuation; collapse whitespace.
2. Remove or standardize speaker tags (`caller:`, `receiver:`, `agent:`, `customer:` etc.).
3. Remove URLs and video IDs.
4. Mask names → `[NAME]` (simple name list / spaCy NER) and digits → `[NUMBER]`.
5. Drop empty or very short texts (< 10 words).
5b. Chunk long texts into equal pieces of ≤ 300 words; keep at most 3 per conversation
    (first, middle, last). Pieces share the parent's `group_id` so splits keep them together.
6. Remove exact duplicates, then near-duplicates (> 0.95 cosine on embeddings, or MinHash).

(Implementation note: name masking runs before lowercasing because it uses capitalisation.)
7. Print a summary per source: rows, label counts, mean/median `n_words`.
   Warn if mean length differs > 2× between sources.

Label definition (v1): any unwanted/scam/robocall = 1, legitimate = 0.

---

## Splits (in `src/split.py`)
- **Per-source split fractions** follow the dataset table above (synthetic = train only).
- **Test A — random:** stratified train/val/test using those fractions (70/15/15 for ABCD,
  60/20/20 for real scam sources).
- **Test B — leave-one-source-out:** for each source, train on the others, test on it.
  When the held-out source is scam-only, also attach a held-out set of legitimate calls
  so false positives can be measured.
- **Test C — early decision:** copy of each test set truncated to the first 50 words.
- Save splits to `data/processed/splits/` as CSVs with the `id` column only + label.

## Models (in `src/models.py`) — all share one interface: `fit(X, y)`, `predict_proba(X)`
| # | Model | Notes |
|---|---|---|
| 0 | Keyword rules | List of scam phrases (gift card, verification code, safe account, arrest, don't hang up, wire, bitcoin, remote access, ...). Score = weighted count. |
| 1 | TF-IDF + LogisticRegression | word 1–2 grams, `class_weight="balanced"` |
| 2 | Sentence embeddings + LogisticRegression | `sentence-transformers/all-MiniLM-L6-v2` |
| 3 | Fine-tuned DeBERTa-v3-small | **Optional**, behind `--use-transformer`; intended for Colab GPU |
| 4 | Zero-shot LLM | **Optional**, behind `--use-llm`; ask user before running (API cost). Same prompt for every call; return label + one-line reason. |

## Evaluation (in `src/evaluate.py`)
Report for every model × test (A, B per source, C):
- False positive rate, recall, precision, F1, ROC-AUC, confusion matrix.
- **Threshold:** choose on validation so FPR ≤ 2%; report recall at that threshold.
- Breakdown per `source` and per `scam_type`.
- Save to `results/metrics.csv` and a readable `results/summary.md`.

## Analysis (in `src/analyze.py`)
1. Top 30 TF-IDF features per class → `results/top_words.txt`.
   Flag suspicious features (speaker tags, names, formatting tokens).
2. 20 false positives and 20 false negatives → `results/errors_fp.csv`, `results/errors_fn.csv`.
3. Test A vs Test B gap per model.
4. Label-shuffle sanity check: retrain with shuffled labels; accuracy must be ≈ 50%.

---

## Project layout
```
scam-classifier/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── data/
│   ├── raw/          # never edit (git-ignored)
│   └── processed/    # git-ignored
├── src/
│   ├── load_data.py
│   ├── clean.py
│   ├── split.py
│   ├── models.py
│   ├── evaluate.py
│   ├── analyze.py
│   └── run_experiment.py   # runs everything end to end
└── results/
```

## Commands
```bash
pip install -r requirements.txt
python src/load_data.py          # inspect + load raw → data/processed/raw_merged.csv
python src/clean.py              # → data/processed/merged.csv + summary
python src/split.py              # → data/processed/splits/
python src/run_experiment.py     # baseline models + evaluation + analysis
python src/run_experiment.py --use-transformer --use-llm   # optional models
```

---

## Order of work
1. Set up project, `requirements.txt`, folders. ✅
2. Download datasets; **inspect each and show the user the columns before writing loaders.**
3. Loaders → merge → clean → print summary. Stop and show the summary.
4. Splits A, B, C.
5. Models 0 and 1 → evaluate → show first results.
6. Model 2 → evaluate.
7. Analysis + sanity checks.
8. Fill the results table in `README.md`.
9. Only then, if asked: models 3 and 4.

**Pause and report to the user after steps 2, 3 and 5** before continuing.

## How to interpret results
| Result | Meaning | Next step |
|---|---|---|
| High on A and B, FPR ≤ 2% | Generalizes | Use as one signal in Gatekeeper |
| High on A, much lower on B | Learned dataset style | More cleaning / diverse data |
| Many FPs on bank/payment calls | Needs hard negatives | Generate realistic legit financial calls |
| Zero-shot LLM ≈ trained models | Training adds little | Use LLM + rules |
| Keyword rules ≈ ML | Data too easy/synthetic | Find harder test data |
