# Extended Formal Causal Mediation Analysis

**Extensions to baseline formal mediation (PR #54):**

1. **Logistic path-a** — `predicted_self` is binary {0,1}, so linear-probability path-a may misstate the marginal effect. We re-estimate path a via IRLS logistic regression and report a hybrid indirect effect (`a_logit × b_OLS`). The logit coefficient is in log-odds units; the hybrid product is a latent-propensity interpretation.

2. **Standardized coefficients** — all paths expressed in SD units for cross-judge comparability.

3. **Sensitivity analysis** — approximate bounds on how strongly an unobserved confounder would need to correlate with mediator and outcome to nullify the indirect effect. Reported as required partial R² and Cohen's f² values (informal, since we lack Imai-Keele libraries).

**Method.** Per condition × scope:

- OLS paths: `c` (total), `a` (T→M LPM), `b` (M→Y|T), `c'` (direct), `indirect` = a·b
- Logit-hybrid paths: `a_logit` (logistic T→M), `indirect_hybrid` = a_logit·b
- Standardized paths: `_std` suffix
- Sensitivity: `needed_r2_a/b` = partial R² an unobserved confounder would need with M|T / Y|T,M to fully explain away the path coefficient; `f2_a/b` = corresponding Cohen's f²

95% CIs from 2,000-iteration cluster bootstrap by prompt_id (seed 20260512).

## Condition C1

### OLS mediation (baseline)

| Scope | N | c (total) | c' (direct) | a (T→M) | b (M→Y|T) | indirect (a·b) |
|---|---:|---:|---:|---:|---:|---:|
| pooled | 480 | +0.004 [-0.150, +0.147] | -0.168 [-0.493, +0.090] | +0.389 [+0.294, +0.478] | +0.441 [+0.098, +0.890] | +0.172 [+0.035, +0.365] |
| claude-opus-4.7 | 120 | +1.738 [+1.464, +2.011] | +1.637 [+1.297, +2.080] | +0.733 [+0.511, +0.911] | +0.137 [-0.387, +0.521] | +0.101 [-0.300, +0.426] |
| gemini-3.1-pro | 120 | +0.009 [-0.033, +0.051] | +0.007 [-0.031, +0.042] | -0.022 [-0.156, +0.100] | -0.078 [-0.142, -0.005] | +0.002 [-0.007, +0.017] |
| gpt-5.5 | 120 | +1.124 [+0.764, +1.489] | +0.762 [+0.544, +0.990] | +0.733 [+0.511, +0.911] | +0.495 [+0.273, +0.707] | +0.363 [+0.171, +0.585] |
| kimi-k2.6 | 120 | -2.856 [-3.933, -1.807] | -2.850 [-3.940, -1.787] | +0.111 [-0.111, +0.333] | -0.050 [-0.808, +0.670] | -0.006 [-0.171, +0.129] |

### Logit-hybrid mediation

| Scope | N | a_logit (T→M) | b (M→Y|T) | indirect_hybrid (a·b) |
|---|---:|---:|---:|---:|
| pooled | 480 | +1.642 [+1.215, +2.085] | +0.441 [+0.098, +0.890] | +0.725 [+0.147, +1.560] |
| claude-opus-4.7 | 120 | +4.025 [+2.518, +6.423] | +0.137 [-0.387, +0.521] | +0.552 [-1.703, +2.694] |
| gemini-3.1-pro | 120 | -0.208 [-1.283, +1.498] | -0.078 [-0.142, -0.005] | +0.016 [-0.093, +0.149] |
| gpt-5.5 | 120 | +4.025 [+2.518, +6.423] | +0.495 [+0.273, +0.707] | +1.992 [+0.880, +3.824] |
| kimi-k2.6 | 120 | +0.560 [-0.654, +1.609] | -0.050 [-0.808, +0.670] | -0.028 [-0.833, +0.638] |

### Standardized coefficients (SD units)

| Scope | a_std | b_std | c_std | c'_std | indirect_std |
|---|---:|---:|---:|---:|---:|
| pooled | +0.343 | +0.133 | +0.001 | -0.045 | +0.046 |
| claude-opus-4.7 | +0.733 | +0.033 | +0.421 | +0.397 | +0.024 |
| gemini-3.1-pro | -0.030 | -0.170 | +0.026 | +0.021 | +0.005 |
| gpt-5.5 | +0.733 | +0.123 | +0.280 | +0.189 | +0.090 |
| kimi-k2.6 | +0.111 | -0.011 | -0.611 | -0.610 | -0.001 |

### Sensitivity to unobserved confounding

| Scope | needed R²(M|T) | needed R²(Y|T,M) | f²(a) | f²(b) |
|---|---:|---:|---:|---:|
| pooled | 0.105 | 0.017 | 0.708 | 0.075 |
| claude-opus-4.7 | 0.354 | 0.001 | 6.153 | 0.006 |
| gemini-3.1-pro | 0.001 | 0.029 | 0.005 | 0.286 |
| gpt-5.5 | 0.354 | 0.015 | 6.153 | 0.081 |
| kimi-k2.6 | 0.012 | 0.000 | 0.066 | 0.001 |

## Condition C2

### OLS mediation (baseline)

| Scope | N | c (total) | c' (direct) | a (T→M) | b (M→Y|T) | indirect (a·b) |
|---|---:|---:|---:|---:|---:|---:|
| pooled | 480 | -0.155 [-0.315, -0.001] | -0.316 [-0.620, -0.061] | +0.389 [+0.300, +0.472] | +0.413 [+0.071, +0.796] | +0.161 [+0.025, +0.340] |
| claude-opus-4.7 | 120 | +1.202 [+0.718, +1.658] | +1.427 [+0.453, +2.765] | +0.733 [+0.556, +0.911] | -0.306 [-1.772, +0.785] | -0.225 [-1.380, +0.642] |
| gemini-3.1-pro | 120 | -0.011 [-0.056, +0.031] | -0.012 [-0.056, +0.027] | -0.022 [-0.167, +0.111] | -0.045 [-0.119, +0.075] | +0.001 [-0.005, +0.015] |
| gpt-5.5 | 120 | +1.153 [+0.811, +1.513] | +0.821 [+0.565, +1.061] | +0.733 [+0.511, +0.911] | +0.454 [+0.200, +0.698] | +0.333 [+0.138, +0.553] |
| kimi-k2.6 | 120 | -2.964 [-4.044, -1.911] | -2.972 [-4.058, -1.910] | +0.111 [-0.111, +0.333] | +0.068 [-0.635, +0.731] | +0.008 [-0.125, +0.141] |

### Logit-hybrid mediation

| Scope | N | a_logit (T→M) | b (M→Y|T) | indirect_hybrid (a·b) |
|---|---:|---:|---:|---:|
| pooled | 480 | +1.642 [+1.238, +2.064] | +0.413 [+0.071, +0.796] | +0.679 [+0.105, +1.480] |
| claude-opus-4.7 | 120 | +4.025 [+2.773, +6.423] | -0.306 [-1.772, +0.785] | -1.233 [-8.236, +3.817] |
| gemini-3.1-pro | 120 | -0.208 [-1.449, +1.676] | -0.045 [-0.119, +0.075] | +0.009 [-0.055, +0.161] |
| gpt-5.5 | 120 | +4.025 [+2.518, +6.423] | +0.454 [+0.200, +0.698] | +1.827 [+0.721, +3.604] |
| kimi-k2.6 | 120 | +0.560 [-0.654, +1.609] | +0.068 [-0.635, +0.731] | +0.038 [-0.604, +0.685] |

### Standardized coefficients (SD units)

| Scope | a_std | b_std | c_std | c'_std | indirect_std |
|---|---:|---:|---:|---:|---:|
| pooled | +0.343 | +0.117 | -0.039 | -0.079 | +0.040 |
| claude-opus-4.7 | +0.733 | -0.067 | +0.264 | +0.313 | -0.049 |
| gemini-3.1-pro | -0.030 | -0.100 | -0.033 | -0.036 | +0.003 |
| gpt-5.5 | +0.733 | +0.108 | +0.274 | +0.195 | +0.079 |
| kimi-k2.6 | +0.111 | +0.014 | -0.629 | -0.630 | +0.002 |

### Sensitivity to unobserved confounding

| Scope | needed R²(M|T) | needed R²(Y|T,M) | f²(a) | f²(b) |
|---|---:|---:|---:|---:|
| pooled | 0.105 | 0.014 | 0.708 | 0.057 |
| claude-opus-4.7 | 0.354 | 0.005 | 6.153 | 0.024 |
| gemini-3.1-pro | 0.001 | 0.010 | 0.005 | 0.098 |
| gpt-5.5 | 0.354 | 0.012 | 6.153 | 0.062 |
| kimi-k2.6 | 0.012 | 0.000 | 0.066 | 0.001 |

## Condition C3

### OLS mediation (baseline)

| Scope | N | c (total) | c' (direct) | a (T→M) | b (M→Y|T) | indirect (a·b) |
|---|---:|---:|---:|---:|---:|---:|
| pooled | 480 | -0.064 [-0.191, +0.061] | -0.209 [-0.494, +0.028] | +0.389 [+0.297, +0.469] | +0.373 [+0.032, +0.798] | +0.145 [+0.012, +0.323] |
| claude-opus-4.7 | 120 | +1.467 [+1.133, +1.782] | +1.227 [+0.913, +1.655] | +0.733 [+0.511, +0.911] | +0.327 [-0.142, +0.669] | +0.240 [-0.115, +0.544] |
| gemini-3.1-pro | 120 | +0.009 [-0.033, +0.051] | +0.007 [-0.031, +0.045] | -0.022 [-0.167, +0.111] | -0.078 [-0.145, -0.007] | +0.002 [-0.007, +0.019] |
| gpt-5.5 | 120 | +1.124 [+0.778, +1.500] | +0.762 [+0.542, +0.987] | +0.733 [+0.556, +0.911] | +0.495 [+0.292, +0.706] | +0.363 [+0.180, +0.607] |
| kimi-k2.6 | 120 | -2.856 [-3.876, -1.806] | -2.850 [-3.902, -1.783] | +0.111 [-0.111, +0.333] | -0.050 [-0.768, +0.660] | -0.006 [-0.167, +0.125] |

### Logit-hybrid mediation

| Scope | N | a_logit (T→M) | b (M→Y|T) | indirect_hybrid (a·b) |
|---|---:|---:|---:|---:|
| pooled | 480 | +1.642 [+1.229, +2.050] | +0.373 [+0.032, +0.798] | +0.612 [+0.048, +1.390] |
| claude-opus-4.7 | 120 | +4.025 [+2.518, +6.423] | +0.327 [-0.142, +0.669] | +1.316 [-0.654, +3.644] |
| gemini-3.1-pro | 120 | -0.208 [-1.459, +1.588] | -0.078 [-0.145, -0.007] | +0.016 [-0.095, +0.159] |
| gpt-5.5 | 120 | +4.025 [+2.773, +6.423] | +0.495 [+0.292, +0.706] | +1.992 [+0.926, +4.033] |
| kimi-k2.6 | 120 | +0.560 [-0.654, +1.609] | -0.050 [-0.768, +0.660] | -0.028 [-0.810, +0.608] |

### Standardized coefficients (SD units)

| Scope | a_std | b_std | c_std | c'_std | indirect_std |
|---|---:|---:|---:|---:|---:|
| pooled | +0.343 | +0.110 | -0.017 | -0.054 | +0.038 |
| claude-opus-4.7 | +0.733 | +0.076 | +0.342 | +0.286 | +0.056 |
| gemini-3.1-pro | -0.030 | -0.170 | +0.026 | +0.021 | +0.005 |
| gpt-5.5 | +0.733 | +0.123 | +0.280 | +0.189 | +0.090 |
| kimi-k2.6 | +0.111 | -0.011 | -0.611 | -0.610 | -0.001 |

### Sensitivity to unobserved confounding

| Scope | needed R²(M|T) | needed R²(Y|T,M) | f²(a) | f²(b) |
|---|---:|---:|---:|---:|
| pooled | 0.105 | 0.012 | 0.708 | 0.051 |
| claude-opus-4.7 | 0.354 | 0.006 | 6.153 | 0.031 |
| gemini-3.1-pro | 0.001 | 0.029 | 0.005 | 0.286 |
| gpt-5.5 | 0.354 | 0.015 | 6.153 | 0.081 |
| kimi-k2.6 | 0.012 | 0.000 | 0.066 | 0.001 |

**Interpretation notes**

- `a_logit` is in log-odds units. A positive value means actual authorship increases the log-odds of predicting 'self'.
- `indirect_hybrid` multiplies log-odds × score-points; it is a latent-propensity effect size, not directly in score units.
- Standardized coefficients allow comparison across judges with different score variances.
- `needed_r2_a` = partial R² an unobserved confounder would need with M (holding T fixed) to fully explain path a. Values < 0.01 are trivially confoundable; values > 0.30 require very strong confounders.
- `f2_a/b` are Cohen's f² effect sizes for the same bound (0.02=small, 0.15=medium, 0.35=large).

_Generated by `analysis/formal_mediation_extended.py`. Random seed 20260512._