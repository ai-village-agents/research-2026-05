# Per-dimension horse-race: cluster-bootstrap 95% CIs

For each of the five rubric dimensions, cluster-bootstrap by prompt_id (B=300) within every judge × condition cell, refit `score_DIM ~ author_is_self + predicted_self + C(author) + C(category)` (OLS via pseudo-inverse, pure numpy), and report percentile 95% CIs on β(author_is_self) and β(predicted_self). Companion to `analysis/per_judge_horse_race.py` and `analysis/horse_race_bootstrap.py` (the latter is the composite-only version).

## Condition C1

### Correctness

| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +1.86 | [+1.41, +2.40] ✓ | +1.73 | [+0.51, +2.79] ✓ | 120 |
| Gemini 3.1 Pro | -0.00 | [-0.00, +0.00] — | +0.00 | [-0.00, +0.00] — | 120 |
| GPT-5.5 | -0.90 | [-1.37, -0.49] ✓ | +1.87 | [+0.87, +2.91] ✓ | 120 |
| Kimi K2.6 | -1.63 | [-2.28, -1.11] ✓ | -0.21 | [-0.97, +0.65] — | 120 |

### Completeness

| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.30 | [+1.95, +2.60] ✓ | +1.65 | [+0.85, +2.53] ✓ | 120 |
| Gemini 3.1 Pro | -0.18 | [-0.26, -0.10] ✓ | -0.09 | [-0.34, +0.17] — | 120 |
| GPT-5.5 | -1.04 | [-1.49, -0.74] ✓ | +1.93 | [+1.17, +2.92] ✓ | 120 |
| Kimi K2.6 | -1.73 | [-2.27, -1.19] ✓ | -0.08 | [-0.92, +0.71] — | 120 |

### Clarity

| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.63 | [+2.31, +3.00] ✓ | +0.02 | [-0.53, +0.40] — | 120 |
| Gemini 3.1 Pro | -0.11 | [-0.19, -0.04] ✓ | -0.11 | [-0.36, +0.02] — | 120 |
| GPT-5.5 | -0.53 | [-0.63, -0.42] ✓ | +0.54 | [+0.41, +0.69] ✓ | 120 |
| Kimi K2.6 | -1.32 | [-1.73, -0.94] ✓ | -0.08 | [-0.58, +0.47] — | 120 |

### Creativity

| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.80 | [+2.46, +3.09] ✓ | +0.23 | [-0.19, +0.61] — | 120 |
| Gemini 3.1 Pro | +0.00 | [-0.00, +0.00] — | -0.01 | [-0.05, +0.00] — | 120 |
| GPT-5.5 | -0.64 | [-0.82, -0.43] ✓ | +0.13 | [-0.07, +0.36] — | 120 |
| Kimi K2.6 | -2.00 | [-2.48, -1.57] ✓ | -0.02 | [-0.78, +0.67] — | 120 |

### Constraint adherence

| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.19 | [+1.81, +2.55] ✓ | +1.75 | [+0.91, +2.56] ✓ | 120 |
| Gemini 3.1 Pro | -0.00 | [-0.00, +0.00] — | +0.00 | [-0.00, +0.00] — | 120 |
| GPT-5.5 | -0.83 | [-1.30, -0.45] ✓ | +2.28 | [+1.50, +3.25] ✓ | 120 |
| Kimi K2.6 | -1.66 | [-2.34, -1.12] ✓ | -0.21 | [-0.99, +0.51] — | 120 |

## Condition C2

### Correctness

| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.07 | [+1.25, +3.10] ✓ | +1.08 | [-0.79, +2.49] — | 120 |
| Gemini 3.1 Pro | -0.00 | [-0.00, +0.00] — | +0.00 | [-0.00, +0.00] — | 120 |
| GPT-5.5 | -0.82 | [-1.30, -0.37] ✓ | +1.97 | [+1.11, +2.83] ✓ | 120 |
| Kimi K2.6 | -1.67 | [-2.23, -1.05] ✓ | -0.08 | [-0.79, +0.71] — | 120 |

### Completeness

| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.27 | [+1.51, +3.15] ✓ | +1.46 | [-0.40, +2.80] — | 120 |
| Gemini 3.1 Pro | -0.19 | [-0.27, -0.10] ✓ | -0.17 | [-0.35, +0.00] — | 120 |
| GPT-5.5 | -0.88 | [-1.22, -0.49] ✓ | +1.96 | [+1.19, +2.65] ✓ | 120 |
| Kimi K2.6 | -1.80 | [-2.39, -1.22] ✓ | +0.05 | [-0.67, +0.85] — | 120 |

### Clarity

| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +1.95 | [+1.29, +2.60] ✓ | +0.00 | [-0.98, +1.01] — | 120 |
| Gemini 3.1 Pro | -0.08 | [-0.18, +0.00] — | -0.02 | [-0.29, +0.27] — | 120 |
| GPT-5.5 | -0.25 | [-0.48, -0.01] ✓ | +0.30 | [+0.04, +0.54] ✓ | 120 |
| Kimi K2.6 | -1.32 | [-1.77, -0.90] ✓ | +0.05 | [-0.48, +0.60] — | 120 |

### Creativity

| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.70 | [+1.99, +3.48] ✓ | +0.25 | [-0.82, +1.18] — | 120 |
| Gemini 3.1 Pro | +0.01 | [-0.00, +0.04] — | +0.06 | [-0.08, +0.26] — | 120 |
| GPT-5.5 | -0.51 | [-0.74, -0.24] ✓ | +0.23 | [-0.03, +0.44] — | 120 |
| Kimi K2.6 | -1.95 | [-2.43, -1.45] ✓ | +0.10 | [-0.59, +0.80] — | 120 |

### Constraint adherence

| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.07 | [+1.31, +3.06] ✓ | +1.17 | [-0.39, +2.41] — | 120 |
| Gemini 3.1 Pro | -0.00 | [-0.00, +0.00] — | +0.00 | [-0.00, +0.00] — | 120 |
| GPT-5.5 | -0.83 | [-1.26, -0.42] ✓ | +2.09 | [+1.29, +2.75] ✓ | 120 |
| Kimi K2.6 | -1.72 | [-2.32, -1.07] ✓ | -0.07 | [-0.81, +0.81] — | 120 |

## Condition C3

### Correctness

| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +1.85 | [+1.35, +2.48] ✓ | +1.71 | [+0.43, +2.83] ✓ | 120 |
| Gemini 3.1 Pro | -0.00 | [-0.00, +0.00] — | +0.00 | [-0.00, +0.00] — | 120 |
| GPT-5.5 | -0.90 | [-1.38, -0.49] ✓ | +1.87 | [+0.87, +2.95] ✓ | 120 |
| Kimi K2.6 | -1.63 | [-2.26, -1.02] ✓ | -0.21 | [-1.04, +0.53] — | 120 |

### Completeness

| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.24 | [+1.96, +2.49] ✓ | +1.83 | [+1.11, +2.64] ✓ | 120 |
| Gemini 3.1 Pro | -0.18 | [-0.28, -0.10] ✓ | -0.09 | [-0.32, +0.14] — | 120 |
| GPT-5.5 | -1.04 | [-1.41, -0.74] ✓ | +1.93 | [+1.10, +2.80] ✓ | 120 |
| Kimi K2.6 | -1.73 | [-2.33, -1.24] ✓ | -0.08 | [-0.91, +0.73] — | 120 |

### Clarity

| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.07 | [+1.91, +2.34] ✓ | +0.31 | [-0.18, +0.63] — | 120 |
| Gemini 3.1 Pro | -0.11 | [-0.18, -0.04] ✓ | -0.11 | [-0.34, +0.06] — | 120 |
| GPT-5.5 | -0.53 | [-0.62, -0.42] ✓ | +0.54 | [+0.42, +0.68] ✓ | 120 |
| Kimi K2.6 | -1.32 | [-1.75, -0.93] ✓ | -0.08 | [-0.65, +0.49] — | 120 |

### Creativity

| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +2.75 | [+2.51, +3.00] ✓ | +0.73 | [+0.30, +1.09] ✓ | 120 |
| Gemini 3.1 Pro | +0.00 | [-0.00, +0.00] — | -0.01 | [-0.04, +0.00] — | 120 |
| GPT-5.5 | -0.64 | [-0.85, -0.45] ✓ | +0.13 | [-0.08, +0.40] — | 120 |
| Kimi K2.6 | -2.00 | [-2.43, -1.51] ✓ | -0.02 | [-0.84, +0.74] — | 120 |

### Constraint adherence

| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |
|---|---:|---|---:|---|---:|
| Claude Opus 4.7 | +1.77 | [+1.42, +2.10] ✓ | +2.04 | [+1.19, +2.92] ✓ | 120 |
| Gemini 3.1 Pro | -0.00 | [-0.00, +0.00] — | +0.00 | [-0.00, +0.00] — | 120 |
| GPT-5.5 | -0.83 | [-1.25, -0.51] ✓ | +2.28 | [+1.36, +3.17] ✓ | 120 |
| Kimi K2.6 | -1.66 | [-2.33, -1.01] ✓ | -0.21 | [-1.16, +0.75] — | 120 |

## Interpretation

**Content vs form dissociation (PR #10) was a *pooled-judge* finding.** The per-judge × per-dimension bootstrap CIs let us check whether it holds within each judge or whether it's an artefact of averaging different judge profiles. If Claude's raw-author β > 0 on clarity/creativity *and* on correctness/completeness/constraint, the dissociation is judge-specific rather than universal.

**A coefficient whose 95% CI excludes zero (marked ✓)** is robustly nonzero after cluster resampling over prompts; coefficients marked — are within sampling noise. Note: B is small relative to the composite bootstrap (500 vs 2000) because we now run 5×3×4 = 60 cells, each costing one full refit per iteration; widening B is a matter of compute.
