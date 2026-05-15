# Label-effect asymmetry profile (post-v1.3.0 exploratory supplement)

This supplement does **not** change the v1.3.0 headline estimands. It compresses the 4×4 causal displayed-label matrix into row, column, and directed-pair asymmetry summaries: which judges are most label-sensitive, which displayed labels attract the most movement, and whether pairwise label reactions are reciprocated.

## Main result

By total absolute row movement, the most label-sensitive judge is **gemini-3.1-pro** (row L1 = 0.510), while the least label-sensitive is **gpt-5.5** (row L1 = 0.000). The largest displayed-label column by absolute movement is **claude-opus-4.7** (column L1 = 0.350).

Only **gemini-3.1-pro (2 BH-significant cells)** has any BH-significant cells; all other row/column asymmetry should be read descriptively.

The strongest directed pair by mean absolute mutual off-diagonal movement is **gemini-3.1-pro ↔ kimi-k2.6** (mean abs mutual effect 0.158), driven by gemini-3.1-pro's response to the kimi-k2.6 label (-0.245) versus kimi-k2.6's response to the gemini-3.1-pro label (-0.070).

## Row profile: label sensitivity by judge

| judge | row_l1_abs | row_l2_norm | diagonal_self_effect | offdiag_mean | diag_minus_offdiag_mean | diagonal_abs_share | n_positive_cells | n_negative_cells | n_zero_cells | n_bh_sig_cells | strongest_positive_label | strongest_positive_effect | strongest_negative_label | strongest_negative_effect |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gemini-3.1-pro | 0.510 | 0.331 | 0.220 | -0.073 | 0.293 | 0.431 | 2 | 2 | 0 | 2 | gemini-3.1-pro | 0.220 | kimi-k2.6 | -0.245 |
| kimi-k2.6 | 0.460 | 0.285 | 0.005 | -0.002 | 0.007 | 0.011 | 2 | 2 | 0 | 0 | claude-opus-4.7 | 0.225 | gpt-5.5 | -0.160 |
| claude-opus-4.7 | 0.180 | 0.110 | 0.090 | -0.030 | 0.120 | 0.500 | 1 | 3 | 0 | 0 | claude-opus-4.7 | 0.090 | gpt-5.5 | -0.060 |
| gpt-5.5 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | NA | 0 | 0 | 4 | 0 | claude-opus-4.7 | 0.000 | claude-opus-4.7 | 0.000 |

## Column profile: movement attracted by displayed label

| displayed_label | column_l1_abs | column_l2_norm | column_mean | n_positive_judges | n_negative_judges | n_zero_judges | n_bh_sig_judges | strongest_positive_judge | strongest_positive_effect | strongest_negative_judge | strongest_negative_effect |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| claude-opus-4.7 | 0.350 | 0.245 | 0.087 | 3 | 0 | 1 | 0 | kimi-k2.6 | 0.225 | gpt-5.5 | 0.000 |
| gemini-3.1-pro | 0.310 | 0.232 | 0.033 | 1 | 2 | 1 | 1 | gemini-3.1-pro | 0.220 | kimi-k2.6 | -0.070 |
| kimi-k2.6 | 0.260 | 0.245 | -0.062 | 1 | 2 | 1 | 1 | kimi-k2.6 | 0.005 | gemini-3.1-pro | -0.245 |
| gpt-5.5 | 0.230 | 0.171 | -0.057 | 0 | 3 | 1 | 0 | gpt-5.5 | 0.000 | kimi-k2.6 | -0.160 |

## Directed pair asymmetry

| pair | a_response_to_b_label | b_response_to_a_label | directed_difference_a_to_b_minus_b_to_a | mean_mutual_effect | mean_abs_mutual_effect |
|---|---:|---:|---:|---:|---:|
| gemini-3.1-pro ↔ kimi-k2.6 | -0.245 | -0.070 | -0.175 | -0.158 | 0.158 |
| claude-opus-4.7 ↔ kimi-k2.6 | -0.010 | 0.225 | -0.235 | 0.107 | 0.118 |
| gpt-5.5 ↔ kimi-k2.6 | 0.000 | -0.160 | 0.160 | -0.080 | 0.080 |
| claude-opus-4.7 ↔ gpt-5.5 | -0.060 | 0.000 | -0.060 | -0.030 | 0.030 |
| claude-opus-4.7 ↔ gemini-3.1-pro | -0.020 | 0.035 | -0.055 | 0.008 | 0.028 |
| gemini-3.1-pro ↔ gpt-5.5 | -0.010 | 0.000 | -0.010 | -0.005 | 0.005 |

## Interpretation

- Label sensitivity is row-concentrated rather than universal: Gemini supplies most total movement and all multiplicity-robust cells; GPT is exactly invariant.

- The largest displayed-label column by total absolute movement is Claude, mostly because Kimi has a non-significant pro-Claude tilt; the largest single negative cell remains Gemini's anti-Kimi-label effect.

- Directed reactions are not reciprocal: a judge's response to another model's label generally does not predict the other model's response to the first judge's label.
