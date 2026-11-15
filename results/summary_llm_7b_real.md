# Zero-shot LLM results

Model `qwen2.5:7b` via Ollama, no training. Random sample of 300 calls per test set (60 for `first50`); threshold from a shared validation sample (FPR <= 2%).

| model                      | test   | variant   |   n_test |   fpr |   recall |   precision |   f1_binary |   roc_auc |   macro_f1_types |   tn |   fp |   fn |   tp |
|:---------------------------|:-------|:----------|---------:|------:|---------:|------------:|------------:|----------:|-----------------:|-----:|-----:|-----:|-----:|
| zero_shot_llm (qwen2.5:7b) | B_real | full      |      300 | 0.111 |    0.545 |       0.158 |       0.245 |     0.815 |            0.407 |  257 |   32 |    5 |    6 |
| zero_shot_llm (qwen2.5:7b) | B_real | first50   |       60 | 0     |    0     |       0     |       0     |     0.763 |            0.325 |   57 |    0 |    3 |    0 |
| zero_shot_llm (qwen2.5:7b) | R      | full      |      300 | 0.07  |    0.25  |       0.167 |       0.2   |     0.709 |            0.414 |  264 |   20 |   12 |    4 |
| zero_shot_llm (qwen2.5:7b) | R      | first50   |       60 | 0     |    0     |       0     |       0     |     0.848 |            0.322 |   56 |    0 |    4 |    0 |
