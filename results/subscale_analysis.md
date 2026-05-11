# Per-rubric-dimension self-preference (subscale analysis)

Same horse-race specification as the recognition-mediation analysis, but the dependent variable is each of the five 1–10 rubric dimensions (rather than the composite mean). All regressions include author / judge / category fixed effects and use HC0 robust standard errors. * p<0.05, ** p<0.01, *** p<0.001.

## C1 descriptive: per-dimension self-preference gap

| dimension            |   mean(self) |   mean(other) |   gap |
|:---------------------|-------------:|--------------:|------:|
| correctness          |        9.056 |         8.104 | 0.952 |
| completeness         |        9.167 |         8.004 | 1.163 |
| clarity              |        9.156 |         8.611 | 0.544 |
| creativity           |        7.567 |         6.763 | 0.804 |
| constraint_adherence |        9.544 |         8.222 | 1.322 |

## Condition C1 — per-dimension regressions

### C1: composite ~ author_is_self + FE (no belief control)

| dimension | β(author_is_self) | SE | 95% CI | p-stars |
|---|---:|---:|---:|:---:|
| correctness | +0.178 | 0.110 | [-0.038, +0.394] |  |
| completeness | +0.367 | 0.108 | [+0.155, +0.578] | *** |
| clarity | +0.383 | 0.064 | [+0.258, +0.509] | *** |
| creativity | +0.606 | 0.092 | [+0.425, +0.786] | *** |
| constraint_adherence | +0.556 | 0.127 | [+0.307, +0.804] | *** |

### C1 horse race: dim ~ author_is_self + predicted_self + FE

| dimension | β(author_is_self) | SE | β(predicted_self) | SE |
|---|---:|---:|---:|---:|
| correctness | -0.340 | 0.180 | +0.981*** | 0.254 |
| completeness | -0.130 | 0.170 | +0.940*** | 0.228 |
| clarity | +0.347*** | 0.080 | +0.070 | 0.085 |
| creativity | +0.587*** | 0.098 | +0.035 | 0.115 |
| constraint_adherence | -0.073 | 0.183 | +1.191*** | 0.239 |

## Condition C2 — per-dimension regressions

### C2: composite ~ author_is_self + FE (no belief control)

| dimension | β(author_is_self) | SE | 95% CI | p-stars |
|---|---:|---:|---:|:---:|
| correctness | +0.122 | 0.137 | [-0.146, +0.391] |  |
| completeness | +0.244 | 0.130 | [-0.010, +0.499] |  |
| clarity | +0.000 | 0.097 | [-0.191, +0.191] |  |
| creativity | +0.394 | 0.109 | [+0.181, +0.608] | *** |
| constraint_adherence | +0.156 | 0.161 | [-0.159, +0.470] |  |

### C2 horse race: dim ~ author_is_self + predicted_self + FE

| dimension | β(author_is_self) | SE | β(predicted_self) | SE |
|---|---:|---:|---:|---:|
| correctness | -0.365 | 0.201 | +0.923** | 0.294 |
| completeness | -0.277 | 0.197 | +0.988*** | 0.283 |
| clarity | -0.025 | 0.101 | +0.048 | 0.136 |
| creativity | +0.316** | 0.121 | +0.149 | 0.163 |
| constraint_adherence | -0.385 | 0.221 | +1.025*** | 0.300 |

## Condition C3 — per-dimension regressions

### C3: composite ~ author_is_self + FE (no belief control)

| dimension | β(author_is_self) | SE | 95% CI | p-stars |
|---|---:|---:|---:|:---:|
| correctness | +0.161 | 0.109 | [-0.053, +0.375] |  |
| completeness | +0.372 | 0.110 | [+0.156, +0.589] | *** |
| clarity | +0.083 | 0.064 | [-0.043, +0.210] |  |
| creativity | +0.594 | 0.087 | [+0.425, +0.764] | *** |
| constraint_adherence | +0.367 | 0.127 | [+0.118, +0.616] | ** |

### C3 horse race: dim ~ author_is_self + predicted_self + FE

| dimension | β(author_is_self) | SE | β(predicted_self) | SE |
|---|---:|---:|---:|---:|
| correctness | -0.365* | 0.180 | +0.996*** | 0.256 |
| completeness | -0.178 | 0.172 | +1.043*** | 0.230 |
| clarity | +0.049 | 0.082 | +0.064 | 0.089 |
| creativity | +0.492*** | 0.099 | +0.194 | 0.122 |
| constraint_adherence | -0.274 | 0.187 | +1.214*** | 0.249 |

## Interpretation

If self-preference were driven by privileged access to correctness ("I am better able to tell that *my* answer is right"), the effect should concentrate on **correctness** and **completeness**. If it is driven by **style familiarity** instead — the form of one's own writing looking subjectively better — the effect should concentrate on **clarity** and **creativity**, the two dimensions that most directly track surface form. The table above lets readers see this directly.
