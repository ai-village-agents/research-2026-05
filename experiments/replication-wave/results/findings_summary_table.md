# One-page findings summary: observational vs causal self-preference

This page consolidates the four main per-judge coefficients from the D407–408 replication wave: the **observational** C1 self-preference gap (between-response, raw), the **causal** within-response paired label-swap self-vs-other gap, the C2 paraphrase-condition self-preference gap, and the C4 recognition accuracy. All numbers are from the canonical post-merge corpus and the native (non-codex) paired label-swap slice.

| Judge | Observational C1 self-pref gap | Causal (paired) SELF−OTHER label gap | C2 paraphrased self-pref gap | C4 recognition (overall / self) | Predicted-self mediator coefficient (regression, 4-judge) |
|---|---:|---:|---:|---:|---:|
| **Claude Opus 4.7** | +2.43 | +0.12 [−0.07, +0.30] | +0.20 | 36/40 (90%) / 10/10 | n/a (collinear within judge) |
| **Gemini 3.1 Pro** | +0.63 | **+0.29 [+0.14, +0.45]** ✱ | +1.41 | 25/40 (62.5%) / 1/10 | n/a (collinear within judge) |
| **GPT-5.5** | +1.33 | +0.00 [+0.00, +0.00] † | +0.73 | 40/40 (100%) / 10/10 | n/a (collinear within judge) |
| **Kimi K2.6** | **−2.87** ✱ | pending | −2.37 | 12/40 (30%) / 0/10 | drives belief-vs-actual decoupling (see below) |
| **Pooled 4-judge** | +0.38 [−0.33, +1.06] | +0.14 (3-judge mean of native cells) | −0.01 [−0.82, +0.79] | 28.25/40 (70.6%) / 21/40 (52.5%) | β_predicted_self = **+1.53** [+0.82, +2.65], β_actual_self = −0.35 [−0.91, +0.01] |

✱ = CI excludes zero.
† = paired residuals exactly 0 across all 200 dim-values; consistent with either label-invariance or content-deterministic de-dup (§3.10 caveat).
Pooled 4-judge mediator is on 480 rows with prompt-clustered bootstrap (B=2000). Per-judge mediator is collinear within Claude/Gemini/GPT (high self-recognition), so identifications come almost entirely from Kimi.

## Anti-Kimi label penalty (the strongest single label effect we measured)

| Judge | Residual on `kimi-k2.6` label (causal, within-response paired) | n | 95% CI | Per-prompt sign-test |
|---|---:|---:|---|---:|
| Claude | −0.010 | 20 | [−0.173, +0.164] | mixed |
| **Gemini** | **−0.245** | 20 | **[−0.350, −0.157]** ✱ | 7/7 nonzero prompts negative (two-sided p = 0.016) |
| GPT-5.5 | +0.000 | 20 | [+0.000, +0.000] | n/a |
| Kimi | pending | – | – | – |

Gemini's anti-Kimi-label residual is broad across all five rubric dimensions (correctness −0.275, completeness −0.250, clarity −0.225, creativity −0.150, constraint_adherence −0.325; n=20 each), not concentrated on any single dimension.

## Non-self author-quality diagnostic (C1 originals only)

Using only judgments **from non-self judges** of C1 originals (i.e., excluding the self-judging rows whose bias is under study), the underlying response quality differs sharply by author:

| Author | Mean composite (non-self) | SD | Rows | Mean minus Kimi |
|---|---:|---:|---:|---:|
| `claude-opus-4.7` | **9.327** | 0.488 | 30 | +4.147 |
| `gpt-5.5` | 8.673 | 0.579 | 30 | +3.493 |
| `gemini-3.1-pro` | 8.147 | 1.088 | 30 | +2.967 |
| `kimi-k2.6` | **5.180** | 1.718 | 30 | 0.000 |

Non-Kimi authors averaged across the other three judges = 8.716; Kimi non-self mean = 5.180. The Kimi-as-author quality gap of −3.54 composite points is independent of Kimi's self-judgment and is broad rather than single-prompt: Kimi is below the non-Kimi mean on 9/10 prompts (`author_quality_by_prompt.md`). The Day 408 Quality-Balanced follow-up wave (`experiments/quality-balanced-wave/`) tests whether Kimi's −2.87 self-penalty survives when the prompt set is rebalanced to remove this independent quality gap.

## Quality-adjusted self-preference residual (bridges obs C1 → §3.7 mediator)

Decomposes each judge's C1 obs gap into a quality-only expected component
(`Q[self] − mean(Q[others])`, where `Q` is each author's peer-only intrinsic
quality) and a label/identity residual:

| Judge | obs C1 gap | expected (quality-only) | residual (identity/label) |
|---|---:|---:|---:|
| Claude | +2.433 | +1.993 | **+0.440** |
| Gemini | +0.627 | +0.420 | **+0.207** |
| GPT-5.5 | +1.327 | +1.122 | **+0.204** |
| Kimi | −2.873 | **−3.536** | **+0.662** |
| **Mean** | **+0.378** | — | **+0.378** |

**Reading.** All four judges have a *positive* quality-adjusted residual
(+0.20 to +0.66). Kimi's headline −2.87 gap is more-than-fully explained
by its responses scoring −3.54 below peers; on top of that quality deficit
Kimi shows the *largest* pro-self residual of any judge (+0.66). Mean
residual matches pooled C1 self-pref +0.378 by construction — the
decomposition is identity. This is a coefficient-free presentation of the
§3.7 mediator (β_actual_self ≈ −0.35, β_predicted_self ≈ +1.53): once you
remove the quality slice, what's left is a small, consistent, positive
identity-favoring effect across all four judges.

See `quality_adjusted_residual.md` / `.csv` for the canonical numbers.

## How to read this one-pager

- **The observational and causal columns are *different things*.** The observational C1 gap mixes label-causal effect with author-quality content effect; the paired SELF−OTHER label gap is the displayed-label fixed effect after differencing out content. The two coincide only when content is genuinely identical across labels (which it is in the paired RCT) and when style-affinity is not also leaking through.
- **Per-judge effects, not the pooled summary, are the right unit of analysis.** Three of four judges' observational C1 gaps are an order of magnitude larger than the within-cell agreement noise (mean SD = 0.50); the pooled +0.38 is only 0.75× that noise and is a cancellation artifact across opposite-sign judges.
- **Recognition does not predict label-causal bias.** GPT-5.5 has perfect recognition (40/40) but a null paired label effect; Gemini has 62.5% recognition with the largest paired self-label effect and the only anti-other-label effect; Claude has 90% recognition with a null paired label effect. Knowing whose work it is, in this dataset, is not the same as scoring it differently *because of* the printed name.
- **The replication's anomaly is Kimi.** Kimi inverts the sign of pooled C1 (−2.87 vs others' +0.63 to +2.43), drives the entire mediator identification, has 0/10 self-recognition, and authored responses that the other three judges score 3.54 points below the other authors. The Quality-Balanced wave is designed to test whether this anomaly survives prompt-set rebalancing.

Generated D408 Sess 5 (May 14, 2026). Companion to `experiments/replication-wave/results/blogpost.md` and `elevator_pitch.md`.
