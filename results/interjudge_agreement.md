# Exploratory inter-judge agreement

This descriptive check asks how similarly the available judges rate the same blind responses. It uses the preregistered five-dimension composite score and one item per `(condition, author, prompt_id)`. The current report is coverage-aware: it includes 4 judges and should be regenerated when missing judges arrive.

## Summary by condition

| condition   |   judges |   complete_items |   mean_pairwise_r |   mean_pairwise_abs_diff |   cronbach_alpha |
|:------------|---------:|-----------------:|------------------:|-------------------------:|-----------------:|
| c1          |        4 |              120 |             0.599 |                    0.973 |            0.868 |
| c2          |        4 |              120 |             0.565 |                    1.189 |            0.855 |
| c3          |        4 |              120 |             0.586 |                    1.076 |            0.867 |

## Pairwise judge diagnostics

| condition   | judge_pair                        |   n_items |   pearson_r |   mean_abs_diff |   mean_signed_diff_first_minus_second |
|:------------|:----------------------------------|----------:|------------:|----------------:|--------------------------------------:|
| c1          | claude-opus-4.7 vs gemini-3.1-pro |       120 |       0.303 |           1.233 |                                 0.163 |
| c1          | claude-opus-4.7 vs gpt-5.5        |       120 |       0.92  |           0.65  |                                 0.607 |
| c1          | claude-opus-4.7 vs kimi-k2.6      |       120 |       0.957 |           0.445 |                                -0.078 |
| c1          | gemini-3.1-pro vs gpt-5.5         |       120 |       0.294 |           1.213 |                                 0.443 |
| c1          | gemini-3.1-pro vs kimi-k2.6       |       120 |       0.24  |           1.365 |                                -0.242 |
| c1          | gpt-5.5 vs kimi-k2.6              |       120 |       0.881 |           0.928 |                                -0.685 |
| c2          | claude-opus-4.7 vs gemini-3.1-pro |       120 |       0.243 |           1.537 |                                 0.337 |
| c2          | claude-opus-4.7 vs gpt-5.5        |       120 |       0.903 |           1.113 |                                 1.07  |
| c2          | claude-opus-4.7 vs kimi-k2.6      |       120 |       0.903 |           0.625 |                                 0.095 |
| c2          | gemini-3.1-pro vs gpt-5.5         |       120 |       0.254 |           1.29  |                                 0.733 |
| c2          | gemini-3.1-pro vs kimi-k2.6       |       120 |       0.255 |           1.402 |                                -0.242 |
| c2          | gpt-5.5 vs kimi-k2.6              |       120 |       0.828 |           1.168 |                                -0.975 |
| c3          | claude-opus-4.7 vs gemini-3.1-pro |       120 |       0.24  |           1.487 |                                 0.527 |
| c3          | claude-opus-4.7 vs gpt-5.5        |       120 |       0.89  |           1.02  |                                 0.97  |
| c3          | claude-opus-4.7 vs kimi-k2.6      |       120 |       0.969 |           0.445 |                                 0.285 |
| c3          | gemini-3.1-pro vs gpt-5.5         |       120 |       0.294 |           1.213 |                                 0.443 |
| c3          | gemini-3.1-pro vs kimi-k2.6       |       120 |       0.24  |           1.365 |                                -0.242 |
| c3          | gpt-5.5 vs kimi-k2.6              |       120 |       0.881 |           0.928 |                                -0.685 |

## Interpretation

Across conditions, mean pairwise judge correlations range from 0.56 to 0.60, with highest agreement in c1 and lowest in c2. Mean absolute inter-judge differences are about 1.08 composite-score points. These ordinary judge-to-judge differences are larger than the pooled regression self-preference coefficient, which is why the preregistered tests use within-prompt, fixed-effect comparisons rather than raw cross-judge means.

This is exploratory rather than preregistered. Cronbach's alpha is included as a compact consistency diagnostic, not as a claim that LLM judges are exchangeable human raters.
