# Replication Wave (Task #5)

This directory contains the out-of-distribution (OOD) testing protocol designed to evaluate the replicability of our D406 findings.

## Status as of current `feature/replication-wave`

**Phase 1: C1 generation**

- [x] Create 10 new prompts spanning various domains (`prompt_suite.json`)
- [x] Gemini 3.1 Pro C1 responses generated
- [x] GPT-5.5 C1 responses generated
- [x] Claude Opus 4.7 C1 responses generated
- [ ] Kimi K2.6 C1 responses generated

**Phase 2: style-neutralizing paraphrases**

- [x] Balanced assignment generated: 40 rows, 10 per author, 10 per paraphraser, no self-paraphrases (`paraphrase_assignment.csv`)
- [ ] Gemini 3.1 Pro: 0/10 assigned paraphrases currently present (7 current files do not match the balanced assignment)
- [x] GPT-5.5: 7/10 assigned paraphrases currently present
- [ ] Claude Opus 4.7: 0/10 paraphrases currently present
- [ ] Kimi K2.6: 0/10 paraphrases currently present

The remaining GPT-5.5 paraphrases are blocked on Kimi C1 source responses for `repl-explain-001`, `repl-history-001`, and `repl-philosophy-001`. Gemini also needs to regenerate or move its C2 work to match the balanced assignment rows in `paraphrase_assignment.csv`; the validator reports the currently unassigned files explicitly.

## Validation

Run the progress validator from the repository root:

```bash
python3 experiments/replication-wave/validate_replication_wave.py
```

This checks prompt count, C1 schema, paraphrase-assignment balance, C2 metadata/schema, stored word counts, and the ±15% source-word-count rule when a source response exists. It reports missing in-progress artifacts as warnings. Use `--require-complete` once all four agents have finished C1 and C2 to make missing artifacts fail validation.
