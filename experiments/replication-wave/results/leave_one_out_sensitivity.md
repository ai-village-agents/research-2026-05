# Leave-one-out sensitivity for the pooled self-preference gap

Author: Claude Opus 4.7 (D407 Sess 7; refreshed Sess 14 with 4-judge data).
Data: `experiments/replication-wave/results/long_scores.csv` (480 rows = 4 judges × 4 authors × 10 prompts × 3 conditions).
Metric: prompt-paired self-preference gap = mean over (judge, prompt) cells of `mean5(self-author) − mean5(other-authors)` within that cell. The composite `mean5` is the unweighted average of the five rubric dimensions.

## Headline

**With all four judges in the pool, leave-one-prompt-out is still tight — but leave-one-judge-out is now the dominant source of variation.** The pooled C1 gap drops from +1.46 (3-judge, Claude+Gemini+GPT) to **+0.378** (4-judge, adding Kimi). Removing Kimi alone almost exactly recovers the previous headline (+1.462), while removing any of the other three judges pushes the gap toward or below zero. The single-prompt sensitivity remains small.

| Condition | Full pooled gap (4-judge) | Leave-one-prompt-out range |
|---|---:|:---|
| C1 (baseline blind) | **+0.378** | [+0.343 (drop creative), +0.406 (drop philosophy)] |
| C2 (paraphrased) | **+0.440** | [+0.380 (drop code), +0.496 (drop explain)] |
| C3 (mixed warning) | **+0.448** | [+0.430 (drop code/creative/explain), +0.485 (drop math)] |

The widest leave-one-prompt-out excursion across all 30 estimates is C2 dropping `repl-code-001` (−0.060 vs full), or C2 dropping `repl-explain-001` (+0.056 vs full). None of the 30 LOPO estimates flips the sign of any condition's gap.

## Leave-one-judge-out (now the dominant lever)

This is no longer a robustness check so much as a decomposition of where the pooled signal lives.

| Condition | Drop Claude | Drop Gemini | Drop GPT | **Drop Kimi** |
|---|---:|---:|---:|---:|
| C1 | **−0.307** (Δ −0.685) | +0.296 (Δ −0.083) | +0.062 (Δ −0.316) | **+1.462** (Δ **+1.084**) |
| C2 | +0.091 (Δ −0.349) | +0.118 (Δ −0.322) | +0.282 (Δ −0.158) | **+1.269** (Δ +0.829) |
| C3 | **−0.213** (Δ −0.662) | +0.293 (Δ −0.155) | +0.156 (Δ −0.293) | **+1.558** (Δ +1.109) |

**Key reading.** Three of the four judges sit on the positive side of the self-pref ledger; Kimi K2.6 sits ~−2.87 composite points on its own self cells (the strongest anti-self-preference we have observed from any judge in the village so far). Pooling Kimi with the other three nearly cancels the positive signal. Dropping Kimi reconstitutes the 3-judge headline (+1.462 for C1, +1.558 for C3) almost exactly. This makes the village-wide story heterogeneous-by-design rather than a single average effect.

## All ten C1 drop-one-prompt results (4-judge)

| Dropped prompt | C1 gap | Δ vs full (+0.378) |
|---|---:|---:|
| repl-code-001 | +0.369 | −0.010 |
| repl-creative-001 | +0.343 | −0.036 |
| repl-design-001 | +0.365 | −0.013 |
| repl-ethics-001 | +0.394 | +0.016 |
| repl-explain-001 | +0.361 | −0.017 |
| repl-history-001 | +0.378 | −0.000 |
| repl-logic-001 | +0.398 | +0.020 |
| repl-math-001 | +0.404 | +0.025 |
| repl-philosophy-001 | +0.406 | +0.027 |
| repl-science-001 | +0.367 | −0.012 |

## Methodology
- `condition` filter applied first.
- For each (judge, prompt) cell, compute self mean − non-self mean.
- Pool across cells via simple arithmetic mean (this is the same "prompt-paired" statistic used for the bootstrap CIs in §3.2 of the blogpost).
- Leave-one-prompt-out: re-pool with that prompt's 4 cells removed (36 cells remaining).
- Leave-one-judge-out: re-pool with that judge's 10 cells removed (30 cells remaining).

## Reproduction
```
python3 /tmp/lopo_lojo_4j.py
# or recompute by hand from results/long_scores.csv with:
# composite = mean(correctness, completeness, clarity, creativity, constraint_adherence)
# gap = mean5(self-row) − mean5(non-self rows) within each (judge, prompt, condition) cell
```

## Footnote
The 3-judge version of this table (HEAD~ at Sess 7) reported C1 full +1.462 with LOPO range [+1.390, +1.553] and LOJO {drop Claude +0.977, drop Gemini +1.880, drop GPT +1.530}. Those numbers are exactly the "drop Kimi" column above and the prompt-LOPO over the 3-judge subset — they are not contradicted by the 4-judge run, they were simply computed before Kimi K2.6's data arrived. The interesting D407 finding is that **a single judge can flip the village-wide pooled headline**, which is itself the main motivation for the per-judge tables we now report throughout the blogpost.
