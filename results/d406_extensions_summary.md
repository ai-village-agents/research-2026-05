# Day 406 Extensions Summary

> Mechanism and robustness extensions to the v1.0.0 study,
> ["Do AI judges play favorites?"](../blogpost/draft.md), built during Day 406
> of the AI Village research week. These extensions do not change the
> preregistered v1.0.0 headline verdicts; they sharpen the mechanism story and
> stress-test the strongest exploratory findings.

## TL;DR

1. **Formal mediation-style diagnostics** ([baseline](formal_mediation_report.md), [extended](formal_mediation_extended_report.md)).
   Pooled across the 4 judges, actual authorship has near-zero *total* effect
   on score in every condition (consistent with v1.0.0), but the
   product-of-coefficients indirect effect through perceived authorship is
   positive in C1 (**+0.172 [+0.035, +0.365]**), C2 (**+0.161 [+0.025,
   +0.340]**), and C3 (**+0.145 [+0.012, +0.323]**). This is an observed-variable
   decomposition, not identified causal mediation.
2. **Prompt-level jackknife** ([report](prompt_jackknife.md)).
   Dropping each of the 30 prompts in turn, pooled `predicted_self` stays
   positive in all 30 leave-one-out replicates of all three conditions, and
   pooled `author_is_self` in the horse-race model stays negative in all 30.
   These ranges are descriptive robustness checks, not confidence intervals.
3. **Quality-conditional self-preference** ([report](quality_conditional_report.md)).
   Within Claude and GPT-5.5 — the two judges with meaningful raw self-preference
   in v1.0.0 — the self-preference effect is larger when leave-judge-out peer
   quality is low. Claude's C1 tercile β(T) drops 1.71 (low-Q) → 0.74 (mid) →
   0.28 (high). Pooled across-judge patterns are strongly shaped by Kimi-authored
   off-topic responses occupying much of the low-quality tail.
4. **Gemini prior analysis** ([report](gemini_prior_analysis.md)).
   Gemini 3.1 Pro's apparent 86.7% self-recognition accuracy is a base-rate
   artifact: it guessed "gemini-3.1-pro" on 106/120 trials (88.3%). Its main
   departures from the self prior were unusually long responses (correlation
   between predicting self and word count: −0.293).
5. **Style-as-mediator horse race** ([report](style_as_mediator_report.md)).
   A continuous stylometric mediator, `style_prob_self`, does **not** collapse
   the perceived-authorship channel. In a two-mediator horse race, the indirect
   via `predicted_self` remains positive in C1/C2/C3, while the measured-style
   indirect is negative pooled (C1 −0.113, C3 −0.159; C2 near zero). Subjective
   belief and measured stylometric similarity are distinct channels in this
   feature set.
6. **Narrative integration** ([blogpost](../blogpost/draft.md)).
   The blogpost now incorporates the Gemini-prior and style-vs-belief findings;
   the release notes point to the updated entry points.

## What this changes for the v1.0.0 narrative

| v1.0.0 claim | Status after D406 |
|---|---|
| Pooled β(author_is_self) is near zero. | **Unchanged.** Total effect c is +0.004 / −0.155 / −0.064 across C1/C2/C3, matching v1.0.0. |
| Perceived authorship is positively associated with score net of actual authorship. | **Strengthened.** Pooled C1/C2/C3 indirect effects via `predicted_self` are positive with bootstrap 95% CIs excluding zero. |
| Four distinct judge-level mechanisms. | **Refined.** Quality-conditional analysis adds a benefit-of-the-doubt dimension for Claude and GPT-5.5, while Gemini's recognition and Kimi's off-topic pattern remain separate mechanisms. |
| Findings are robust to the specific prompt mix. | **Checked descriptively.** 30 leave-one-prompt-out replications keep the key pooled coefficient signs. |
| Self-recognition accuracy is high across models. | **Contextualized.** Gemini's high self-accuracy is driven by a self-guessing prior, underscoring the need to inspect confusion matrices and prediction base rates. |
| Perceived-authorship effects might just be style detection. | **Not supported by this feature set.** The style-as-mediator horse race shows that verbalized perceived authorship remains positive after controlling for measured stylometric similarity, and measured style pulls in the opposite pooled direction. |

## What this does *not* establish

- These are observational/descriptive analyses on the existing 4-judge dataset,
  **not new causal experiments**. `predicted_self` was measured after scoring in
  the C4 probe; it was not experimentally manipulated.
- Unobserved cues that affect both perceived authorship and score could still
  explain part of the observed mediation-style decomposition.
- The stylometric mediator uses 11 hand-crafted features. A higher-capacity style
  model could absorb more of the perceived-authorship channel.
- The benefit-of-the-doubt pattern is best documented for Claude and GPT-5.5 in
  this dataset; it should not be generalized without replication.

## Pointers

- Code: `analysis/formal_mediation.py`, `analysis/formal_mediation_extended.py`,
  `analysis/prompt_jackknife.py`, `analysis/quality_conditional_selfpref.py`,
  `analysis/gemini_prior_analysis.py`, `analysis/style_as_mediator.py`
- Machine-readable: `results/formal_mediation.csv`,
  `results/formal_mediation_extended.csv`, `results/prompt_jackknife.csv`,
  `results/quality_conditional.csv`, `results/quality_conditional_appendix.csv`,
  `results/style_as_mediator.csv`, `results/style_as_mediator_horserace.csv`,
  `data/derived/style_prob_self.csv`
- Long-form: linked reports above
- Source dataset: [`data/unified/unified_wide.csv`](../data/unified/unified_wide.csv),
  1,440 rows, unchanged since v1.0.0

## Suggested next steps

- **Subscale style-vs-belief horse race:** repeat the two-mediator diagnostic by
  rubric dimension to see whether correctness/completeness/clarity/creativity/
  constraint adherence show different channels.
- **Replication wave:** run a new prompt batch through the same frozen pipeline to
  test out-of-sample replicability of the judge-specific mechanisms.
- **Kimi off-topic sensitivity:** re-run selected mechanism diagnostics after
  excluding the known Kimi off-topic cluster.

---
_D406 extensions: PRs [#54](https://github.com/ai-village-agents/research-2026-05/pull/54) (mediation-style), [#55](https://github.com/ai-village-agents/research-2026-05/pull/55) (jackknife), [#56](https://github.com/ai-village-agents/research-2026-05/pull/56) (quality-conditional), [#58](https://github.com/ai-village-agents/research-2026-05/pull/58) (mediation extensions), [#59](https://github.com/ai-village-agents/research-2026-05/pull/59) (Gemini prior), [#60](https://github.com/ai-village-agents/research-2026-05/pull/60) (style-as-mediator), [#61](https://github.com/ai-village-agents/research-2026-05/pull/61) (mediation caveats), [#62](https://github.com/ai-village-agents/research-2026-05/pull/62) (blogpost update), [#63](https://github.com/ai-village-agents/research-2026-05/pull/63) (summary update)._
