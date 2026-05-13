# C2-v2 score sheets (shared for team review)

This directory holds **C2-v2 rejudging score sheets** — judges rescoring the 10 Kimi-K2.6-paraphraser slots against the **genuine v2 paraphrases** (commit `b00d2aa`) instead of the v1 Gemini stand-ins (frozen at `data/c2_paraphrases_v1_frozen/`).

`score_sheets/` is gitignored, so v2 sheets are copied here for cross-team verification.

## Status
- `claude-opus-4.7/C2_v2.json` — Claude Opus 4.7 preliminary direct v2 rescoring complete (10/10, D407).
- `gemini-3.1-pro/C2_v2.json` — Gemini 3.1 Pro preliminary direct/full v2 rescoring sheet pushed (D407).
- `gpt-5.5/C2_v2.json` — GPT-5.5 preliminary direct v2 rescoring complete (10/10, D407).
- Kimi K2.6 C1–C4 first-pass: pending ingestion at the time of this note.

## Headline previews
| judge | C2 v1 self-pref gap | C2 v2 preview gap | Δ |
|---|---:|---:|---:|
| Claude Opus 4.7 | +1.487 | +1.440 | −0.047 |
| Gemini 3.1 Pro | +1.407 | +1.407 | +0.000 |
| GPT-5.5 | +0.913 | +0.540 | −0.373 |

These are preliminary direct v2 rescoring previews, not replacements for the canonical v1 C2 rows in `results/long_scores.csv`. See:
- `../../results/C2_v2_preview_claude.md`
- `../../results/C2_v2_preview_gemini.md`
- `../../results/C2_v2_preview_gpt-5.5.md`

## Methodology
v2 corpus: `paraphrased_responses/kimi-k2.6/*.json` (10 files, `b00d2aa`).
v1 frozen: `c2_paraphrases_v1_frozen/kimi-k2.6/*.json` (10 files, `aad2e6c`).
Rubric: 5 dims × 1–10 (correctness, completeness, clarity, creativity, constraint adherence).
