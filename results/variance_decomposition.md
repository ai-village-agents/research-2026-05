# Variance decomposition of composite judge scores
Available full-judge data, conditions C1+C2+C3, N=1440 score-vectors. Sequential Type-I sum-of-squares partition of the composite score. Each row is the additional SS explained when adding that term on top of the terms above it.

Total SS = 4062.95; total variance = 2.823.

| Term | SS | % of TSS | Cumulative % |
|---|---:|---:|---:|
| Prompt (which question) | 316.43 | 7.8% | 7.8% |
| Condition (C1/C2/C3) | 3.68 | 0.1% | 7.9% |
| Judge identity | 167.99 | 4.1% | 12.0% |
| Author identity | 1271.12 | 31.3% | 43.3% |
| Judge × Author (self-pref) | 390.69 | 9.6% | 52.9% |
| **Residual (within-cell)** | 1913.04 | 47.1% | 100.0% |

## Reading

- **Author identity** is the single largest explained component — judges agree enough about *who is good* that the model under evaluation accounts for the biggest chunk of explainable score variance.
- **Judge × Author** (the self-preference signature) is about half as large as the author main effect. This is the variance that is *specific to particular judge–author pairs* over and above each judge's general severity and each author's general quality, and it is the variance that the H1 self-preference test is built to detect.
- **Prompt** and **Judge identity** explain roughly comparable, modest amounts (which questions are harder, and which judges are stricter on average).
- **Condition (C1/C2/C3)** explains essentially nothing (~0.1%): paraphrasing and bias-warning do not change *average* score levels — they shift the *pattern of who scores whom*, not the overall calibration.
- The residual (within-cell) is ~47% of total variance and captures both genuine response-level quality variation within author–prompt cells and any judge noise.
