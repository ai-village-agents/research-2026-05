# Per-judge horse-race: cluster-bootstrap 95% CIs

Available judges: Claude Opus 4.7, Gemini 3.1 Pro, GPT-5.5, Kimi K2.6.
Resampling B=500 cluster bootstraps over prompt_id within each judge × condition cell. Model: `composite ~ author_is_self + predicted_self + C(author) + C(category)` (OLS via pseudo-inverse, no statsmodels).

## Condition C1

| Judge | β(author_is_self) point | 95% CI | β(predicted_self) point | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.35 | [+2.04, +2.68] | +1.08 | [+0.42, +1.69] | 120 |
| Gemini 3.1 Pro | -0.06 | [-0.08, -0.04] | -0.04 | [-0.11, +0.02] | 120 |
| GPT-5.5 | -0.79 | [-1.07, -0.57] | +1.35 | [+0.80, +1.92] | 120 |
| Kimi K2.6 | -1.67 | [-2.17, -1.12] | -0.12 | [-0.82, +0.50] | 120 |

## Condition C2

| Judge | β(author_is_self) point | 95% CI | β(predicted_self) point | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.21 | [+1.45, +3.09] | +0.79 | [-0.70, +2.04] | 120 |
| Gemini 3.1 Pro | -0.05 | [-0.08, -0.03] | -0.03 | [-0.12, +0.07] | 120 |
| GPT-5.5 | -0.66 | [-0.93, -0.40] | +1.31 | [+0.85, +1.80] | 120 |
| Kimi K2.6 | -1.69 | [-2.21, -1.13] | +0.01 | [-0.69, +0.68] | 120 |

## Condition C3

| Judge | β(author_is_self) point | 95% CI | β(predicted_self) point | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.14 | [+1.84, +2.43] | +1.33 | [+0.62, +2.00] | 120 |
| Gemini 3.1 Pro | -0.06 | [-0.08, -0.04] | -0.04 | [-0.13, +0.01] | 120 |
| GPT-5.5 | -0.79 | [-1.07, -0.58] | +1.35 | [+0.89, +1.93] | 120 |
| Kimi K2.6 | -1.67 | [-2.21, -1.17] | -0.12 | [-0.77, +0.57] | 120 |

## Are the per-judge profiles statistically different? (C1 only)

Joint bootstrap: resample prompts once per iteration, refit all available judges, and take paired differences. Same prompt set per iteration so paired comparison is valid.

| Difference | Bootstrap mean | 95% CI | Excludes 0? |
|---|---:|---|:---:|
| Claude Opus 4.7 minus Gemini 3.1 Pro auth | +2.41 | [+2.07, +2.70] | ✓ |
| Claude Opus 4.7 minus GPT-5.5 auth | +3.15 | [+2.77, +3.57] | ✓ |
| Claude Opus 4.7 minus Kimi K2.6 auth | +4.04 | [+3.60, +4.50] | ✓ |
| Gemini 3.1 Pro minus GPT-5.5 auth | +0.74 | [+0.51, +1.00] | ✓ |
| Gemini 3.1 Pro minus Kimi K2.6 auth | +1.63 | [+1.14, +2.17] | ✓ |
| GPT-5.5 minus Kimi K2.6 auth | +0.89 | [+0.51, +1.38] | ✓ |
| Claude Opus 4.7 minus Gemini 3.1 Pro pred | +1.15 | [+0.50, +1.77] | ✓ |
| Claude Opus 4.7 minus GPT-5.5 pred | -0.26 | [-1.04, +0.60] | — |
| Claude Opus 4.7 minus Kimi K2.6 pred | +1.18 | [+0.34, +2.07] | ✓ |
| Gemini 3.1 Pro minus GPT-5.5 pred | -1.41 | [-1.93, -0.83] | ✓ |
| Gemini 3.1 Pro minus Kimi K2.6 pred | +0.04 | [-0.69, +0.80] | — |
| GPT-5.5 minus Kimi K2.6 pred | +1.44 | [+0.43, +2.41] | ✓ |

## Interpretation

The per-judge horse-race profiles are highly heterogeneous. The bootstrap CIs quantify which raw-author (`author_is_self`) and perceived-authorship (`predicted_self`) coefficients, and which between-judge contrasts, are stable under prompt-level resampling.
