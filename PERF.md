# PERF.md — performance review and improvement plan

_Reviewed 2026-11-14. Scope: (1) model quality — the thing the project is actually judged on,
(2) service latency/throughput, (3) research-pipeline wall-clock. The code items were implemented the
same day (see [§0.1](#01-what-is-implemented)); the data items stay open because they need real calls._

**How this was produced:** read `src/`, `tests/`, `deploy/`, `config/scoring.yaml` and everything in
`results/`, then microbenchmarked the non-LLM hot paths on this machine (macOS, CPU, `.venv`,
`SEED=42`). Ollama was not running, so LLM timings are the documented ~14 s/request from
`SERVICE.md`, not a fresh measurement. Absolute microbenchmark numbers are noisy (embedding cache
state changes them by >5×); the ratios and the ranking are the point. Raw numbers are in
[Appendix](#appendix--raw-measurements).

---

## 0. Verdict

The code is functional and tested (18 tests pass in 6.15 s), and the service design is sound:
rules + classifier + LLM, with verbatim evidence and a graceful LLM fallback. The performance
problem is **not** algorithmic inefficiency in the Python. It is:

1. **The headline metric cannot be measured yet.** There are **2 real genuine calls** in the whole
   corpus (`results/data_summary.md`). Every FPR number on real calls is therefore "0/2" and
   meaningless, while Test A (synthetic → synthetic) is ~0.99 F1 and tells us almost nothing.
2. **Unseen-source FPR is 20–100% for every trained model.** TF-IDF flags 96.8% of genuine BothBosu
   calls and 100% of genuine Kaggle calls; DeBERTa 72.8% / 96.5% (`results/summary.md`,
   `results/summary_deberta.md`). Target is ≤ 2%.
3. **One fraud type is missing from the data entirely.** F5 (romance) has **0 rows**; the spec
   requires ≥ 300 training examples per type and a retrain when any type F1 < 0.70.
4. **The service can spend 3.5 s on non-LLM work before it even starts the LLM** at the
   20,000-character input cap — measured below — because of three redundant per-chunk loops.
5. **The deployed LLM timeout (100 s) is 3× the caller's 30 s budget**, so slow requests are
   guaranteed to be wasted work and to fail downstream (`deploy/azure/docker-compose.yml`,
   `deploy/azure/native/scam-service.service.template`).

| # | Improvement | Area | Expected impact | Effort |
|---|---|---|---|---|
| P0-1 | Collect real genuine phone calls (≥ 200) | Data | Unblocks the key metric; the single largest gain | Large (external) |
| P0-2 | Fill F5 and real F1/F2/F6/F7/F8 coverage | Data | Makes macro F1 and the retrain rule meaningful | Medium |
| P0-3 | Threshold + FPR reporting discipline | Evaluation | Stops over-claiming; reduces test FPR drift | Small |
| P0-4 | Remove style/source shortcuts (names, greetings, length) | Model | Directly lowers unseen-source FPR | Medium |
| P0-5 | Negation-aware F01 ("we never ask for your PIN") | Rules | 17% → ~0% F01 false alarms on genuine bank calls | Small |
| P0-6 | Speaker-role handling for API text | Rules/model | Stops the victim's own words triggering flags | Small–Medium |
| P1-1 | Fix LLM timeout mismatch (100 s → ~25 s) | Service | Eliminates ~75 s of wasted work per slow request | Trivial |
| P1-2 | Bound concurrency / add queue feedback | Service | Prevents latency collapse under load | Small |
| P1-3 | Batch F17 + incremental classifier scoring | Service | ~3.5 s → <0.5 s non-LLM at max text length | Small |
| P1-4 | Pool the LLM HTTP connection | Service | 5–30 ms saved per request; cleaner failure modes | Trivial |
| P1-5 | Bound the in-process embedding cache | Service | Stops unbounded memory growth per caller | Small |
| P2-1 | Length-sorted DeBERTa batches + early stopping + head/tail truncation | Research | Faster Colab runs; fewer truncated scam endings | Small–Medium |
| P2-2 | Cache/reuse experiment fits; pin research deps | Research | Repeat runs and results become comparable | Small |

### 0.1 What is implemented

| Item | Change |
|---|---|
| P0-2 (reporting half) | `evaluate.type_metrics` scores the fixed F0–F9 set: a type absent from a test set scores 0 (support 0) instead of disappearing from the macro average |
| P0-3 | threshold chosen at 1.5% FPR (margin inside the 2% target); FPR and recall reported with 95% Wilson intervals; FPR is `NA` when a test set has fewer than 100 genuine calls, and `n_negatives` is a column in `results/metrics.csv` |
| P0-5 | F01 requires an un-negated request verb near the match: "we will never ask you for your PIN" and "we sent you a code" no longer fire, while "read me the code" and "do not tell anyone, now read me the code" do. Tests in `tests/test_call_analysis.py` |
| P1-1 | deploy timeout 100 s → 25 s (compose + systemd); `/v1/status` exposes `llm_timeout_seconds` |
| P1-3 | F17 encodes every caller segment of the call in one batch and one matrix multiply; the classifier is scored once on the full transcript for the decision and on at most 12 timeline windows (was one cumulative encode per window) |
| P1-4 | `CallLLM` reuses one keep-alive HTTP(S) connection per thread instead of opening a socket per request |
| P1-5 | service mode (`persist=False`) bypasses the embedding cache entirely, so caller text never accumulates in memory |
| P2-2 | TF-IDF / embedding / keyword fits are cached by (model, hyper-parameters, training ids, labels) in `data/processed/fit_cache/`; `FIT_CACHE=0` bypasses the cache |

Still open: P0-1, P0-2 (data), P0-4, P0-6, P0-7, P1-2, P1-6, P1-7, P2-1, P2-3 (deps pinning).

---

## 1. Where the time goes

### 1.1 Service request (typical call, ~80 words, 2–3 chunks)

Documented end-to-end: **~14 s** on a laptop with a warm 7B model; startup ~25 s
(`SERVICE.md`, `README.md`). The LLM call is >95% of that. Measured non-LLM components:

| Stage | Code | Measured |
|---|---|---|
| Chunking | `chunk_call` | 0.02 ms/call |
| Red-flag rules | `rule_flags_in_chunk` | ~1.0 ms/chunk (cold) |
| F17 script match | `ScriptMatcher.in_chunk` | ~23–35 ms/chunk cold; 0.01 ms/chunk when the text is already in the embedding cache |
| Classifier (full call) | `CallClassifier.fraud_score` | 0.3 ms (392 words), 2.8 ms (1,765 words) |
| Classifier (per-chunk prefix loop) | `ScamService.analyze` | 14 ms for a 3-chunk, 1,765-word call |

For a normal call the non-LLM path is ~30 ms — irrelevant next to 14 s. **Do not optimise it for
normal calls.** It matters only at the input cap and under concurrency.

### 1.2 Service request at the 20,000-character cap (96 chunks)

| Stage | Measured |
|---|---|
| Rules, whole call | 110 ms |
| F17, whole call (cold cache, one encode per segment) | **2,235 ms** |
| Cumulative classifier loop (one encode per chunk) | **1,127 ms** |
| Classifier once on the full text | 2.6 ms |
| **Total before the LLM call** | **~3.5 s** |

Three separate O(n²) patterns cause this:

- `pipeline.ScamService.analyze` rebuilds `so_far` by joining every segment for every chunk and
  re-encodes it (`clf = self.classifier.fraud_score(so_far)`). 96 encodings where 1 would do.
- `ScriptMatcher.in_chunk` encodes each caller segment separately
  (`src/call_analysis/flags.py`, `ScriptMatcher.in_chunk`), so a 96-chunk call makes ~96
  single-item `SentenceTransformer.encode` calls at ~20 ms each instead of one batch.
- The timeline is computed before the LLM call, so this 3.5 s is added to the caller's deadline
  rather than being display-only work.

### 1.3 Experiment pipeline

`run_experiment.py` fits every model once per test split — 6 splits (`A`, `B_real`, `B_bothbosu`,
`B_call_transcripts`, `B_kaggle_scam_nonscam`, `B_synthetic_own`), so 6 TF-IDF fits, 6 embedding
fits and **6 full DeBERTa trainings per run**. `analyze.py` adds 6 more TF-IDF fits plus 5
label-shuffle refits. The embeddings are cached on disk (`models.SentenceEncoder`), so only the
first run pays the encoding cost; DeBERTa pays the full cost every time. That is the dominant
research wall-clock.

---

## 2. P0 — model quality (this is the real performance work)

### P0-1. Real genuine calls are the blocking gap

**Evidence:** `results/data_summary.md` shows F0 = 1,841 rows, of which **2 are real** (both are
15-word FTC illegal-robocall clips labelled genuine by a keyword rule). `results/summary.md`
reports `B_real` FPR = 0.000 for all three models — computed from those 2 negatives. The README's
own verdict says no model generalises, and every published FPR on real calls is unmeasurable.

**Why it matters more than any code change:** the project's key metric is FPR ≤ 2% on real calls.
With n = 2 the 95% Wilson interval for 0 false positives is ~[0%, 84%]. No amount of modelling,
thresholding or calibration fixes that. This is also why every model looks great on Test A and bad
on B: Test A is synthetic → synthetic.

**Do:**
- Treat real genuine data as the next milestone, not a nice-to-have. Target ≥ 200 real genuine
  calls (bank/payment/service calls are the hard negatives that matter), ideally ≥ 500.
- Until then, report `FPR = NA` whenever the negative count is < 100, and never quote "FPR 0%" on
  `B_real`. `evaluate.binary_metrics` currently computes `fp/(fp+tn)` regardless; make that
  `np.nan` below a threshold and surface the count next to the metric.
- Prefer a smaller, well-labelled real set over more synthetic rows: synthetic share is already
  far above the spec's ≤30% of train (Option 1 is 100% synthetic by design).

**Verify:** rerun `split.py` + `run_experiment.py`; `B_real` must have ≥ 100 F0 rows and a
confidence interval on FPR. Success criterion: FPR ≤ 2% with a Wilson upper bound ≤ 3%.

### P0-2. Fill F5 and the real per-type gaps

**Evidence:** `results/data_summary.md` source × type table has **no F5 column at all** — zero
rows. Real rows per type are F1 = 65, F3 = 295, F4 = 433, F8 = 2, F9 = 22, F2/F6/F7 = 0. The spec
requires ≥ 300 training examples per type, and "any fraud type F1 < 0.70 → add data and retrain".
F5, F2, F6 and F7 cannot even be scored honestly (`evaluate.type_metrics` silently averages only
the types present in the test set, which hides the missing ones).

**Do:**
- Land the Aston romance loader (F5, real, currently "link needs a browser") and the
  `anatomy_scam` stub as soon as the authors respond.
- Generate F5/F2/F7 training-only synthetic rows in `synthetic_own` (already the source for F2, F6,
  F7, F8), respecting the 30% synthetic cap on the final mix.
- Change `evaluate.type_metrics` to score a **fixed 10-label set** (F0–F9) so absent types show
  F1 = 0 and support = 0 instead of disappearing. This changes no model, only honesty of the
  reported macro F1; current `macro_f1_types` on Test A (0.98) is over 8–9 present types.

**Verify:** `results/split_summary.md` shows every fraud type with train support ≥ 300 and test
support > 0 from at least one source; macro F1 cannot be reported without F5 support.

### P0-3. Threshold and FPR reporting are too loose

**Evidence:** the threshold is chosen on validation for FPR ≤ 2% (`evaluate.choose_threshold`),
yet Test A FPR is **3.0%** for TF-IDF, and unseen-source FPR reaches 96.8% (TF-IDF, BothBosu),
100% (Kaggle), 72.8% (DeBERTa, BothBosu). The threshold is a single global number picked on a
validation distribution whose negatives look nothing like the production negatives.

Three concrete problems:
1. **No margin.** `k = floor(0.02 * n_neg)` allows exactly 2% FPs on validation; sampling noise
   on test pushes it over the target. Choose at 1–1.5% on validation.
2. **No uncertainty.** A single point estimate hides that the 2% is estimated from a few hundred
   negatives. Report Wilson intervals, and bootstrap the threshold selection.
3. **Calibration mismatch.** The score is `1 − P(F0)` from a model trained on a 71% scam
   synthetic mix, applied to a real test set that is 99.8% scam or mostly genuine depending on the
   split. Pick the threshold on a validation set whose **class prior and source mix match the
   deployment target** (mostly genuine), not on the training mix.

**Do:** choose the threshold on cross-fitted out-of-fold validation scores at 1.5% FPR; report
FPR/recall with 95% CIs; keep `predict_types` but only trust it above the threshold; add a
`n_negatives` column to `results/metrics.csv` and mark FPR `NA` when it is small.

**Verify:** `results/summary.md` includes CIs; Test A FPR stays ≤ 2% on the same run; no test split
reports an FPR from fewer than 100 negatives.

### P0-4. Remove the remaining style/source shortcuts

**Evidence:** `results/top_words.txt` still lists an unmasked name **"john"**, BothBosu's
placeholder company **"xyz"**, greetings ("this is", "hi", "thanks"), `[NAME]` n-grams and
`[NUMBER]`-style formatting as top features. `results/shortcut_check.md` warns that median length
differs **2.1×** between labels (genuine 72 vs scam 151 words), source means differ 45 vs 249
words, and `usenix_romance` is 100% scam and 18% of all rows. `check_shortcuts.py` correctly
detects this, but nothing consumes its warnings.

**Do (cheapest first):**
- Extend `clean.NOT_NAMES`/placeholder masking to company placeholders (`xyz`, `abc company`,
  and any token repeated as a template slot). Mask or strip call-opening greetings in **all**
  sources identically (rule 6), not just some.
- Length-normalise: train on a fixed word budget (e.g. first 150 words + last 50) and/or add
  `n_words`-stratified sampling so length cannot separate the classes. Test C already measures the
  first-50-words case; use it as the primary early-decision metric.
- Run an **adversarial validation**: train a classifier to predict `source` from text. Any feature
  that predicts source strongly is a shortcut candidate; drop or mask the top ones and re-check
  Test B.
- Keep `usenix_romance` train-only (it already is), but down-weight it so 18% of the corpus is not
  one writing style.

**Verify:** `results/top_words.txt` has no name/company/greeting tokens in the top 30 for any
class; the source-classifier AUC falls toward chance; `B_*` FPR improves without Test A F1
dropping more than ~0.01.

### P0-5. Negation-aware F01 (currently the top source of service false alarms)

**Evidence:** `results/call_analysis/rule_validation.md`: **17% of genuine synthetic bank calls
trigger the critical flag F01**, from two patterns — "we will **never** ask you for your PIN"
(a reassurance) and "I'll **send** a code to your number" (not a request to read it back). A
critical flag is 40 points, so this alone can push a genuine call to Medium. The same file shows
29% of genuine BothBosu calls get a high/critical flag.

**Do:** in `flags.find_phrase`/`rule_flags_in_chunk`, add a negation/claim window:
- suppress F01 when the match is preceded within ~4 words by "never", "not", "won't", "we do not",
  "don't", "no one will";
- distinguish *sending* a code from *asking for* one: require a request verb ("read", "tell",
  "give", "confirm", "provide") near "code" for F01, and do not fire on "we sent you a code";
- add a unit test per wording to `tests/test_call_analysis.py` (there is already a
  `test_read_me_the_code_triggers_f01`).

This is a rule change, so per the project's own rule it must be checked on held-out calls with
`validate_rules.py` before it is accepted.

**Verify:** `validate_rules.py` genuine-bank F01 rate 17% → ~0–2%, while the OTP-scam F01 rate stays
≥ 78%; demo ranking unchanged.

### P0-6. Speaker roles are unknown in the API path

**Evidence:** `pipeline.analyze` notes "Speaker roles are unknown for API text, so flags are checked
on every line", and `flags.rule_flags_in_chunk` skips only segments whose speaker is exactly
`"You"`. For API text every line is `None`, so the victim saying "I'll never give you my PIN" can
trigger F01. This is the same class of error as P0-5 but structural.

**Do:** accept optional speaker turns in the request (`text` stays the contract, add
`turns: [{speaker, text}]`), or infer the caller side from who makes requests (harder). At minimum,
down-weight a flag whose quote is a first-person refusal ("I won't give you…") and add an explicit
`quote_side: unknown` field so consumers know the evidence is side-ambiguous.

**Verify:** a genuine victim refusal no longer fires F01; the transcription-API contract test still
passes (`tests/test_service.py::test_response_matches_transcription_api_contract`).

### P0-7. Model experiments worth running (in this order)

These are model-quality changes, not refactors. Each is cheap to test with the existing harness.

1. **Char n-grams in TF-IDF** (`analyzer="char_wb", ngram_range=(3,5)`) alongside word 1–2 grams.
   ASR errors are the production distribution; the rules already do fuzzy matching, the model does
   not. Expected: better B_real recall at a fixed FPR.
2. **Hard-negative mining.** The 20 FPs in `results/errors_fp.csv` are the cheapest training data
   you have. Add them (and their sources) to training as F0, subject to the group-split rule, and
   re-measure. This directly targets the "flags most genuine calls" failure.
3. **Two-stage decision:** calibrated binary F0-vs-fraud head for the threshold, separate type head
   for F1–F9. `predict_types` currently takes the argmax over fraud types and then discards it below
   threshold; a dedicated binary head usually calibrates better at low FPR.
4. **DeBERTa:** max_len 256 truncates many calls (mean 249 words for usenix, 200 for
   call_transcripts; wordpieces are ~1.3× words). Use head+tail truncation (first 128 + last 128
   tokens) so the closing payment request is not cut, or max_len 384. Add early stopping on
   validation macro F1 instead of fixed 3 epochs.
5. **Domain-adversarial / source-balanced batches** only if P0-4's adversarial validation shows
   source is still predictable after masking. Do not add complexity before measuring.

---

## 3. P1 — service latency, throughput and memory

### P1-1. Timeout mismatch wastes 70% of the work on slow calls

`deploy/azure/docker-compose.yml` and the systemd unit set `SCAM_LLM_TIMEOUT_SECONDS=100`; the
transcription API waits **30 s** (`SERVICE.md`, `CLAUDE.md`). A request that takes 35 s is a
guaranteed downstream failure, but this service keeps generating for another 65 s. The LLM lock
also means later requests queue behind it.

**Do:** set the timeout to 20–25 s in both deploy paths and in the code default (currently 20 s,
which is already right), and make the fallback path the norm at the deadline. Add the LLM timeout
value to `/v1/status` so the caller can assert it is inside its own budget.

**Verify:** `deploy/azure/smoke_test.py` prints latency; force an LLM timeout and confirm the
response is a valid fallback in < 25 s.

### P1-2. Concurrency is serialised but the queue is unbounded

`ScamService._ask_llm` takes a global `threading.Lock`, and the FastAPI endpoints are sync `def`,
so uvicorn's threadpool accepts many requests that all wait for one LLM slot. At ~14 s per call,
one slot serves ~4.3 requests/min. Two concurrent callers are fine; ten become timeouts with no
signal to the caller.

**Do:** add a bounded semaphore (e.g. 2 waiting) and return 503 + `Retry-After` when full, or
expose `X-Queue-Position`/`estimated_wait_s`. If you raise `OLLAMA_NUM_PARALLEL`, measure p50/p95
first: on CPU, parallelism trades single-request latency for throughput.

**Verify:** a 10-concurrent-request load test (proposed `deploy/azure/bench.py`, 20 calls) reports
p50/p95 and zero 30 s violations; `SCAM_LLM_TIMEOUT_SECONDS` bounds every response.

### P1-3. Batch F17 and stop re-scoring the classifier for every chunk

Measured at the 20k-char cap: F17 2.2 s + cumulative classifier 1.1 s + rules 0.1 s ≈ 3.5 s. Fix:

- `ScriptMatcher.in_chunk` → collect caller segments for the **whole call**, encode once with
  `SentenceEncoder.encode(list)`, then one matrix multiply (`vecs @ library.T`) and assign each hit
  back to its chunk. Single-item `encode` is the expensive part: measured **33.5 ms/segment** one
  at a time vs **1.38 ms/segment** batched (24× cheaper) on a cold cache.
- `ScamService.analyze` → score the classifier once on the full cleaned transcript (needed for the
  final score), and compute the timeline from every 3rd window or from cached segment embeddings.
  The timeline is display data; the decision does not need 96 decimal-place updates.
- Cache `clean_text` per segment if the same text is scored repeatedly.

**Expected:** ~3.5 s → <0.5 s at the cap; no change for normal calls, where the cost is already
~30 ms.

**Verify:** rerun the appendix benchmark (96 chunks) and `python -m pytest tests -q` (18 tests);
reports/timeline fields must be byte-identical for the 10 demo calls.

### P1-4. Reuse the LLM HTTP connection

`CallLLM._call_once` uses `urllib.request.urlopen` for every request, which opens a new TCP
connection (and TLS if hosted). Use one `httpx.Client`/`requests.Session` per process with
keep-alive. Saves 5–30 ms locally, more against a remote provider, and gives one place for
timeouts/retries instead of `urllib.error` handling.

**Verify:** `/v1/status` latency and smoke test show no regression; one client instance per service.

### P1-5. The service embedding cache is unbounded

`pipeline.ScamService.__init__` sets `get_encoder().persist = False`, which prevents disk writes but
leaves the in-memory `self.cache` growing forever: every caller's unique text (and every cumulative
prefix) adds a 384-float vector, ~1.5 KB each. A 96-chunk call adds ~96 entries; a day of traffic
adds tens of thousands. This is both a memory leak and a privacy surface.

**Do:** give `SentenceEncoder` a `max_entries`/LRU eviction, or bypass the cache entirely when
`persist=False` (the service's texts are never reused). Prefer bypass: it removes a branch and the
leak.

**Verify:** a 1,000-request soak test keeps RSS flat; no text/vector is written to disk.

### P1-6. Startup and health

`/healthz` returns ok only after `lifespan` loads the classifier and warms the LLM, which is the
right behaviour, but startup is ~25 s (or minutes on a cold model pull) and the Docker healthcheck
has `--start-period=600s`, so a bad deploy is not reported for 10 minutes. Add `/readyz` with
`{classifier: bool, llm: bool, llm_error}` and a per-stage timing field in the response
(`timings_ms`, no text) so p95 can be tracked without logs containing transcripts.

**Verify:** kill Ollama and confirm `/readyz` is 503 while `/healthz` is 200; Docker marks unhealthy
within ~2 minutes.

### P1-7. Context window vs input cap

`MAX_TEXT_CHARS = 20000` ≈ 3,200 words ≈ **4,450 prompt tokens** including the preamble and task.
The compose file sets `CALL_LLM_NUM_CTX=4096` (code default 8192). At the cap, the prompt exceeds
the context and Ollama truncates it, so the model may never see the start (identity claim) or the
end (payment request) — wasted prefill and a wrong summary.

**Do:** either cap the transcript sent to the LLM (~2,800 words with head+tail sampling) or align
`CALL_LLM_NUM_CTX` with the max input. The rules and classifier can still consume the full text.

**Verify:** a 20k-char request returns a summary that mentions the first and last minutes; token
count logged per request.

---

## 4. P2 — research pipeline throughput

### P2-1. DeBERTa training is the experiment bottleneck

Each `run_experiment.py --use-transformer` trains DeBERTa **6 times** (once per split), 3 fixed
epochs, random batch order with padding to the longest item in each batch (16), max_len 256. On a
T4 that is the bulk of the Colab time, and no validation set is used to stop.

**Do:** length-sorted batches (or a length-bucketed sampler) to cut padding; early stopping on
validation macro F1 with `load_best_model_at_end`; `max_len=384` or head+tail truncation; run only
the splits you need with `--tests` while iterating. Keep the same seed and report the epoch chosen.

**Verify:** same or better per-type F1 on Test A/B within fewer GPU-minutes; print epoch and val
macro F1.

### P2-2. Cache experiment fits and pin the research environment

- `run_experiment` refits per split because the train sets differ — that is correct, but TF-IDF and
  embedding fits can be cached by a hash of the train ids, and `analyze.py` refits the same TF-IDF
  models it could load from a cache. Embedding encoding is already cached; make the fit cache
  explicit (joblib under `data/processed/`, git-ignored).
- `pyproject.toml` declares no dependencies; `requirements.txt` is unpinned; `deploy/azure/
  requirements-service.txt` is pinned. Two environments can resolve different sklearn/numpy
  versions, which changes both speed and scores. Pin the research requirements (or generate a
  lock) so "faster" is not confounded with "different BLAS/sklearn".

**Verify:** a second `run_experiment.py` run reuses fits (log "cached") and reproduces
`results/metrics.csv` to 3 decimals.

### P2-3. Data cleaning (low priority)

`clean.drop_near_duplicates` computes MinHash over a Python 3-gram loop for 7.4k rows, and
`clean_text` runs `re.sub` once per known name per row. At the current size this is seconds, not
minutes; do not optimise it before P0/P1. If the corpus grows 10×, switch `_minhash` to a
`datasketch` shingle helper or skip near-dup for synthetic sources that are known unique.

---

## 5. Do-first sequence

1. **P0-1 / P0-2 data.** Get ≥ 200 real genuine calls and F5/Aston + F2/F6/F7 real or approved
   synthetic coverage. Nothing else moves the headline metric.
2. **P0-3 reporting.** Before the next result table is written, make FPR `NA` under 100 negatives,
   add CIs, and pick the threshold at 1.5% with matching prior. This prevents another round of
   "0% FPR" claims that are artefacts of 2 negatives.
3. **P0-5 negation rules + P0-4 masking.** Measured 17% F01 false alarms is the most concrete,
   smallest fix with a direct production effect.
4. **P1-1 timeout, P1-2 backpressure, P1-3 batching.** These are contained changes with measurable
   latency wins and no model retraining.
5. **P0-6 speaker roles**, then **P0-7 model experiments** in the listed order.

Success for this plan: `B_real` has ≥ 100 genuine rows and FPR ≤ 2% with a Wilson upper bound
≤ 3%; every fraud type has ≥ 300 training rows and a non-zero test support; service p95 < 30 s with
zero timeout violations; non-LLM work at the input cap < 0.5 s.

---

## 6. How to verify (commands)

```bash
python -m pytest tests -q                    # 18 passed in 6.15 s measured on this machine
python src/split.py && python src/run_experiment.py
python src/analyze.py                        # top words / errors / A-vs-B gap
python src/call_analysis/validate_rules.py   # required before accepting any rule change
python deploy/azure/smoke_test.py https://<domain> <token>   # latency + contract
```

For service changes, add a small load test that issues 20 sequential and 10 concurrent requests and
prints p50/p95 plus the LLM fallback rate. Keep transcripts out of logs and out of the response
timings (the privacy rule in `SERVICE.md` still applies).

---

## Appendix — raw measurements

Environment: macOS, CPU-only `.venv` (Python 3.13.7), no Ollama running. Corpus:
`synthetic_fraud_calls.csv` (2,340 calls, mean 80 words). `CallClassifier` loaded from
`src/service/artifacts/classifier.joblib` (15 KB). Values are best-of-3 where noted; embedding-cache
state is the main source of variance.

| Measurement | Value |
|---|---|
| `chunk_call`, 300 calls | 0.02 ms/call; mean 2.7 chunks/call |
| `rule_flags_in_chunk`, 30-word chunks | 1.01 ms/chunk; mean 0.38 flags/chunk |
| `SentenceEncoder.encode`, 1 segment (batch of 1, cold) | 33.5 ms/segment |
| `SentenceEncoder.encode`, 60 unique segments in one batch (cold) | 83 ms total = 1.38 ms/segment (24× faster) |
| `ScriptMatcher.in_chunk`, cold per-segment encoding | 23–35 ms/chunk (23 at 96 chunks) |
| `ScriptMatcher.in_chunk`, text already cached | 0.01 ms/chunk |
| `CallClassifier.fraud_score`, 392 words | 0.3 ms |
| `CallClassifier.fraud_score`, 1,765 words | 2.8 ms |
| Classifier loop over 12 chunk prefixes (392 words) | 2.3 ms |
| Classifier loop over 3 chunk prefixes (1,765 words) | 14.1 ms |
| 3,200-word transcript (the 20k-char cap) | 96 chunks |
| Rules over 96 chunks | 110 ms |
| F17 over 96 chunks (cold) | 2,235 ms |
| Cumulative classifier over 96 chunks | 1,127 ms |
| Classifier once over the same text | 2.6 ms |
| Prompt size at the cap (preamble + task + text) | ~3,423 words ≈ 4,450 tokens |
| Test suite | 18 passed in 6.15 s |
| Documented service latency / startup | ~14 s/request, ~25 s startup |
