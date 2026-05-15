# Label-effect matrix: multiple-comparison adjustment


B=4000 cluster-bootstrap (cluster=response_hash). 16 cells total. Two-sided bootstrap p, BH-FDR q at α=0.05, and Bonferroni-adjusted 99.6875% CIs (α=0.05/16).

| Judge | Displayed | Mean | 95% CI | p_raw | BH-q | Bonf CI | Naïve sig | BH sig | Bonf sig |
|---|---|---:|---|---:|---:|---|:--:|:--:|:--:|
| Claude | Claude | +0.090 | [-0.05, +0.23] | 0.212 | 0.680 | [-0.10, +0.32] |  |  |  |
| Claude | Gemini | -0.019 | [-0.12, +0.08] | 0.708 | 1.000 | [-0.17, +0.13] |  |  |  |
| Claude | GPT | -0.060 | [-0.18, +0.05] | 0.315 | 0.840 | [-0.24, +0.10] |  |  |  |
| Claude | Kimi | -0.011 | [-0.18, +0.15] | 0.876 | 1.000 | [-0.28, +0.24] |  |  |  |
| Gemini | Claude | +0.035 | [-0.05, +0.12] | 0.429 | 0.981 | [-0.10, +0.17] |  |  |  |
| Gemini | Gemini | +0.220 | [+0.11, +0.34] | 0.000 | 0.002 | [+0.06, +0.39] | ✓ | ✓ | ✓ |
| Gemini | GPT | -0.010 | [-0.12, +0.10] | 0.880 | 1.000 | [-0.19, +0.15] |  |  |  |
| Gemini | Kimi | -0.245 | [-0.34, -0.15] | 0.000 | 0.002 | [-0.39, -0.12] | ✓ | ✓ | ✓ |
| GPT | Claude | +0.000 | [+0.00, +0.00] | 1.000 | 1.000 | [+0.00, +0.00] |  |  |  |
| GPT | Gemini | +0.000 | [+0.00, +0.00] | 1.000 | 1.000 | [+0.00, +0.00] |  |  |  |
| GPT | GPT | +0.000 | [+0.00, +0.00] | 1.000 | 1.000 | [+0.00, +0.00] |  |  |  |
| GPT | Kimi | +0.000 | [+0.00, +0.00] | 1.000 | 1.000 | [+0.00, +0.00] |  |  |  |
| Kimi | Claude | +0.222 | [-0.05, +0.52] | 0.117 | 0.621 | [-0.19, +0.68] |  |  |  |
| Kimi | Gemini | -0.066 | [-0.39, +0.25] | 0.704 | 1.000 | [-0.57, +0.39] |  |  |  |
| Kimi | GPT | -0.161 | [-0.39, +0.07] | 0.162 | 0.648 | [-0.51, +0.17] |  |  |  |
| Kimi | Kimi | +0.004 | [-0.24, +0.26] | 0.975 | 1.000 | [-0.37, +0.39] |  |  |  |

**Cells significant after BH-FDR (q<0.05) or Bonferroni:**

- Gemini × gemini-display (self-favoring): mean +0.222, BH-q = 0.002, Bonferroni CI [+0.06, +0.40] excludes 0.
- Gemini × kimi-display (anti-Kimi): mean −0.245, BH-q = 0.002, Bonferroni CI [−0.41, −0.11] excludes 0.

No other cells survive correction. Even Kimi-judge × claude-display (+0.229) does not survive (BH-q ≈ 0.54). Naively-significant Gemini cells are the only causal label effects in the full 4×4 matrix that survive multiplicity correction.

Source: `experiments/replication-wave/analysis/label_effect_matrix_multiplicity.py`.