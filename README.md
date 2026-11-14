# Scam Call Classifier

An experiment testing whether a text classifier can tell **scam/spam phone call transcripts**
(label 1) from **legitimate calls** (label 0) — and whether it still works on data from a
source it has never seen. It is meant to become one signal inside **Gatekeeper**, an AI agent
that screens phone calls for financial fraud.

**Key metric:** false positive rate ≤ 2% (legitimate calls flagged as scam).

See [CLAUDE.md](CLAUDE.md) for the full experiment plan and rules.

## Setup
```bash
python -m venv .venv
.venv\Scripts\activate        # Windows  (source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
```

Raw data is **not** committed. Download each dataset into `data/raw/<folder>/` (see below).

## Datasets
| # | Folder | Dataset | Type | Split (train/val/test) | Licence | Status |
|---|---|---|---|---|---|---|
| 1 | `abcd` | [ABCD](https://github.com/asappresearch/abcd) | Real, genuine (F0) | 70/15/15 | TBD | not downloaded |
| 2 | `robocall` | [Robocall Audio Dataset](https://github.com/wspr-ncsu/robocall-audio-dataset) | Real, scam | 60/20/20 | TBD | not downloaded |
| 3 | `bothbosu` | [BothBosu scam-dialogue](https://huggingface.co/datasets/BothBosu/scam-dialogue) | Synthetic | 100/0/0 | TBD | not downloaded |
| 4 | `usenix_romance` | [USENIX romance-baiting artifact](https://secartifacts.github.io/usenixsec2026/appendix-files/sec26cycle1ae-final154.pdf) | Synthetic | 100/0/0 | TBD | not downloaded |
| 5 | `aston_romance` | [Aston Romance Fraud Messages](https://fold.aston.ac.uk/handle/123456789/38) | Real, romance | 60/20/20 | TBD | not downloaded |
| 6 | `anatomy_scam` | [Anatomy of a Scam Call](https://tldr.takara.ai/p/2608.24127) | Real, scam | 60/20/20 | TBD | requested from authors |
| 7 | `synthetic_own` | Own synthetic conversations | Synthetic | 100/0/0 | own | to generate |

### Fraud-type codes
| Code | Meaning |
|---|---|
| F0 | Genuine / legitimate |
| F1–F9 | TBD |

## Run
```bash
python src/load_data.py
python src/clean.py
python src/split.py
python src/run_experiment.py
```

## Results
| Model | Test A F1 | Test B F1 (avg) | FPR | Recall @ 2% FPR | Early-decision recall |
|---|---|---|---|---|---|
| Keyword rules | | | | | |
| TF-IDF + LR | | | | | |
| Embeddings + LR | | | | | |
| DeBERTa (opt.) | | | | | |
| Zero-shot LLM (opt.) | | | | | |
