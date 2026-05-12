# Subscale × condition horse-race: belief vs style channel

**Design.** For each rubric dimension D (correctness, completeness, clarity, creativity, constraint_adherence) and each scoring condition C (C1 baseline, C2 paraphrased, C3 warned), we fit the two-mediator horse-race used in PR #60:

```
Y_D ~ T (author_is_self)  →  c
M1  ~ T                   →  a1   (M1 = predicted_self, verbalised belief from C4)
M2  ~ T                   →  a2   (M2 = style_prob_self, stylometric LR prob)
Y_D ~ T + M1 + M2         →  c', b1, b2
```

Indirect via belief = a1·b1; indirect via style = a2·b2. 95% CIs from 2000-iter cluster bootstrap on `prompt_id`, seed 20260512. N per cell = 480 (4 judges × 4 authors × 30 prompts). Pooled across judges; per-judge heterogeneity is not modeled in this subscale table.


**Scope caveat.** This is an exploratory observed-variable mediation-style decomposition, not an identified causal mediation design. `predicted_self` was measured later in C4 rather than manipulated, `style_prob_self` is only an 11-feature lightweight stylometric proxy, and the bootstrap intervals are descriptive uncertainty summaries for these cells rather than proof of a transportable mechanism.


## C1

| Dimension | c (total) | c' (direct) | a1·b1 (belief) | a2·b2 (style) | b1 | b2 |
|---|---:|---:|---:|---:|---:|---:|
| correctness | -0.047 [-0.158, +0.058] | +0.052 [-0.330, +0.350] | +0.045 [-0.122, +0.264] | -0.144 [-0.306, +0.015] | +0.116 [-0.330, +0.634] | -0.424 [-0.902, +0.046] |
| completeness | +0.119 [+0.025, +0.219] | +0.049 [-0.279, +0.310] | +0.227 [+0.057, +0.447] | -0.157 [-0.302, -0.032] | +0.583 [+0.159, +1.074] | -0.461 [-0.879, -0.092] |
| clarity | -0.133 [-0.347, +0.061] | -0.070 [-0.359, +0.188] | +0.035 [-0.046, +0.124] | -0.098 [-0.286, +0.033] | +0.090 [-0.114, +0.323] | -0.288 [-0.780, +0.100] |
| creativity | -0.136 [-0.383, +0.086] | -0.332 [-0.722, +0.008] | +0.195 [+0.077, +0.348] | +0.001 [-0.181, +0.168] | +0.500 [+0.212, +0.860] | +0.003 [-0.520, +0.485] |
| constraint_adherence | +0.217 [+0.061, +0.367] | +0.035 [-0.382, +0.387] | +0.358 [+0.161, +0.611] | -0.177 [-0.357, -0.003] | +0.921 [+0.467, +1.445] | -0.520 [-1.069, -0.009] |

## C2

| Dimension | c (total) | c' (direct) | a1·b1 (belief) | a2·b2 (style) | b1 | b2 |
|---|---:|---:|---:|---:|---:|---:|
| correctness | -0.061 [-0.206, +0.083] | -0.033 [-0.358, +0.248] | +0.055 [-0.107, +0.271] | -0.084 [-0.223, +0.036] | +0.142 [-0.290, +0.645] | -0.379 [-0.991, +0.159] |
| completeness | +0.031 [-0.103, +0.164] | -0.134 [-0.425, +0.111] | +0.258 [+0.084, +0.480] | -0.094 [-0.195, +0.001] | +0.663 [+0.250, +1.135] | -0.425 [-0.859, +0.004] |
| clarity | -0.419 [-0.619, -0.244] | -0.383 [-0.671, -0.137] | -0.004 [-0.083, +0.091] | -0.033 [-0.144, +0.077] | -0.009 [-0.218, +0.220] | -0.150 [-0.665, +0.327] |
| creativity | -0.244 [-0.500, -0.000] | -0.469 [-0.867, -0.119] | +0.160 [+0.036, +0.317] | +0.064 [-0.082, +0.215] | +0.412 [+0.101, +0.773] | +0.291 [-0.413, +0.905] |
| constraint_adherence | -0.081 [-0.236, +0.083] | -0.292 [-0.683, +0.042] | +0.339 [+0.140, +0.606] | -0.127 [-0.268, -0.006] | +0.871 [+0.404, +1.412] | -0.577 [-1.224, -0.025] |

## C3

| Dimension | c (total) | c' (direct) | a1·b1 (belief) | a2·b2 (style) | b1 | b2 |
|---|---:|---:|---:|---:|---:|---:|
| correctness | -0.058 [-0.164, +0.047] | +0.097 [-0.280, +0.390] | +0.033 [-0.133, +0.250] | -0.189 [-0.359, -0.022] | +0.086 [-0.353, +0.602] | -0.554 [-1.050, -0.063] |
| completeness | +0.119 [+0.022, +0.222] | +0.058 [-0.265, +0.321] | +0.232 [+0.058, +0.456] | -0.171 [-0.326, -0.037] | +0.596 [+0.158, +1.101] | -0.502 [-0.940, -0.114] |
| clarity | -0.342 [-0.531, -0.167] | -0.128 [-0.448, +0.156] | -0.034 [-0.122, +0.056] | -0.179 [-0.374, -0.026] | -0.088 [-0.299, +0.149] | -0.527 [-1.048, -0.075] |
| creativity | -0.117 [-0.336, +0.086] | -0.271 [-0.676, +0.078] | +0.176 [+0.055, +0.337] | -0.021 [-0.220, +0.177] | +0.452 [+0.150, +0.831] | -0.063 [-0.664, +0.500] |
| constraint_adherence | +0.078 [-0.061, +0.217] | -0.001 [-0.407, +0.345] | +0.320 [+0.128, +0.574] | -0.241 [-0.429, -0.052] | +0.822 [+0.361, +1.351] | -0.709 [-1.302, -0.152] |

## Headlines

- **Largest belief-channel indirect (|a1·b1|):**
  - C1 × constraint_adherence: +0.358 [+0.161, +0.611]
  - C2 × constraint_adherence: +0.339 [+0.140, +0.606]
  - C3 × constraint_adherence: +0.320 [+0.128, +0.574]
- **Largest style-channel indirect (|a2·b2|):**
  - C3 × constraint_adherence: -0.241 [-0.429, -0.052]
  - C3 × correctness: -0.189 [-0.359, -0.022]
  - C3 × clarity: -0.179 [-0.374, -0.026]
- **Sign opposition (belief positive, style negative) — cells where CI of belief excludes 0 above AND CI of style excludes 0 below:**
  - C1 × completeness: belief +0.227 [+0.057, +0.447]; style -0.157 [-0.302, -0.032]
  - C3 × completeness: belief +0.232 [+0.058, +0.456]; style -0.171 [-0.326, -0.037]
  - C1 × constraint_adherence: belief +0.358 [+0.161, +0.611]; style -0.177 [-0.357, -0.003]
  - C2 × constraint_adherence: belief +0.339 [+0.140, +0.606]; style -0.127 [-0.268, -0.006]
  - C3 × constraint_adherence: belief +0.320 [+0.128, +0.574]; style -0.241 [-0.429, -0.052]
- **Both channels POS (both CIs > 0):**
  - (none)

_Source: `analysis/subscale_horse_race.py`, generated D406._
