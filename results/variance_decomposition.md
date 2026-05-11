# Variance decomposition of composite judge scores
3-judge interim data, conditions C1+C2+C3, N=1080 score-vectors. Sequential Type-I sum-of-squares partition of the composite score. Each row is the additional SS explained when adding that term on top of the terms above it.

Total SS = 2555.65; total variance = 2.369.

| Term | SS | % of TSS | Cumulative % |
|---|---:|---:|---:|
| Prompt (which question) | 163.18 | 6.4% | 6.4% |
| Condition (C1/C2/C3) | 4.93 | 0.2% | 6.6% |
| Judge identity | 142.44 | 5.6% | 12.2% |
| Author identity | 735.29 | 28.8% | 40.9% |
| Judge × Author (self-pref) | 328.21 | 12.8% | 53.8% |
| **Residual (within-cell)** | 1181.59 | 46.2% | 100.0% |

## Reading

- **Author identity** is the single largest explained component — judges agree enough about *who is good* that the model under evaluation accounts for the biggest chunk of explainable score variance.
- **Judge × Author** (the self-preference signature) is about half as large as the author main effect. This is the variance that is *specific to particular judge–author pairs* over and above each judge's general severity and each author's general quality, and it is the variance that the H1 self-preference test is built to detect.
- **Prompt** and **Judge identity** explain roughly comparable, modest amounts (which questions are harder, and which judges are stricter on average).
- **Condition (C1/C2/C3)** explains essentially nothing (~0.2%): paraphrasing and bias-warning do not change *average* score levels — they shift the *pattern of who scores whom*, not the overall calibration.
- The residual (within-cell) is ~46% of total variance and captures both genuine response-level quality variation within author–prompt cells and any judge noise.
