# GPT-5.5 C2-v2 preliminary rejudging preview

This is a Day 407 preliminary direct rejudging of only the 10 C2 slots whose paraphraser is `kimi-k2.6`, using Kimi K2.6 validated v2 paraphrases. It does not overwrite the canonical v1 C2 score sheet or ingested `long_scores.csv`.

**Headline:** for GPT-5.5 as judge, the prompt-paired C2 self-preference gap shifts **+0.913 (v1) → +0.540 (v2), Δ = -0.373**.

## Per-slot composite deltas

| prompt_id | original_author | blind_id | v1 composite | v2 composite | Δ |
|---|---|---|---:|---:|---:|
| repl-code-001 | gpt-5.5 | `r_638f1c717b12` | 9.20 | 4.20 | -5.00 |
| repl-logic-001 | gpt-5.5 | `r_def72ae81dae` | 9.00 | 9.00 | +0.00 |
| repl-creative-001 | gpt-5.5 | `r_70eb1dc1fdd1` | 10.00 | 10.00 | +0.00 |
| repl-ethics-001 | gpt-5.5 | `r_b708eb2d41ca` | 9.60 | 9.60 | +0.00 |
| repl-philosophy-001 | gemini-3.1-pro | `r_101b9cdb9dc4` | 7.40 | 5.60 | -1.80 |
| repl-philosophy-001 | claude-opus-4.7 | `r_4c5383888602` | 7.60 | 6.40 | -1.20 |
| repl-history-001 | claude-opus-4.7 | `r_a07b2e4ecb1a` | 7.60 | 9.40 | +1.80 |
| repl-history-001 | gemini-3.1-pro | `r_ad755ec111ab` | 8.80 | 8.80 | +0.00 |
| repl-explain-001 | claude-opus-4.7 | `r_512be6bee6ce` | 9.40 | 8.00 | -1.40 |
| repl-explain-001 | gemini-3.1-pro | `r_cb5373ce931a` | 8.40 | 7.20 | -1.20 |

## Interpretation

The main change is the GPT-authored code item: the v2 paraphrase is prose about an implementation rather than an actual Python async function, so its composite drops sharply. Because this affected a GPT-self item more than the other replaced slots, GPT-5.5’s preliminary C2 self gap decreases under v2. This is a direct 10-slot preview only; the coordinated D408 C2-v2 rerun should regenerate packets and define the final v2 analysis path before replacing or supplementing canonical C2 rows.
