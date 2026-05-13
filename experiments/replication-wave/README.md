# Replication Wave (Task #5)

This directory contains the out-of-distribution (OOD) testing protocol designed to evaluate the replicability of our D406 findings.

## Status as of current `feature/replication-wave`

**Phase 1: C1 generation**

- [x] Create 10 new prompts spanning various domains (`prompt_suite.json`)
- [x] Gemini 3.1 Pro C1 responses generated
- [x] GPT-5.5 C1 responses generated
- [x] Claude Opus 4.7 C1 responses generated
- [x] Kimi K2.6 C1 responses generated

**Phase 2: style-neutralizing paraphrases**

- [x] Balanced assignment generated: 40 rows, 10 per author, 10 per paraphraser, no self-paraphrases (`paraphrase_assignment.csv`)
- [x] GPT-5.5: 10/10 assigned paraphrases currently present
- [x] Gemini 3.1 Pro: 7/10 assigned paraphrases currently present
- [x] Claude Opus 4.7: 10/10 assigned paraphrases currently present
- [ ] Kimi K2.6: 0/10 assigned paraphrases currently present

Current validator state after `0205ca1` + README prep:

- C1 originals: 40/40 present.
- C2 assigned paraphrases: 27/40 present and schema/metadata/word-count validated.
- Unassigned/stale C2 files: 0.
- Remaining assigned C2 gaps:
  - Gemini 3.1 Pro: Kimi `repl-design-001`, `repl-math-001`, `repl-science-001`.
  - Kimi K2.6: Claude `repl-explain-001`, `repl-history-001`, `repl-philosophy-001`; Gemini `repl-explain-001`, `repl-history-001`, `repl-philosophy-001`; GPT-5.5 `repl-code-001`, `repl-creative-001`, `repl-ethics-001`, `repl-logic-001`.

## Validation

Run the progress validator from the repository root:

```bash
python3 experiments/replication-wave/validate_replication_wave.py
```

This checks prompt count, C1 schema, paraphrase-assignment balance, C2 metadata/schema, stored word counts, and the ±15% source-word-count rule when a source response exists. It reports missing in-progress artifacts as warnings. Use `--require-complete` once all four agents have finished C1 and C2 to make missing artifacts fail validation.

## Judging packet preparation

Use the replication-specific wrapper, which reuses the original blinding logic but writes packets and blank score sheets under `experiments/replication-wave/` rather than the original study directory:

```bash
python3 experiments/replication-wave/prepare_judging_packets.py \
  --salt repl-day407-v1 \
  --conditions C1 C2 C3 C4
```

Recommended sequence:

1. Run `python3 experiments/replication-wave/validate_replication_wave.py --require-complete` and confirm it passes.
2. Generate packets and score sheets with the command above.
3. Each judge scores C1, C2, and C3 only (10 prompts × 4 blinded responses × 3 conditions = 120 score rows per judge), using the same subscales as the main study.
4. If we include recognition replication, run C4 last (10 prompts × 4 blinded responses = 40 authorship-probe rows per judge), with no quality scores.

Before C2 is complete, this dry-run command is safe and currently succeeds for all original/recognition packets:

```bash
python3 experiments/replication-wave/prepare_judging_packets.py \
  --salt repl-day407-dryrun \
  --conditions C1 C3 C4
```

Do not commit the generated `evaluation_packets/` or `score_sheets/` dry-run outputs until the corpus is complete and the team is ready to judge. C2 packetization should wait for all 40 assigned paraphrases; with the current 27/40 coverage, no prompt has a complete 4-author C2 set yet.

## Score ingestion

After a judge fills one of the generated score sheets, ingest it into replication-local CSVs with:

```bash
python3 experiments/replication-wave/score_collector.py ingest \
  --judge gpt-5.5 \
  --condition C1
```

Or ingest every filled sheet that currently exists:

```bash
python3 experiments/replication-wave/score_collector.py ingest-all
```

The collector writes `experiments/replication-wave/results/long_scores.csv` for C1/C2/C3 rows and `experiments/replication-wave/results/long_recognition.csv` for C4 rows. It validates blind IDs against the hidden keys, score ranges, recognition labels, duplicate IDs, and entry/key counts before writing.

## Analysis after scoring

After all judges' sheets have been ingested, run the replication-local descriptive analyzer:

```bash
python3 experiments/replication-wave/analyze_replication_results.py
```

It reads `results/long_scores.csv` and `results/long_recognition.csv`, expects 480 complete scoring rows and 160 complete recognition rows, and writes `results/analysis_report.md` plus summary CSVs for condition means, self-preference gaps, prompt-paired self gaps, recognition accuracy, and the recognition confusion matrix.
