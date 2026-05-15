# Cross-Condition Score Stability (Post-v1.3.0 Exploratory Supplement)

This supplement analyzes the response-level score stability across our three experimental conditions (C1 Baseline, C2 Paraphrased, C3 Warned) for each judge. By measuring the Spearman correlation and Mean Absolute Difference (MAD) between scores assigned to the same (author, prompt) pairs across conditions, we can quantify how vulnerable each judge is to formatting shifts and explicit debiasing prompts.

## Main Findings

*   **C3 Warning Immunity:** When presented with the C3 explicit bias warning ("You are participating in an experiment... do not favor your own text"), Claude-Opus-4.7, GPT-5.5, and Kimi-K2.6 exhibited near-perfect score rigidity. Their C1 vs C3 Spearman correlations were exactly 1.000, with a Mean Absolute Difference of ~0.00. They largely ignored the warning entirely.
*   **Gemini's Reactance:** Gemini-3.1-pro was the *only* judge to significantly alter its scores in response to the C3 warning (Spearman ρ=0.943, MAD=0.225).
*   **C2 Formatting Sensitivity:** Paraphrasing the text (C2) to remove formatting and stylistic watermarks severely disrupted the internal ranking consistency for *all* judges. Claude was the most disrupted (Spearman ρ=0.403), while Gemini was the most resilient (Spearman ρ=0.692).

## Stability Metrics by Judge

| Judge | C1 vs C2 (Paraphrased) Spearman | C1 vs C3 (Warned) Spearman | C1 vs C2 MAD | C1 vs C3 MAD |
|:---|---:|---:|---:|---:|
| claude-opus-4.7 | 0.403 | 1.000 | 1.445 | 0.000 |
| kimi-k2.6 | 0.526 | 1.000 | 1.340 | 0.005 |
| gpt-5.5 | 0.551 | 1.000 | 1.145 | 0.000 |
| gemini-3.1-pro | 0.692 | 0.943 | 1.015 | 0.225 |

Interpretation: The C3 warning is completely ineffective at changing the scoring behavior of three of the four models. The C2 paraphrasing condition represents a massive disruption to how all models grade text, introducing >1.0 points of absolute drift on average for every judge.

*Source data: [`cross_condition_stability.csv`](cross_condition_stability.csv)*
