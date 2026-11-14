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
| 1 | `abcd` | [ABCD](https://github.com/asappresearch/abcd) | Real, genuine (F0) | 70/15/15 | MIT | downloaded |
| 2 | `robocall` | [Robocall Audio Dataset](https://github.com/wspr-ncsu/robocall-audio-dataset) | Real, scam | 60/20/20 | Data: public domain (FTC); docs: CC BY-ND | downloaded |
| 3 | `bothbosu` | [BothBosu scam-dialogue](https://huggingface.co/datasets/BothBosu/scam-dialogue) | Synthetic | 100/0/0 | Apache-2.0 | downloaded |
| 4 | `usenix_romance` | [USENIX romance-baiting artifact](https://secartifacts.github.io/usenixsec2026/appendix-files/sec26cycle1ae-final154.pdf) | Synthetic | 100/0/0 | CC-BY-4.0 (Zenodo 10.5281/zenodo.18770783) | downloaded |
| 5 | `aston_romance` | [Aston Romance Fraud Messages](https://fold.aston.ac.uk/handle/123456789/38) | Real, romance | 60/20/20 | TBD | link needs a browser — pending |
| 6 | `anatomy_scam` | [Anatomy of a Scam Call](https://tldr.takara.ai/p/2608.24127) | Real, scam | 60/20/20 | TBD | requested from authors |
| 7 | `synthetic_own` | Own synthetic conversations | Synthetic | 100/0/0 | own | to generate |

### Fraud-type codes
| Code | Meaning |
|---|---|
| F0 | Not fraud |
| F1 | Financial impersonation |
| F2 | Account takeover |
| F3 | Government impersonation |
| F4 | Tech support / business impersonation |
| F5 | Romance / catfishing |
| F6 | Pig-butchering / investment |
| F7 | Honeytrap / sextortion |
| F8 | Family emergency / voice clone |
| F9 | Prize / job / advance-fee |

**Task:** transcript → fraud type (F0–F9). Baseline TF-IDF + LR; main model fine-tuned DeBERTa.
**Targets:** macro F1 ≥ 0.85 on the real test set, FPR on F0 < 2%, retrain any type with F1 < 0.70.

## Run
```bash
python src/inspect_raw.py      # look at raw data (read-only)
python src/load_data.py        # -> data/processed/raw_merged.csv
python src/clean.py            # -> data/processed/merged.csv + results/data_summary.md
python src/split.py            # -> data/processed/splits/ + results/split_summary.md
python src/run_experiment.py   # -> results/metrics*.csv + results/summary.md
python src/analyze.py          # -> results/analysis.md, top_words.txt, errors_fp/fn.csv
```
Embeddings need `torch` (CPU is fine: `pip install torch --index-url https://download.pytorch.org/whl/cpu`).

## Results v2 — phone calls only (2026-11-14)
Data: 7 phone-call sources (no chats). Only 2 real genuine calls exist, so (Option 1, agreed with
the user) models are **trained on synthetic calls only**, thresholds are set on synthetic validation
(FPR ≤ 2%), and tested on:
- **Test A** — held-out synthetic calls from the same sources (in-distribution).
- **Test B** — sources never seen in training: average over BothBosu, Kaggle scam/non-scam,
  call_transcripts and team synthetic (FPR + F1), plus **B_real** = all 819 real calls
  (Robocall + YouTube; recall only — 2 genuine calls are too few for FPR).
- **Test C** — Test A recall using only the first 50 words.

| Model | Test A F1 | Test B F1 (avg) | FPR (A) | FPR (B avg) | Real-scam recall (B_real) | Early-decision recall (C) | Fraud-type macro F1 (A) |
|---|---|---|---|---|---|---|---|
| Keyword rules | 0.715 | 0.490 | 1.9% | **1.3%** | 22.2% | 28.7% | 0.37 |
| TF-IDF + LR | 0.993 | 0.738 | 3.0% | 75.0% | 96.5% | 98.8% | 0.98 |
| Embeddings + LR | 0.985 | 0.746 | 2.7% | 20.1% | 58.8% | 84.6% | 0.97 |
| DeBERTa-v3-small (fine-tuned)† | 0.996 | 0.717 | 1.5% | 72.7% | 92.2% | 91.3% | 0.98 |
| Zero-shot LLM (qwen2.5:3b)* | 0.409 | 0.362 | 1.5% | 0.0% | 16.6% | 10.0% | 0.25 |

† DeBERTa: `microsoft/deberta-v3-small`, 3 epochs, class-weighted, trained on Colab T4 on every split (full test sets). Same pattern as TF-IDF: near-perfect on Test A, but on unseen sources it flags 29–97% of genuine calls (AUC 0.79–0.90). Full table: [results/summary_deberta.md](results/summary_deberta.md).

\* Zero-shot LLM: Ollama `qwen2.5:3b`, no training, run on Colab T4 on a random sample of 200 calls per test set (60 for early decision); threshold from a shared 200-call validation sample. Using its own judgement (scam probability ≥ 50) it catches 99–100% of scams but flags 32–100% of genuine calls (all of the team's genuine bank calls); its scores take only 8 distinct values, so holding FPR ≤ 2% pushes the threshold to 0.85 and recall drops to 14–28%. Full table: [results/summary_llm.md](results/summary_llm.md).

### Verdict: still "high on A, much lower on B" — no model generalises yet
- On unseen sources, **TF-IDF flags 75% of genuine calls** (it calls almost everything a scam, which is
  also why its real-scam recall is high). Embeddings: 20% false alarms, 59% of real scams caught.
- **Keyword rules are the only model under 2% FPR on unseen sources**, but they catch only 22% of real scams.
- Hardest unseen source: the team synthetic calls (AUC 0.66–0.72) — realistic genuine bank calls
  and fraud types (F2, F6, F7) that no other source contains.
- Remaining shortcut words in the top TF-IDF features: greetings ("hi", "thanks", "this is"),
  `[NAME]` placeholder n-grams, an unmasked name ("john") and BothBosu's placeholder company "xyz".
  See [results/top_words.txt](results/top_words.txt).
- Label-shuffle check passes (AUC 0.52 ± 0.08); no train/test text overlap.

<details><summary>v1 results (with ABCD chats — invalid, kept for reference)</summary>

### v1 (2026-11-14)
Binary scam-vs-genuine F1; threshold chosen on validation for FPR ≤ 2%. Test A = main split
(real test data, 6.6% scams). Test B = average of "ABCD held out" and "Robocall held out".
Early-decision = Test A recall using only the first 50 words. Full details:
[results/summary.md](results/summary.md), [results/analysis.md](results/analysis.md).

| Model | Test A F1 | Test B F1 (avg) | FPR (A) | FPR (B avg) | Recall @ 2% FPR (A) | Early-decision recall | Fraud-type macro F1 (A) |
|---|---|---|---|---|---|---|---|
| Keyword rules | 0.000 | 0.044 | 2.1% | 7.6% | 0.000 | 0.221 | 0.19 |
| TF-IDF + LR | 0.878 | 0.496 | 2.0% | 46.7% | 1.000 | 1.000 | 0.83 |
| Embeddings + LR | 0.860 | 0.435 | 2.3% | 12.4% | 1.000 | 1.000 | 0.68 |
| DeBERTa (opt.) | — | — | — | — | — | — | — |
| Zero-shot LLM (opt.) | — | — | — | — | — | — | — |

### Verdict: high on A, much lower on B → the models learned dataset style, not scam language
- Test A looks near-perfect (AUC 1.000) because every real genuine example is a typed ABCD chat and
  every real scam is a recorded robocall. Top TF-IDF features for "genuine" are chat phrases
  ("help you", "order id", "anything else"); for "scam" they are call phrases ("press [NUMBER]", "uh").
- When ABCD is held out, TF-IDF flags **93%** of genuine chats as scams (embeddings: 25%).
- Keyword rules fail because ABCD's shopping chats are full of words like "refund", "order", "password".
- Label-shuffle check passes (AUC 0.56 ± 0.07, no train/test text overlap) — the pipeline does not leak.
- Only 104 real scam calls are in the test set (F1 10, F3 49, F4 40, F9 5); F2, F5–F8 have no real
  test data, so their scores can't be measured yet.

**Next step:** add real *genuine phone-call* transcripts (ideally bank / payment calls) and the
Anatomy of a Scam Call corpus, then re-run `python src/run_experiment.py && python src/analyze.py`.

</details>
