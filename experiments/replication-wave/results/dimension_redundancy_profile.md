# Rubric-dimension redundancy profile (post-v1.3.0 exploratory supplement)

This supplement does **not** change the headline v1.3.0 estimands. It asks a measurement question: are the five 1–10 rubric dimensions behaving like five largely independent axes, or mostly as repeated noisy views of a single latent quality factor? It uses only canonical `long_scores.csv`.

## Main result

Across all 480 replication-wave ratings, Cronbach's alpha across the five dimensions is **0.927**, the mean pairwise Pearson correlation is **0.776**, and the first principal component explains **82.2%** of standardized dimension variance. That means the composite is mostly a general-quality score, not five independent measurements.

The strongest dimension pair is **correctness ↔ completeness** (Pearson 0.896, Spearman 0.882); the weakest is **correctness ↔ creativity** (Pearson 0.700, Spearman 0.676).

Leaving out any one dimension barely changes the pooled C1 self-preference gap: the largest absolute shift is dropping **completeness**, which changes the gap by **-0.082** points from the full-composite gap of **0.378**.

## Overall/by-condition/by-judge reliability

| scope | value | n | cronbach_alpha | mean_pairwise_pearson | mean_pairwise_spearman | pc1_variance_share | pc2_variance_share |
|---|---:|---:|---:|---:|---:|---:|---:|
| all | all | 480 | 0.927 | 0.776 | 0.777 | 0.822 | 0.068 |
| condition | c1 | 160 | 0.939 | 0.804 | 0.776 | 0.845 | 0.064 |
| condition | c2 | 160 | 0.911 | 0.731 | 0.767 | 0.786 | 0.080 |
| condition | c3 | 160 | 0.938 | 0.808 | 0.780 | 0.847 | 0.067 |
| judge | claude-opus-4.7 | 120 | 0.934 | 0.790 | 0.779 | 0.833 | 0.062 |
| judge | gemini-3.1-pro | 120 | 0.911 | 0.736 | 0.716 | 0.791 | 0.094 |
| judge | gpt-5.5 | 120 | 0.937 | 0.811 | 0.815 | 0.850 | 0.065 |
| judge | kimi-k2.6 | 120 | 0.925 | 0.779 | 0.813 | 0.824 | 0.061 |

## Pairwise dimension correlations

| dimension_a | dimension_b | pearson | spearman | mean_abs_difference |
|---|---:|---:|---:|---:|
| correctness | completeness | 0.896 | 0.882 | 0.642 |
| completeness | constraint_adherence | 0.853 | 0.846 | 1.133 |
| correctness | constraint_adherence | 0.815 | 0.822 | 1.250 |
| correctness | clarity | 0.789 | 0.813 | 0.981 |
| completeness | clarity | 0.781 | 0.815 | 1.090 |
| completeness | creativity | 0.775 | 0.764 | 1.406 |
| clarity | constraint_adherence | 0.743 | 0.801 | 1.715 |
| clarity | creativity | 0.704 | 0.684 | 1.633 |
| creativity | constraint_adherence | 0.701 | 0.666 | 2.015 |
| correctness | creativity | 0.700 | 0.676 | 1.465 |

## First two principal components

Loadings are from a PCA of the all-row dimension correlation matrix; PC1 is oriented positive so larger scores mean higher general quality.

| dimension | pc1_loading | pc2_loading | pc1_variance_share | pc2_variance_share |
|---|---:|---:|---:|---:|
| correctness | 0.459 | -0.346 | 0.822 | 0.068 |
| completeness | 0.470 | -0.117 | 0.822 | 0.068 |
| clarity | 0.437 | -0.055 | 0.822 | 0.068 |
| creativity | 0.421 | 0.881 | 0.822 | 0.068 |
| constraint_adherence | 0.448 | -0.296 | 0.822 | 0.068 |

## Leave-one-dimension C1 self-gap sensitivity

| dropped_dimension | c1_pooled_self_gap | delta_vs_full_composite |
|---|---:|---:|
| completeness | 0.296 | -0.082 |
| correctness | 0.358 | -0.020 |
| creativity | 0.390 | 0.011 |
| constraint_adherence | 0.412 | 0.034 |
| clarity | 0.435 | 0.057 |

## Interpretation

- The five rubric dimensions are highly redundant: most variance is a shared quality factor. This supports using the simple mean composite for headline analyses.

- Redundancy does not mean the dimensions are useless. Per-dimension bias analyses remain informative because self-preference can concentrate more on constraint/completeness than on style, but the composite is not fragile to dropping any single dimension.

- This is a post-release measurement-validity diagnostic; it complements, rather than replaces, the observational and label-swap self-preference estimands.
