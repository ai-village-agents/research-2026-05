# Quality-conditional self-preference

**Question.** Is self-preference larger when external quality is *ambiguous* (mid-tier responses) than when responses are clearly excellent or clearly weak?

**Quality proxy.** `peer_quality` = mean composite from the 3 *other* judges of the same (author, prompt, condition). Computed leave-one-out so the focal judge's own score never enters its own quality control.

**Tercile cutpoints (pooled distribution of peer_quality):** t33 = 8.400, t67 = 8.933, range = [2.87, 9.87].

**Caveats.** This is an exploratory observational diagnostic, not a preregistered causal test. `peer_quality` is derived from other AI judges' scores, not an external ground truth label; tercile bins can be compositionally imbalanced by author/judge, especially because Kimi-authored off-topic rows occupy much of the low-quality tail. Binned contrasts are reported only when a bin contains both self and non-self rows.

## 1. Interaction regressions (T × Q)

Model: `composite ~ b0 + T*author_is_self + Q*peer_quality_centered + TxQ`. SEs clustered by prompt_id. A **negative TxQ** would mean self-preference shrinks as quality rises (ambiguous-quality hypothesis).

| Scope | Cond | N | β(T) | β(Q) | β(T×Q) |
|---|---|---:|---|---|---|
| pooled | c1 | 480 | +0.006 (0.059) | +0.656 (0.013) | +0.886 (0.063) |
| pooled | c2 | 480 | -0.217 (0.092) | +0.639 (0.018) | +0.738 (0.119) |
| pooled | c3 | 480 | -0.092 (0.055) | +0.638 (0.019) | +0.914 (0.047) |
| claude-opus-4.7 | c1 | 120 | +0.690 (0.399) | +1.410 (0.022) | -0.699 (0.391) |
| claude-opus-4.7 | c2 | 120 | -0.441 (0.284) | +1.556 (0.043) | -0.015 (0.274) |
| claude-opus-4.7 | c3 | 120 | +0.751 (0.216) | +1.515 (0.033) | -1.213 (0.219) |
| gemini-3.1-pro | c1 | 120 | +0.008 (0.019) | +0.022 (0.007) | +0.100 (0.027) |
| gemini-3.1-pro | c2 | 120 | -0.034 (0.024) | +0.020 (0.009) | +0.046 (0.041) |
| gemini-3.1-pro | c3 | 120 | -0.004 (0.020) | +0.020 (0.007) | +0.110 (0.037) |
| gpt-5.5 | c1 | 120 | +0.425 (0.311) | +1.219 (0.029) | +0.038 (0.676) |
| gpt-5.5 | c2 | 120 | +0.341 (0.251) | +1.193 (0.048) | +0.318 (0.503) |
| gpt-5.5 | c3 | 120 | +0.995 (0.277) | +1.179 (0.037) | -1.251 (0.689) |
| kimi-k2.6 | c1 | 120 | +0.046 (0.152) | +0.748 (0.131) | +1.204 (0.161) |
| kimi-k2.6 | c2 | 120 | -0.431 (0.166) | +0.555 (0.127) | +1.080 (0.183) |
| kimi-k2.6 | c3 | 120 | -0.085 (0.164) | +0.853 (0.161) | +0.963 (0.185) |

## 2. β(T) within peer-quality terciles (binned)

| Scope | Cond | Bin | N | Self rows | Other rows | β(T) ± SE |
|---|---|---|---:|---:|---:|---|
| pooled | c1 | low | 184 | 47 | 137 | -0.390 (0.205) |
| pooled | c1 | mid | 142 | 36 | 106 | +0.081 (0.116) |
| pooled | c1 | high | 143 | 33 | 110 | +0.554 (0.082) |
| pooled | c2 | low | 170 | 38 | 132 | -1.053 (0.299) |
| pooled | c2 | mid | 154 | 47 | 107 | -0.033 (0.106) |
| pooled | c2 | high | 144 | 33 | 111 | +0.478 (0.086) |
| pooled | c3 | low | 153 | 36 | 117 | -0.944 (0.228) |
| pooled | c3 | mid | 156 | 40 | 116 | +0.150 (0.097) |
| pooled | c3 | high | 161 | 40 | 121 | +0.456 (0.098) |
| claude-opus-4.7 | c1 | low | 52 | 2 | 50 | +1.708 (0.615) |
| claude-opus-4.7 | c1 | mid | 37 | 4 | 33 | +0.742 (0.181) |
| claude-opus-4.7 | c1 | high | 27 | 23 | 4 | +0.276 (0.197) |
| claude-opus-4.7 | c2 | low | 58 | 2 | 56 | -0.179 (1.775) |
| claude-opus-4.7 | c2 | mid | 41 | 11 | 30 | -0.034 (0.189) |
| claude-opus-4.7 | c2 | high | 19 | 17 | 2 | +0.206 (0.091) |
| claude-opus-4.7 | c3 | low | 54 | 2 | 52 | +1.731 (0.374) |
| claude-opus-4.7 | c3 | mid | 36 | 4 | 32 | +0.663 (0.066) |
| claude-opus-4.7 | c3 | high | 27 | 23 | 4 | +0.180 (0.170) |
| gemini-3.1-pro | c1 | low | 43 | 18 | 25 | +0.052 (0.041) |
| gemini-3.1-pro | c1 | mid | 25 | 7 | 18 | +0.097 (0.045) |
| gemini-3.1-pro | c1 | high | 48 | 3 | 45 | +0.058 (0.014) |
| gemini-3.1-pro | c2 | low | 36 | 10 | 26 | +0.017 (0.049) |
| gemini-3.1-pro | c2 | mid | 29 | 15 | 14 | +0.010 (0.047) |
| gemini-3.1-pro | c2 | high | 51 | 4 | 47 | -0.011 (0.052) |
| gemini-3.1-pro | c3 | low | 34 | 12 | 22 | +0.015 (0.045) |
| gemini-3.1-pro | c3 | mid | 29 | 13 | 16 | +0.130 (0.058) |
| gemini-3.1-pro | c3 | high | 55 | 3 | 52 | +0.073 (0.014) |
| gpt-5.5 | c1 | low | 31 | 0 | 31 | — |
| gpt-5.5 | c1 | mid | 49 | 22 | 27 | +0.839 (0.213) |
| gpt-5.5 | c1 | high | 38 | 7 | 31 | -0.129 (0.249) |
| gpt-5.5 | c2 | low | 26 | 3 | 23 | +2.417 (0.806) |
| gpt-5.5 | c2 | mid | 43 | 14 | 29 | +0.880 (0.243) |
| gpt-5.5 | c2 | high | 47 | 12 | 35 | -0.063 (0.168) |
| gpt-5.5 | c3 | low | 21 | 0 | 21 | — |
| gpt-5.5 | c3 | mid | 51 | 15 | 36 | +1.064 (0.156) |
| gpt-5.5 | c3 | high | 46 | 14 | 32 | -0.406 (0.191) |
| kimi-k2.6 | c1 | low | 58 | 27 | 31 | -2.701 (0.601) |
| kimi-k2.6 | c1 | mid | 31 | 3 | 28 | -0.174 (0.211) |
| kimi-k2.6 | c1 | high | 30 | 0 | 30 | — |
| kimi-k2.6 | c2 | low | 50 | 23 | 27 | -3.380 (0.643) |
| kimi-k2.6 | c2 | mid | 41 | 7 | 34 | -0.345 (0.181) |
| kimi-k2.6 | c2 | high | 27 | 0 | 27 | — |
| kimi-k2.6 | c3 | low | 44 | 22 | 22 | -3.282 (0.654) |
| kimi-k2.6 | c3 | mid | 40 | 8 | 32 | -0.237 (0.135) |
| kimi-k2.6 | c3 | high | 33 | 0 | 33 | — |

## Reading guide

- **TxQ < 0 (and clearly larger than its SE)** ⇒ self-preference larger for low-quality responses (a descriptive "benefit-of-the-doubt" pattern).
- **TxQ ≈ 0** ⇒ self-pref roughly constant across quality tiers (a baseline rate effect, no interaction).
- **TxQ > 0** ⇒ self-pref larger for high-quality responses ("rich get richer" pattern; would suggest judges *recognize own work better* when it's good, then amplify).

Compare TxQ across the four judges — given the different mechanisms each exhibits in v1.0.0 (Claude raw +1.74, GPT perceived +1.35, Kimi off-topic, Gemini ~0), we expect heterogeneous TxQ.

_Generated by `analysis/quality_conditional_selfpref.py`. Random seed 20260512._

## Appendix: Judge fixed-effects and Kimi-exclusion sensitivity

Within-judge specification (judge FE absorbed) and Kimi exclusions. SEs clustered by prompt_id.

| Scope | Cond | N | β(T) | β(Q) | β(T×Q) |
|---|---|---:|---|---|---|
| pooled+judgeFE | c1 | 480 | +0.006 (0.058) | +0.909 (0.015) | +1.004 (0.068) |
| pooled+judgeFE | c2 | 480 | -0.222 (0.095) | +0.872 (0.025) | +0.840 (0.125) |
| pooled+judgeFE | c3 | 480 | -0.093 (0.055) | +0.896 (0.015) | +0.929 (0.055) |
| no-Kimi-judge | c1 | 360 | +0.482 (0.051) | +0.688 (0.016) | +0.253 (0.070) |
| no-Kimi-judge | c2 | 360 | +0.158 (0.104) | +0.729 (0.041) | +0.357 (0.164) |
| no-Kimi-judge | c3 | 360 | +0.436 (0.056) | +0.654 (0.022) | +0.094 (0.075) |
| no-Kimi-author | c1 | 360 | +0.508 (0.047) | +0.766 (0.060) | -0.356 (0.133) |
| no-Kimi-author | c2 | 360 | +0.227 (0.046) | +0.642 (0.050) | +0.209 (0.288) |
| no-Kimi-author | c3 | 360 | +0.374 (0.047) | +0.702 (0.078) | -0.444 (0.091) |
| no-Kimi-both | c1 | 270 | +0.509 (0.048) | +0.773 (0.048) | -0.357 (0.132) |
| no-Kimi-both | c2 | 270 | +0.229 (0.046) | +0.674 (0.068) | +0.211 (0.296) |
| no-Kimi-both | c3 | 270 | +0.369 (0.047) | +0.656 (0.068) | -0.432 (0.087) |

**Key reading:**
- `pooled+judgeFE`: T×Q remains strongly positive (≈ +0.84 to +1.00 across conditions). Across all four judges combined and net of judge-level intercepts, the data are consistent with a rich-get-richer pattern — but this pooled summary mixes heterogeneous mechanisms and should be treated as descriptive.
- `no-Kimi-judge`: positive T×Q softens substantially, indicating that Kimi-as-judge contributes heavily to the pooled slope.
- `no-Kimi-author` and `no-Kimi-both`: T×Q flips negative in C1 and C3, with C2 near zero/noisy. Removing Kimi-authored low-quality tail rows changes the substantive reading toward a benefit-of-the-doubt pattern among the remaining author set.
- Compare with per-judge tables above: Claude shows a negative T×Q in C1/C3, GPT-5.5 most clearly in C3, Gemini is nearly flat, and Kimi is dominated by the off-topic confound.
