# Replication wave analysis report

Descriptive analysis generated from replication-local score CSVs.

## Scoring coverage

Rows: 360 / expected complete 480
Conditions: c1, c2, c3
Judges: claude-opus-4.7, gemini-3.1-pro, gpt-5.5
Authors: claude-opus-4.7, gemini-3.1-pro, gpt-5.5, kimi-k2.6
Unique prompts: 10

## Condition summary

| condition   |   mean_composite |   sd_composite |   n |   self_mean |   other_mean |   self_minus_other |
|:------------|-----------------:|---------------:|----:|------------:|-------------:|-------------------:|
| c1          |            7.937 |          1.977 | 120 |       9.033 |        7.571 |              1.462 |
| c2          |            7.455 |          2.204 | 120 |       8.407 |        7.138 |              1.269 |
| c3          |            7.938 |          1.957 | 120 |       9.107 |        7.549 |              1.558 |

## Self-preference gaps by judge

| condition   | judge           |   self_mean |   other_mean |   self_preference_gap |   n_self |   n_other |
|:------------|:----------------|------------:|-------------:|----------------------:|---------:|----------:|
| c1          | claude-opus-4.7 |        9.78 |        7.347 |                 2.433 |       10 |        30 |
| c1          | gemini-3.1-pro  |        8.38 |        7.753 |                 0.627 |       10 |        30 |
| c1          | gpt-5.5         |        8.94 |        7.613 |                 1.327 |       10 |        30 |
| c2          | claude-opus-4.7 |        8.82 |        7.333 |                 1.487 |       10 |        30 |
| c2          | gemini-3.1-pro  |        8.44 |        7.033 |                 1.407 |       10 |        30 |
| c2          | gpt-5.5         |        7.96 |        7.047 |                 0.913 |       10 |        30 |
| c3          | claude-opus-4.7 |        9.78 |        7.347 |                 2.433 |       10 |        30 |
| c3          | gemini-3.1-pro  |        8.6  |        7.687 |                 0.913 |       10 |        30 |
| c3          | gpt-5.5         |        8.94 |        7.613 |                 1.327 |       10 |        30 |

## Prompt-paired self gaps

| condition   |   mean_prompt_paired_self_gap |    sd |   n_judge_prompt_pairs |    se |   t_stat_descriptive |
|:------------|------------------------------:|------:|-----------------------:|------:|---------------------:|
| c1          |                         1.462 | 1.053 |                     30 | 0.192 |                7.603 |
| c2          |                         1.269 | 2.258 |                     30 | 0.412 |                3.078 |
| c3          |                         1.558 | 0.909 |                     30 | 0.166 |                9.383 |

## Recognition coverage

Rows: 120 / expected complete 160
Judges: claude-opus-4.7, gemini-3.1-pro, gpt-5.5
True authors: claude-opus-4.7, gemini-3.1-pro, gpt-5.5, kimi-k2.6
Predicted authors: claude-opus-4.7, gemini-3.1-pro, gpt-5.5, kimi-k2.6
Unique prompts: 10

## Recognition accuracy

| judge           |   correct |   n |   accuracy |   self_recognition_hits |   self_recognition_n |   mean_confidence |
|:----------------|----------:|----:|-----------:|------------------------:|---------------------:|------------------:|
| claude-opus-4.7 |        36 |  40 |      0.9   |                      10 |                   10 |             3.375 |
| gemini-3.1-pro  |        25 |  40 |      0.625 |                       1 |                   10 |             3.175 |
| gpt-5.5         |        40 |  40 |      1     |                      10 |                   10 |             4     |

## Recognition confusion matrix

| judge           | true_author     |   claude-opus-4.7 |   gemini-3.1-pro |   gpt-5.5 |   kimi-k2.6 |
|:----------------|:----------------|------------------:|-----------------:|----------:|------------:|
| claude-opus-4.7 | claude-opus-4.7 |                10 |                0 |         0 |           0 |
| claude-opus-4.7 | gemini-3.1-pro  |                 0 |                9 |         1 |           0 |
| claude-opus-4.7 | gpt-5.5         |                 0 |                1 |         8 |           1 |
| claude-opus-4.7 | kimi-k2.6       |                 0 |                0 |         1 |           9 |
| gemini-3.1-pro  | claude-opus-4.7 |                 9 |                0 |         1 |           0 |
| gemini-3.1-pro  | gemini-3.1-pro  |                 6 |                1 |         2 |           1 |
| gemini-3.1-pro  | gpt-5.5         |                 1 |                0 |         9 |           0 |
| gemini-3.1-pro  | kimi-k2.6       |                 1 |                2 |         1 |           6 |
| gpt-5.5         | claude-opus-4.7 |                10 |                0 |         0 |           0 |
| gpt-5.5         | gemini-3.1-pro  |                 0 |               10 |         0 |           0 |
| gpt-5.5         | gpt-5.5         |                 0 |                0 |        10 |           0 |
| gpt-5.5         | kimi-k2.6       |                 0 |                0 |         0 |          10 |
