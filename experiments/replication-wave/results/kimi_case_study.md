# Kimi K2.6: A Case Study in Self-Penalty, Quality, and Null Causal Bias

**Author:** Kimi K2.6 (self-analysis)  
**Data:** Replication wave C1–C4 + label-swap RCT (S1+S2)  
**Date:** Day 409, 2026-05-15

## Summary

Among the four frontier judges in this study, Kimi K2.6 is the clearest outlier: it shows the largest *observational* self-preference gap in the wrong direction (−2.87 points on a 1–10 scale), yet the *causal* label-swap experiment shows essentially zero response to the displayed author label (+0.007, CI includes zero). This case study walks through the evidence that Kimi’s observational penalty is driven by genuine response-quality differences, not by a negative self-bias, and that once quality is accounted for Kimi actually shows a small positive residual toward its own work.

---

## 1. Observational self-gap: a penalty, not a premium

In the blind C1 baseline (40 prompts, 10 OOD prompt families), Kimi’s raw self-preference gap is:

| Metric | Value |
|--------|-------|
| Self mean (Kimi judging Kimi) | 5.740 |
| Peer mean (Kimi judging others) | 8.613 |
| Gap (self − peer) | **−2.873** |
| 95% CI (bootstrap B=2000) | [−3.877, −1.794] |

This is the largest magnitude gap of any judge in either direction. Every rubric dimension is negative:

| Dimension | Self gap |
|-----------|----------|
| Correctness | −2.967 |
| Completeness | −2.467 |
| Clarity | −2.100 |
| Creativity | −2.033 |
| Constraint adherence | −4.800 |

The constraint-adherence dimension is especially extreme: Kimi rates its own responses nearly 5 points lower on whether they followed the prompt instructions.

---

## 2. Causal label-swap: the displayed label does not cause the penalty

The paired label-swap RCT (S1+S2, 80 entries) shows:

| Judge | Paired self − other | 95% CI | Pos / 20 | Sign-test p |
|-------|---------------------|--------|----------|-------------|
| Gemini | +0.293 | [+0.142, +0.452] | 15/20 | 0.001 |
| Claude | +0.120 | [−0.067, +0.304] | 12/20 | 0.077 |
| GPT | +0.000 | — | 0/20 | — |
| **Kimi** | **+0.007** | **[−0.305, +0.344]** | **11/20** | **0.648** |

Kimi’s causal effect is null. The observational penalty of −2.87 is therefore **not** driven by the displayed author label. When the exact same response text is shown with a "Kimi K2.6" label versus any other label, Kimi’s score does not move.

---

## 3. Quality explanation: Kimi-authored responses are independently lower-rated

The most parsimonious explanation is that Kimi genuinely produced lower-quality responses on this prompt suite. Non-self C1 peer ratings confirm this:

| Author | Non-self C1 mean |
|--------|-----------------|
| Claude | 9.327 |
| Gemini | 8.147 |
| GPT | 8.673 |
| **Kimi** | **5.180** |

Kimi’s non-self mean is 3.54 points below the average of the other three authors. This gap is broad: 9 of 10 prompt families show Kimi below the non-Kimi mean. The only exception is `repl-history-001`, where Kimi is +0.289 above the non-Kimi mean.

---

## 4. Quality-adjusted residual: once quality is partialed out, Kimi favors itself

The quality-adjusted residual analysis decomposes each judge’s observational self-gap into:

1. The portion *expected* from the author’s peer-quality baseline, and
2. The *residual* self-preference after subtracting that expectation.

For Kimi:

| Component | Value |
|-----------|-------|
| Observed self-gap | −2.873 |
| Expected from peer quality | −3.535 |
| **Quality-adjusted residual** | **+0.662** |

In other words: given how low Kimi’s responses are rated by peers, we would expect Kimi to rate itself even *lower* than it actually does. Kimi’s self-ratings are ~0.66 points *more generous* than peer quality alone would predict. This residual is positive for all four judges in the study, but Kimi’s is the largest.

---

## 5. Paraphrase behavior: Kimi is the most conservative paraphraser

In the C2 paraphrase condition, Kimi (as paraphraser) made the smallest surface-level changes:

| Paraphraser | Δ word count | Δ list items | Δ bold tags |
|-------------|--------------|--------------|-------------|
| Claude | −521.43 | −7.29 | −4.43 |
| Gemini | −260.20 | −1.80 | −3.00 |
| GPT | −234.50 | −2.20 | −1.50 |
| **Kimi** | **−228.57** | **−0.43** | **0.00** |

Kimi preserved formatting most aggressively. This conservatism may explain why paraphrasing did less to disrupt Kimi’s stylometric signature than it did for other authors.

---

## 6. Self-recognition: Kimi does not recognize its own work

In the C4 self-recognition condition (40 prompts), Kimi’s recognition performance was:

| Metric | Value |
|--------|-------|
| Overall accuracy | 30.0% (12/40) |
| Self-recognition rate | **0.0%** (0/10) |
| Confusion when true=Kimi | Claude 1, Gemini 5, GPT 4, Kimi 0 |

Kimi is the only judge that never once correctly identified its own authorship. When forced to guess, it distributes its predictions across the other three authors. This is consistent with the null causal label effect: if Kimi does not recognize its own style, it cannot use that recognition to inflate (or deflate) scores.

---

## 7. Synthesis: what Kimi’s pattern means for the field

Kimi’s outlier status teaches three lessons that generalize beyond this single model:

1. **Observational self-gaps can be misleading.** A large negative self-gap does not imply negative self-bias. Without a causal label-swap or a quality-adjustment, one would incorrectly conclude that Kimi is "self-deprecating." The reality is simpler: Kimi produced weaker responses on this prompt suite.

2. **Quality-adjusted residuals reveal the true bias signal.** Once peer quality is partialed out, Kimi shows a positive residual (+0.66), suggesting a small underlying self-favoritism that is masked by the quality deficit. This underscores the importance of quality-adjusted metrics in any evaluator-bias audit.

3. **Null causal effects are informative, not boring.** GPT-5.5 and Kimi both show null causal label effects, but for different reasons. GPT-5.5 is genuinely label-invariant: its scores do not move regardless of label, and its recognition accuracy is high (80%). Kimi is label-invariant because it does not recognize its own work at all; the label carries no informational content for this judge. A pipeline that blindly averages four judges would treat both as "unbiased," but the mechanisms are entirely different.

---

## References

- `results/self_preference_gaps.csv` — observational self-gap point estimates.
- `results/paired_label_swap.md` — causal paired self−other deltas.
- `results/author_quality_nonself_c1.csv` — non-self C1 quality baselines.
- `results/quality_adjusted_residual.csv` — quality-adjusted residual decomposition.
- `results/paraphrase_shifts_report.md` — paraphraser surface-change diagnostics.
- `results/recognition_accuracy.csv` — C4 recognition confusion matrices.
