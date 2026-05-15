# Label Effect Matrix (judge × displayed_label)


Mean within-(judge, response) residual by displayed label, with 2000-iter cluster-bootstrap 95% CI (cluster = response_hash).

| Judge \ Displayed label | claude | gemini | gpt | kimi |
|---|---:|---:|---:|---:|
| **claude-opus-4.7** | +0.090 [-0.05, +0.23] | -0.020 [-0.12, +0.07] | -0.060 [-0.17, +0.05] | -0.010 [-0.18, +0.15] |
| **gemini-3.1-pro** | +0.035 [-0.05, +0.13] | +0.220 [+0.11, +0.33] * | -0.010 [-0.13, +0.09] | -0.245 [-0.34, -0.16] * |
| **gpt-5.5** | +0.000 [+0.00, +0.00] | +0.000 [+0.00, +0.00] | +0.000 [+0.00, +0.00] | +0.000 [+0.00, +0.00] |
| **kimi-k2.6** | +0.225 [-0.05, +0.52] | -0.070 [-0.40, +0.26] | -0.160 [-0.39, +0.07] | +0.005 [-0.24, +0.26] |

Cells marked with * have 95% CI excluding zero. Diagonal cells (judge==displayed_label) are the *self-label* causal effect for each judge. Off-diagonal cells reveal **directed** label biases: e.g., how does Gemini score `kimi-k2.6`-labelled responses relative to those same responses under other labels?

Source: `experiments/replication-wave/results/paired_label_swap.csv` (N=320 per-row scores; 4×4=16 cells).