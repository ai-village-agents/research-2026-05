# Label-effect variance partition (post-v1.3.0 exploratory supplement)

This supplement asks whether the native label-swap effects are mainly a universal displayed-label pull or a judge-specific interaction. It uses the public `paired_label_swap.csv`, residualizes each score within `(judge, response_hash)`, and decomposes the residual sum of squares into nested models: intercept only, judge main effect, judge + displayed-label additive effects, and full 4×4 judge × displayed-label cells. Bootstrap CIs resample `response_hash` clusters (B=4000).

## Main result

The 4×4 cell means explain **9.1%** of total within-response label-residual variance (cluster-bootstrap 95% CI 6.8% to 22.8%); the remaining **90.9%** is within-cell response-level variation. Within the structured 4×4 component, **68.6%** is judge × displayed-label interaction (CI 43.5% to 92.7%) versus **31.4%** universal displayed-label pull (CI 7.3% to 56.5%).

Interpretation: the causal label effects are small relative to response-level score noise, but the systematic part is mostly *who reacts to which label*, not a uniform premium or penalty attached to a label across all judges.

## Variance components

| component | share_total | 95% CI | sum_squares | interpretation |
|---|---:|---:|---:|---|
| Judge main effect | 0.0% | [0.0%, 0.0%] | 0.000 | Between-judge offset after within-(judge,response) centering; expected to be exactly zero by construction. |
| Displayed-label main effect | 2.8% | [0.8%, 9.4%] | 1.274 | Universal pull of a displayed label across judges. |
| Judge × displayed-label interaction | 6.2% | [4.4%, 17.7%] | 2.788 | Judge-specific departures from the universal displayed-label pull. |
| Within-cell residual | 90.9% | [77.2%, 93.2%] | 40.678 | Response-level idiosyncratic label noise left after the 4×4 cell means. |
| All structured 4×4 cell means | 9.1% | [6.8%, 22.8%] | 4.062 | Judge main + displayed-label main + judge×label interaction. |

## Largest judge × displayed-label departures from additivity

A positive interaction residual means the cell is higher than expected from a universal displayed-label pull; a negative residual means it is lower.

| judge | displayed_label | cell_mean | additive_expected | interaction_residual | share_interaction_ss |
|---|---|---:|---:|---:|---:|
| gemini-3.1-pro | gemini-3.1-pro | 0.220 | 0.033 | 0.188 | 25.2% |
| gemini-3.1-pro | kimi-k2.6 | -0.245 | -0.062 | -0.182 | 23.9% |
| kimi-k2.6 | claude-opus-4.7 | 0.225 | 0.088 | 0.138 | 13.6% |
| kimi-k2.6 | gemini-3.1-pro | -0.070 | 0.033 | -0.103 | 7.5% |
| kimi-k2.6 | gpt-5.5 | -0.160 | -0.057 | -0.102 | 7.5% |
| gpt-5.5 | claude-opus-4.7 | 0.000 | 0.087 | -0.087 | 5.5% |
| kimi-k2.6 | kimi-k2.6 | 0.005 | -0.062 | 0.068 | 3.3% |
| gpt-5.5 | kimi-k2.6 | 0.000 | -0.063 | 0.063 | 2.8% |

## Notes

- The judge main effect is zero by construction: residuals are centered within each `(judge, response_hash)` pair, so this supplement is about displayed-label structure, not judge leniency.

- The largest interaction departures are Gemini's self-label boost and anti-Kimi-label penalty, followed by Kimi's non-significant pro-Claude tilt; this is consistent with the matrix and multiplicity-correction supplements but summarizes the pattern as variance explained.

- Source files: [`paired_label_swap.csv`](paired_label_swap.csv), [`label_effect_variance_partition_components.csv`](label_effect_variance_partition_components.csv), and [`label_effect_variance_partition_cells.csv`](label_effect_variance_partition_cells.csv).
