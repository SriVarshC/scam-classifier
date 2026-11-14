# Zero-shot LLM results

Model `qwen2.5:3b` via Ollama, no training. Random sample of 200 calls per test set (60 for `first50`); threshold from a shared validation sample (FPR <= 2%).

| model                      | test                  | variant   |   n_test |     fpr |   recall |   precision |   f1_binary |   roc_auc |   macro_f1_types |   tn |   fp |   fn |   tp |
|:---------------------------|:----------------------|:----------|---------:|--------:|---------:|------------:|------------:|----------:|-----------------:|-----:|-----:|-----:|-----:|
| zero_shot_llm (qwen2.5:3b) | A                     | full      |      200 |   0.015 |    0.259 |       0.972 |       0.409 |     0.777 |            0.248 |   64 |    1 |  100 |   35 |
| zero_shot_llm (qwen2.5:3b) | A                     | first50   |       60 |   0     |    0.1   |       1     |       0.182 |     0.627 |            0.096 |   20 |    0 |   36 |    4 |
| zero_shot_llm (qwen2.5:3b) | B_bothbosu            | full      |      200 |   0     |    0.14  |       1     |       0.246 |     0.745 |            0.304 |   86 |    0 |   98 |   16 |
| zero_shot_llm (qwen2.5:3b) | B_bothbosu            | first50   |       60 |   0     |    0.121 |       1     |       0.216 |     0.774 |            0.296 |   27 |    0 |   29 |    4 |
| zero_shot_llm (qwen2.5:3b) | B_call_transcripts    | full      |       54 |   0     |    0.276 |       1     |       0.432 |     0.899 |            0.419 |   25 |    0 |   21 |    8 |
| zero_shot_llm (qwen2.5:3b) | B_call_transcripts    | first50   |       54 |   0     |    0.103 |       1     |       0.188 |     0.911 |            0.304 |   25 |    0 |   26 |    3 |
| zero_shot_llm (qwen2.5:3b) | B_kaggle_scam_nonscam | full      |      200 |   0     |    0.282 |       1     |       0.44  |     0.974 |            0.281 |  115 |    0 |   61 |   24 |
| zero_shot_llm (qwen2.5:3b) | B_kaggle_scam_nonscam | first50   |       60 |   0     |    0.179 |       1     |       0.303 |     0.938 |            0.22  |   32 |    0 |   23 |    5 |
| zero_shot_llm (qwen2.5:3b) | B_real                | full      |      200 |   0     |    0.166 |       1     |       0.284 |     0.995 |            0.144 |    1 |    0 |  166 |   33 |
| zero_shot_llm (qwen2.5:3b) | B_real                | first50   |       60 | nan     |    0.067 |       1     |       0.125 |   nan     |            0.179 |    0 |    0 |   56 |    4 |
| zero_shot_llm (qwen2.5:3b) | B_synthetic_own       | full      |      200 |   0     |    0.197 |       1     |       0.329 |     0.694 |            0.24  |   58 |    0 |  114 |   28 |
| zero_shot_llm (qwen2.5:3b) | B_synthetic_own       | first50   |       60 |   0     |    0.143 |       1     |       0.25  |     0.728 |            0.146 |   18 |    0 |   36 |    6 |
