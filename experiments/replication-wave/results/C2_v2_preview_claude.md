# Preliminary C2-v2 results — Claude Opus 4.7 judge (D407 Sess 7)

## Summary
Claude Opus 4.7 rescored the 10 Kimi-K2.6-paraphraser slots against the **genuine v2 paraphrases** (commit `b00d2aa`) and compared to v1 Gemini stand-in stimuli (commit `95d1c94`, now frozen at `data/c2_paraphrases_v1_frozen/`).

**Headline finding: the v2 corpus does NOT materially change Claude's measured C2 self-preference gap.**

| Corpus | Prompt-paired self-pref gap | SD |
|---|---:|---:|
| C2 v1-pure (10 stand-ins) | **+1.487** | 2.239 |
| C2 corrected (v1 non-Kimi + v2 Kimi) | **+1.440** | 2.285 |
| Δ | **−0.047** | — |

The v2 corpus correction shifts Claude's prompt-paired C2 gap by less than 0.05 of a rubric point. The "C2 +1.49 self-pref gap" reported in the blogpost for this judge is robust to the v1→v2 corpus substitution.

## Per-slot v1 vs v2 deltas

| prompt_id | author | v1 mean | v2 mean | Δ |
|---|---|---:|---:|---:|
| repl-code-001 | gpt-5.5 | 8.80 | 4.40 | **−4.40** |
| repl-logic-001 | gpt-5.5 | 8.80 | 8.80 | 0.00 |
| repl-creative-001 | gpt-5.5 | 10.00 | 9.60 | −0.40 |
| repl-ethics-001 | gpt-5.5 | 8.80 | 8.80 | 0.00 |
| repl-philosophy-001 | gemini-3.1-pro | 6.80 | 8.20 | +1.40 |
| repl-philosophy-001 | claude-opus-4.7 | 9.80 | 8.80 | −1.00 |
| repl-history-001 | gemini-3.1-pro | 8.80 | 8.80 | 0.00 |
| repl-history-001 | claude-opus-4.7 | 10.00 | 9.80 | −0.20 |
| repl-explain-001 | claude-opus-4.7 | 10.00 | 8.80 | −1.20 |
| repl-explain-001 | gemini-3.1-pro | 8.80 | 6.40 | **−2.40** |
| **Mean** | | 9.06 | 8.24 | **−0.82** |

Two slots dropped sharply because Kimi's actual paraphrase strategy **removes formatting elements the prompt explicitly required**:
- `repl-code-001`: Kimi's v2 paraphrase turns the runnable Python code into a prose description of the implementation. Type hints, docstring text, and `async`/`await` syntax disappear, costing the `constraint_adherence` dimension heavily.
- `repl-explain-001`: Kimi's v2 paraphrase merges Claude's and Gemini's bullet-pointed explanations into running paragraphs. The prompt explicitly asks for bullet points.

These are **stylistic artifacts of Kimi as a paraphraser**, not stylistic deficiencies of the original authors. They flow uniformly across all source-authors paraphrased by Kimi (so they affect self and other roughly equally), which is why the prompt-paired gap survives intact.

## Implication for the main analysis
The 10 Kimi-paraphraser slots being v1 Gemini stand-ins during the original judging was a *real* design flaw, but on this judge's scores it shifts the headline C2 number by under one-twentieth of a rubric point. The asymmetric paraphrase effect (Claude −38.9% vs Gemini +124.5%) for this judge is preserved under v2.

## Status
This note is a **historical preliminary preview** of Claude Opus 4.7's C2-v2 rescoring pass. The project later completed Gemini and GPT C2-v2 rescoring, Kimi K2.6 C1–C4 judging, and the full four-judge native label-swap analysis. For the final C2-v2-inclusive results, use the canonical merged outputs in `long_scores.csv`, `blogpost.md`, `findings_summary_table.md`, and `headline_number_audit.md`.

Historical snapshot at the time this preview was written:
- Claude C2-v2: **complete (10/10)** at `score_sheets/claude-opus-4.7/C2_v2.json`
- Gemini C2-v2 and GPT-5.5 C2-v2 were outside this preliminary preview snapshot.
- Kimi K2.6 C1–C4 was also outside this preliminary preview snapshot.

## Methodology note
v2 corpus = `experiments/replication-wave/paraphrased_responses/kimi-k2.6/*.json` (10 files, commit `b00d2aa`).
v1 frozen corpus = `experiments/replication-wave/data/c2_paraphrases_v1_frozen/kimi-k2.6/*.json` (10 files, my freeze `aad2e6c`).
Scoring rubric identical to v1 (5 dims × 1–10).
