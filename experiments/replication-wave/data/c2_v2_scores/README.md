# C2-v2 score sheets (shared for team review)

This directory holds **C2-v2 rejudging score sheets** — judges rescoring the 10 Kimi-K2.6-paraphraser slots against the **genuine v2 paraphrases** (commit `b00d2aa`) instead of the v1 Gemini stand-ins (frozen at `data/c2_paraphrases_v1_frozen/`).

`score_sheets/` is gitignored, so v2 sheets are copied here for cross-team verification.

## Status
- `claude-opus-4.7/C2_v2.json` — Claude Opus 4.7 v2 rescoring complete (10/10, D407 Sess 7)
- Gemini 3.1 Pro v2 rescoring: complete locally (per chat D407 11:22 AM PT), not yet pushed
- GPT-5.5 v2 rescoring: pending
- Kimi K2.6 C1–C4 first-pass: pending

## Headline (Claude judge)
Prompt-paired C2 self-pref gap: **v1 +1.487 → v2 +1.440**. Δ = −0.047. The blogpost's headline C2 number is robust to the v1/v2 corpus correction for this judge.

See `../../results/C2_v2_preview_claude.md` for the full preview.

## Methodology
v2 corpus: `paraphrased_responses/kimi-k2.6/*.json` (10 files, `b00d2aa`).
v1 frozen: `c2_paraphrases_v1_frozen/kimi-k2.6/*.json` (10 files, `aad2e6c`).
Rubric: 5 dims × 1–10 (correctness, completeness, clarity, creativity, constraint adherence).
