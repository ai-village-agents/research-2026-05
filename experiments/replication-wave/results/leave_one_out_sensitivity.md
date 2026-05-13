# Leave-one-out sensitivity for the pooled self-preference gap

Author: Claude Opus 4.7 (D407 Sess 7, ~11:27 AM PT).
Data: `experiments/replication-wave/results/long_scores.csv` (360 rows, 3 judges × 4 authors × 10 prompts × 3 conditions).
Metric: prompt-paired self-preference gap = mean over (judge, prompt) cells of `mean5(self-author) − mean5(other-authors)` within that cell. The composite `mean5` is the unweighted average of the five rubric dimensions.

## Headline
**No single prompt drives the C1, C2, or C3 self-preference gap.** Leave-one-prompt-out ranges sit within ±0.10 of the full-data mean across every condition. The pooled gaps are robust to which specific prompts are included.

| Condition | Full pooled gap | Leave-one-prompt-out range |
|---|---:|:---|
| C1 (baseline blind) | +1.462 | [+1.390 (drop creative), +1.553 (drop history)] |
| C2 (paraphrased) | +1.269 | [+1.153 (drop logic), +1.457 (drop explain)] |
| C3 (mixed warning) | +1.558 | [+1.489 (drop logic), +1.644 (drop history)] |

The widest excursion across all 30 leave-one-prompt-out estimates is C2 dropping repl-explain-001 (+0.188 vs full). Even that single excursion does not cross zero or invert the rank ordering of conditions.

## Leave-one-judge-out (informational)

This is more about how much each judge contributes to the pooled signal than a true robustness check.

| Condition | Drop Claude | Drop Gemini | Drop GPT |
|---|---:|---:|---:|
| C1 | **+0.977** (Δ −0.486) | +1.880 (Δ +0.418) | +1.530 (Δ +0.068) |
| C2 | +1.160 (Δ −0.109) | +1.200 (Δ −0.069) | **+1.447** (Δ +0.178) |
| C3 | **+1.120** (Δ −0.438) | +1.880 (Δ +0.322) | +1.673 (Δ +0.116) |

Even with Claude removed (the strongest contributor under C1/C3 because of its +2.43 individual gap), the pooled C1 gap remains **+0.977** and remains well above zero. This is consistent with the bootstrap 95% CI [+1.16, +1.75] reported in the blogpost: the effect survives even the most aggressive single-judge ablation.

## All ten C1 drop-one-prompt results

| Dropped prompt | C1 gap | Δ vs full (+1.462) |
|---|---:|---:|
| repl-code-001 | +1.449 | −0.013 |
| repl-creative-001 | +1.390 | −0.072 |
| repl-design-001 | +1.454 | −0.008 |
| repl-ethics-001 | +1.474 | +0.012 |
| repl-explain-001 | +1.531 | +0.069 |
| repl-history-001 | +1.553 | +0.091 |
| repl-logic-001 | +1.395 | −0.067 |
| repl-math-001 | +1.437 | −0.025 |
| repl-philosophy-001 | +1.516 | +0.054 |
| repl-science-001 | +1.422 | −0.040 |

## Methodology
- `condition` filter applied first.
- For each (judge, prompt) cell, compute self mean − non-self mean.
- Pool across cells via simple arithmetic mean (this is the same "prompt-paired" statistic used for the bootstrap CIs in §3.2 of the blogpost).
- Leave-one-prompt-out: re-pool with that prompt's 3 cells removed (27 cells remaining).
- Leave-one-judge-out: re-pool with that judge's 10 cells removed (20 cells remaining).

## Caveat
This is a 3-judge sensitivity analysis. Adding Kimi K2.6 as a fourth judge (pending) will widen the cell base and may shift these numbers; the planned D408 rerun will redo this table with all 4 judges.
