# §3.8 backing data — per-dimension self-preference (3-judge, C1)

Reproduces from `results/long_scores.csv` (condition `c1`, 120 rows pooled across Claude/Gemini/GPT-5.5).

## Pooled gap (self − other) by dimension

| dim | self mean | other mean | gap |
|---|---:|---:|---:|
| correctness | 9.200 | 7.600 | +1.600 |
| completeness | 9.267 | 7.500 | +1.767 |
| clarity | 9.333 | 8.433 | +0.900 |
| creativity | 7.833 | 6.711 | +1.122 |
| constraint_adherence | 9.533 | 7.611 | +1.922 |

## Prompt-paired gap (n=30 judge×prompt cells with both self and ≥1 other)

| dim | mean | sd | prompt-clustered 95% CI (B=500) |
|---|---:|---:|:---|
| correctness | +1.600 | 1.334 | [+1.067, +2.056] |
| completeness | +1.767 | 1.383 | [+1.372, +2.278] |
| clarity | +0.900 | 0.565 | [+0.689, +1.106] |
| creativity | +1.122 | 1.557 | [+0.922, +1.389] |
| constraint_adherence | +1.922 | 1.327 | [+1.467, +2.322] |

## Per-judge × per-dim gap

| dim | Claude | Gemini | GPT-5.5 |
|---|---:|---:|---:|
| correctness | +2.600 | +0.600 | +1.600 |
| completeness | +2.933 | +0.700 | +1.667 |
| clarity | +1.333 | +0.733 | +0.633 |
| creativity | +2.967 | −0.100 | +0.500 |
| constraint_adherence | +2.333 | +1.200 | +2.233 |

## Notes
- Bootstrap: B=500 prompt-cluster resamples, seed 11.
- All five dimensions show positive pooled gap with 95% CI excluding zero.
- Gemini creativity is the only negative cell.
- Constraint adherence has the largest pooled gap and is the largest gap for GPT-5.5 (+2.23) and Gemini (+1.20). Claude's largest gap is on creativity (+2.97), followed by completeness (+2.93).
- Caveat: N=10 prompts is small; a strict family-wise multiple-testing correction (Bonferroni, 5 dims) gives an effective α of 0.01 per dim, but all CIs above are still away from zero.
