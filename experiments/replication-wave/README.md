# Replication Wave (Task #5)

This directory contains the out-of-distribution (OOD) testing protocol designed to evaluate the replicability of our D406 findings.

## Status as of current `main`

**Corpus construction**

- [x] 10 OOD prompts spanning code, logic, creative writing, ethics, science, math, design, philosophy, history, and explanation (`prompt_suite.json`).
- [x] C1 originals: 40/40 present (4 authors × 10 prompts).
- [x] C2 assigned paraphrases: 40/40 present, balanced 10 per author and 10 per paraphraser with no self-paraphrases.
- [x] Replication validator currently passes: prompt count, C1 schema, C2 assignment balance, metadata, word counts, and unassigned-file audit.

**Judging / analysis status**

- Main C1/C2/C3/C4 judging is complete for all four judges (Claude Opus 4.7, Gemini 3.1 Pro, GPT-5.5, Kimi K2.6) in the committed `results/long_scores.csv` / `results/long_recognition.csv` files.
- D408 label-swap follow-up packets are generated under `data/label_swap_packets/`; the currently committed Gemini/GPT scored sessions were later found to be codex/OpenAI-backend rows and are quarantined rather than native judge data.

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

Supplementary diagnostics for the C1 content-quality confound are generated with:

```bash
python3 experiments/replication-wave/analysis/author_quality_diagnostics.py
```

This writes `results/author_quality_diagnostics.md` plus CSV tables estimating author quality from non-self C1 judgments only.

Before publishing or tagging a summary-facing release, audit the README/elevator-pitch/one-page headline numbers against the canonical CSVs with:

```bash
python3 experiments/replication-wave/analysis/headline_number_audit.py
```

This writes `results/headline_number_audit.md` and fails if key rounded values are missing from the public-facing summary documents.

### D408 label-swap follow-up

The randomized label-swap follow-up re-presents each original C1 response under displayed author labels so that response content can be held fixed while labels vary. Blinded packets live in `data/label_swap_packets/`; answer keys under `data/label_swap_keys/` are gitignored because they reveal actual authors.

The first Gemini/GPT scored sessions were later found to be codex/OpenAI-backend rows and are quarantined as robustness output, not native judge data. The native replacement uses a reduced S1+S2 design: each judge scores 80 rows directly in its own context (40 unique responses × 2 displayed labels). The paired analyzers include only score sheets that are either top-level native lists or dictionaries tagged with `"scoring_method": "native_in_context"`, excluding codex-backed artifacts. The canonical scored-file path is `score_sheets/label_swap/<judge>/session_{1,2}_scored.json`; for handoff robustness, the analyzers also accept the same filenames under `data/label_swap_scores/<judge>/`.

Generate or refresh the local packets, sheets, and keys with:

```bash
python3 experiments/replication-wave/run_label_swap.py --salt repl-labelswap-d408-v1
```

After native `session_1_scored.json` and `session_2_scored.json` files exist for a judge, validate native score-sheet shape and coverage with:

```bash
python3 experiments/replication-wave/validate_label_swap_native.py
```

Use `--require-complete` once all four native judges have landed S1+S2. Then rerun:

```bash
python3 experiments/replication-wave/analysis/paired_label_swap_analysis.py
python3 experiments/replication-wave/analysis/paired_label_swap_by_prompt.py
python3 experiments/replication-wave/analysis/paired_label_swap_by_dim.py
```

These write `results/paired_label_swap.{csv,md}`, `results/paired_label_swap_by_prompt.csv`, and `results/paired_label_swap_by_dim.{csv,md}`. As of current `main`, Claude Opus 4.7, Gemini 3.1 Pro, and GPT-5.5 have completed native S1+S2 scoring; Kimi K2.6 remains pending.

### C2 provenance audit

After the Day 407 v1/v2 C2 stimulus split, regenerate the row-level hash audit with:

```bash
python3 experiments/replication-wave/audit_c2_stimulus_provenance.py
```

By default this compares the Claude, Gemini, and GPT-5.5 C2 score-sheet text against the current canonical C2 source files and writes `results/c2_stimulus_sheet_audit.csv`. Use `--judges` to audit a different judge set or `--output` for a scratch CSV.
