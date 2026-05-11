# Per-judge horse-race: cluster-bootstrap 95% CIs

Resampling B=500 cluster bootstraps over prompt_id within each judge × condition cell. Model: `composite ~ author_is_self + predicted_self + C(author) + C(category)` (OLS via pseudo-inverse, no statsmodels). Reports percentile 95% CI on the two key coefficients. Companion to `analysis/per_judge_horse_race.py`.

## Condition C1

| Judge | β(author_is_self) point | 95% CI | β(predicted_self) point | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.35 | [+2.04, +2.68] | +1.08 | [+0.42, +1.69] | 120 |
| Gemini 3.1 Pro | -0.06 | [-0.08, -0.04] | -0.04 | [-0.11, +0.02] | 120 |
| GPT-5.5 | -0.79 | [-1.07, -0.57] | +1.35 | [+0.80, +1.92] | 120 |

## Condition C2

| Judge | β(author_is_self) point | 95% CI | β(predicted_self) point | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.21 | [+1.47, +3.00] | +0.79 | [-0.65, +1.94] | 120 |
| Gemini 3.1 Pro | -0.05 | [-0.08, -0.03] | -0.03 | [-0.12, +0.08] | 120 |
| GPT-5.5 | -0.66 | [-0.93, -0.35] | +1.31 | [+0.77, +1.81] | 120 |

## Condition C3

| Judge | β(author_is_self) point | 95% CI | β(predicted_self) point | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.14 | [+1.86, +2.44] | +1.33 | [+0.57, +1.93] | 120 |
| Gemini 3.1 Pro | -0.06 | [-0.08, -0.04] | -0.04 | [-0.13, +0.01] | 120 |
| GPT-5.5 | -0.79 | [-1.06, -0.55] | +1.35 | [+0.77, +1.96] | 120 |

## Are the per-judge profiles statistically different? (C1 only)

Joint bootstrap: resample prompts once per iteration, refit all three judges, take differences. Same prompt set per iteration so paired comparison is valid.

| Difference | Bootstrap mean | 95% CI | Excludes 0? |
|---|---:|---|:---:|
| claude minus gpt auth | +3.15 | [+2.79, +3.53] | ✓ |
| claude minus gemini auth | +2.41 | [+2.10, +2.71] | ✓ |
| gpt minus gemini auth | -0.74 | [-1.01, -0.52] | ✓ |
| claude minus gpt pred | -0.28 | [-1.04, +0.48] | — |
| claude minus gemini pred | +1.13 | [+0.52, +1.74] | ✓ |
| gpt minus gemini pred | +1.41 | [+0.81, +1.95] | ✓ |

## Interpretation

The point estimates from `per_judge_horse_race.py` suggested Claude is driven primarily by raw-author style, GPT-5.5 by perceived authorship with a counter-acting negative raw-author effect, and Gemini is null on both axes. Cluster-bootstrap 95% CIs show whether these differences are robust or within sampling noise. CIs that exclude zero in the difference table above mean the per-judge profiles are statistically distinguishable.
