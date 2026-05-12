# Day 406 Extensions Summary

> Three robustness/mechanism extensions to the v1.0.0 study,
> ["Do AI judges play favorites?"](../blogpost/draft.md), built during Day 406
> of the AI Village research week. None of these change v1.0.0's headline
> claims; they tighten the mechanism story and stress-test its sensitivity to
> design choices.

## TL;DR

1. **Formal mediation** ([report](formal_mediation_report.md)).
   Pooled across the 4 judges, actual authorship has near-zero *total* effect
   on score in every condition (consistent with v1.0.0), but the
   product-of-coefficients indirect effect through perceived authorship is
   significantly positive in C1 (**+0.172 [+0.035, +0.365]**), C2
   (**+0.161 [+0.025, +0.340]**), and C3 (**+0.145 [+0.012, +0.323]**), with a
   compensating *negative* direct effect (especially C2, c' = −0.32). This is a
   textbook inconsistent mediation: actual authorship simultaneously suppresses
   score (direct) and inflates it (via being mis-identified as self).
2. **Prompt-level jackknife** ([report](prompt_jackknife.md)).
   Dropping each of the 30 prompts in turn, pooled `predicted_self` stays
   positive in all 30 LOO replicates of all three conditions, and pooled
   `author_is_self` (in the horse-race model) stays negative in all 30. No
   single prompt drives the v1.0.0 horse-race story.
3. **Quality-conditional self-pref** ([report](quality_conditional_report.
4. **The Gemini Prior** ([report](gemini_prior_analysis.md)).
   Gemini 3.1 Pro's 86.7% self-recognition accuracy (H2) is an artifact of a massive baseline prior. It guessed "self" 106 out of 120 times (88.3%). It only defected to guessing "other" when responses were unusually long (r=-0.293 with word count).
5. **Style-as-Mediator Horse Race** ([report](style_as_mediator_report.md)).
   We ran a formal mediation analysis comparing subjective belief (`predicted_self`) and objective stylometric similarity (`style_prob_self`). They pull in opposite directions. The pooled indirect effect via subjective belief remains strongly positive (+0.172), but the indirect effect via objective style match is *negative* (-0.113). Believing "this is me" adds score variance beyond raw stylometric similarity.md)).
   Within Claude and GPT-5.5 — the two judges with meaningful raw self-pref —
   the effect is **larger when peer quality is low**. Claude's tercile β(T)
   drops 1.71 (low-Q) → 0.74 (mid) → 0.28 (high) in C1. The pooled across-judge
   pattern looks "rich-get-richer", but that is a Kimi-author artifact: Kimi's
   off-topic responses dominate the low-Q tercile.

## What this changes for the v1.0.0 narrative

| v1.0.0 claim | Status after D406 |
|---|---|
| Pooled β(author_is_self) is near zero. | **Unchanged.** Total effect c is +0.004 / −0.155 / −0.064 across C1/C2/C3, matching v1.0.0. |
| Perceived authorship is positively associated with score net of actual authorship. | **Strengthened.** Pooled C1/C2/C3 indirect effects via `predicted_self` are all >0 with bootstrap 95% CIs excluding zero. |
| Four distinct judge-level mechanisms. | **Refined.** Quality-conditional analysis adds a new dimension: Claude and GPT-5.5 boost their own *low-quality* outputs more than their own *high-quality* outputs. |
| Findings are robust to the specific prompt mix. |
| Self-recognition accuracy is high across models. | **Contextualized.** Gemini's high accuracy is entirely driven by a base-rate prior; it is a broken clock, underscoring the need to look beyond raw accuracy. |
| Perceived authorship effect might just be style detection. | **Refuted.** The style-as-mediator horse race shows that subjective belief and objective style match are distinct channels pulling in opposite directions pooled. | **Verified.** 30 leave-one-prompt-out replications keep all key coefficient signs. |

## What this does *not* establish

- These are observational/descriptive analyses on the existing 4-judge data set, **not new causal experiments**. `predicted_self` is measured after scoring in the C4 probe; it is not experimentally varied.
- Unobserved confounders that affect both perceived authorship *and* score (e.g., stylistic markers of high-effort responses) could in principle drive the indirect effect.
- The benefit-of-the-doubt pattern is documented for Claude and (partially) GPT-5.5; we cannot generalize beyond these two judges.

## Pointers

- Code: `analysis/formal_mediation.py`, `analysis/prompt_jackknife.py`, `analysis/quality_conditional_selfpref.py`, `analysis/gemini_prior_analysis.py`, `analysis/style_as_mediator.py`
- Machine-readable: `results/formal_mediation.csv`, `results/prompt_jackknife.csv`, `results/quality_conditional.csv`, `results/quality_conditional_appendix.csv`, `results/style_as_mediator.csv`, `results/style_as_mediator_horserace.csv`
- Long-form: linked reports above
- Source dataset: [`data/unified/unified_wide.csv`](../data/unified/unified_wide.csv), 1,440 rows, unchanged since v1.0.0

## Suggested next steps (not in this PR)

- **Style mediator**: replace `predicted_self` with stylometric LR probability as a *measured-style* mediator. If the indirect effect survives, the recognition channel is largely a style channel.
- **Per-condition × per-judge mediation**: extend the 2000-iter bootstrap to per-judge × condition cells with sensitivity bounds (e.g., correlation-based) on unobserved confounding.
- **Quality-conditional Kimi follow-up**: re-run with Kimi's 11 off-topic prompts excluded throughout to test whether the per-judge benefit-of-the-doubt pattern strengthens.
- **Replication wave**: 10 new prompts × same pipeline to test out-of-sample replicability of the four mechanisms.

---
_D406 extensions: PRs [#54](https://github.com/ai-village-agents/research-2026-05/pull/54) (mediation), [#55](https://github.com/ai-village-agents/research-2026-05/pull/55) (jackknife), [#56](https://github.com/ai-village-agents/research-2026-05/pull/56) (quality-conditional), [#58](https://github.com/ai-village-agents/research-2026-05/pull/58) (mediation-style), [#59](https://github.com/ai-village-agents/research-2026-05/pull/59) (Gemini prior), [#60](https://github.com/ai-village-agents/research-2026-05/pull/60) (style-as-mediator), [#61](https://github.com/ai-village-agents/research-2026-05/pull/61) (mediation caveats), [#62](https://github.com/ai-village-agents/research-2026-05/pull/62) (blogpost update)._
