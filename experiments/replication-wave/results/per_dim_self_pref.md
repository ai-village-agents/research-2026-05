# §3.8 backing data — per-dimension self-preference (4-judge, C1)

Reproduces from `results/long_scores.csv` (condition `c1`, pooled across Claude, Gemini, GPT-5.5, Kimi).

## Pooled gap (self − other) by dimension

| dim | self mean | other mean | gap |
|---|---:|---:|---:|
| correctness | 8.375 | 7.917 | +0.458 |
| completeness | 8.450 | 7.742 | +0.708 |
| clarity | 8.650 | 8.500 | +0.150 |
| creativity | 7.300 | 6.967 | +0.333 |
| constraint_adherence | 8.275 | 8.033 | +0.242 |

## Prompt-paired gap (n=40 judge×prompt cells with both self and ≥1 other)

| dim | mean | sd | prompt-clustered 95% CI (B=500) |
|---|---:|---:|:---|
| correctness | +0.458 | 2.484 | [+0.233, +0.692] |
| completeness | +0.708 | 2.314 | [+0.550, +0.900] |
| clarity | +0.150 | 1.518 | [−0.025, +0.317] |
| creativity | +0.333 | 2.056 | [+0.158, +0.492] |
| constraint_adherence | +0.242 | 3.335 | [−0.033, +0.525] |

## Per-judge × per-dim gap

| dim | Claude | Gemini | GPT-5.5 | Kimi |
|---|---:|---:|---:|---:|
| correctness | +2.600 | +0.600 | +1.600 | −2.967 |
| completeness | +2.933 | +0.700 | +1.667 | −2.467 |
| clarity | +1.333 | +0.733 | +0.633 | −2.100 |
| creativity | +2.967 | −0.100 | +0.500 | −2.033 |
| constraint_adherence | +2.333 | +1.200 | +2.233 | −4.800 |

## Notes
- Bootstrap: B=500 prompt-cluster resamples, seed 11.
- Adding Kimi changes the pooled interpretation: correctness, completeness, and creativity remain positive with bootstrap intervals above zero, while clarity and constraint adherence now have intervals that touch or cross zero.
- Kimi is negative on every dimension, so the 4-judge pooled gaps are much smaller than the earlier 3-judge table.
- Caveat: N=10 prompts is small; these intervals are descriptive prompt-cluster bootstraps, not a fully powered dimension-wise hypothesis family.
