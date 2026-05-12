# Per-rubric-dimension self-preference (subscale analysis)

Same horse-race specification as the recognition-mediation analysis, but the dependent variable is each of the five 1–10 rubric dimensions (rather than the composite mean). All regressions include author / judge / category fixed effects and use HC0 robust standard errors. * p<0.05, ** p<0.01, *** p<0.001.

## C1 descriptive: per-dimension self-preference gap

| dimension            |   mean(self) |   mean(other) |    gap |
|:---------------------|-------------:|--------------:|-------:|
| correctness          |        8.433 |         8.481 | -0.047 |
| completeness         |        8.458 |         8.339 |  0.119 |
| clarity              |        8.683 |         8.817 | -0.133 |
| creativity           |        7.033 |         7.169 | -0.136 |
| constraint_adherence |        8.725 |         8.508 |  0.217 |

## Condition C1 — per-dimension regressions

### C1: composite ~ author_is_self + FE (no belief control)

| dimension | β(author_is_self) | SE | 95% CI | p-stars |
|---|---:|---:|---:|:---:|
| correctness | -0.047 | 0.177 | [-0.393, +0.299] |  |
| completeness | +0.119 | 0.169 | [-0.211, +0.450] |  |
| clarity | -0.133 | 0.116 | [-0.361, +0.094] |  |
| creativity | -0.136 | 0.160 | [-0.450, +0.178] |  |
| constraint_adherence | +0.217 | 0.189 | [-0.154, +0.587] |  |

### C1 horse race: dim ~ author_is_self + predicted_self + FE

| dimension | β(author_is_self) | SE | β(predicted_self) | SE |
|---|---:|---:|---:|---:|
| correctness | -0.277 | 0.204 | +0.590** | 0.205 |
| completeness | -0.123 | 0.193 | +0.623*** | 0.187 |
| clarity | -0.217 | 0.137 | +0.214 | 0.119 |
| creativity | -0.255 | 0.177 | +0.306 | 0.167 |
| constraint_adherence | -0.084 | 0.214 | +0.773*** | 0.208 |

## Condition C2 — per-dimension regressions

### C2: composite ~ author_is_self + FE (no belief control)

| dimension | β(author_is_self) | SE | 95% CI | p-stars |
|---|---:|---:|---:|:---:|
| correctness | -0.061 | 0.185 | [-0.424, +0.302] |  |
| completeness | +0.031 | 0.176 | [-0.313, +0.375] |  |
| clarity | -0.419 | 0.125 | [-0.665, -0.174] | *** |
| creativity | -0.244 | 0.163 | [-0.564, +0.075] |  |
| constraint_adherence | -0.081 | 0.195 | [-0.464, +0.302] |  |

### C2 horse race: dim ~ author_is_self + predicted_self + FE

| dimension | β(author_is_self) | SE | β(predicted_self) | SE |
|---|---:|---:|---:|---:|
| correctness | -0.286 | 0.211 | +0.577* | 0.224 |
| completeness | -0.233 | 0.204 | +0.679** | 0.214 |
| clarity | -0.498*** | 0.142 | +0.201 | 0.136 |
| creativity | -0.390* | 0.183 | +0.373* | 0.180 |
| constraint_adherence | -0.339 | 0.225 | +0.664** | 0.233 |

## Condition C3 — per-dimension regressions

### C3: composite ~ author_is_self + FE (no belief control)

| dimension | β(author_is_self) | SE | 95% CI | p-stars |
|---|---:|---:|---:|:---:|
| correctness | -0.058 | 0.177 | [-0.406, +0.289] |  |
| completeness | +0.119 | 0.169 | [-0.212, +0.451] |  |
| clarity | -0.342 | 0.113 | [-0.563, -0.120] | ** |
| creativity | -0.117 | 0.157 | [-0.424, +0.190] |  |
| constraint_adherence | +0.078 | 0.188 | [-0.291, +0.447] |  |

### C3 horse race: dim ~ author_is_self + predicted_self + FE

| dimension | β(author_is_self) | SE | β(predicted_self) | SE |
|---|---:|---:|---:|---:|
| correctness | -0.289 | 0.204 | +0.592** | 0.205 |
| completeness | -0.143 | 0.193 | +0.676*** | 0.187 |
| clarity | -0.410** | 0.135 | +0.175 | 0.118 |
| creativity | -0.265 | 0.174 | +0.382* | 0.165 |
| constraint_adherence | -0.221 | 0.214 | +0.767*** | 0.210 |

## Interpretation

If self-preference were driven by privileged access to correctness ("I am better able to tell that *my* answer is right"), the effect should concentrate on **correctness** and **completeness**. If it is driven by **style familiarity** instead — the form of one's own writing looking subjectively better — the effect should concentrate on **clarity** and **creativity**, the two dimensions that most directly track surface form. The table above lets readers see this directly.
