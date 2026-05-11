# Evaluator-Bias Experiment

A controlled within-subject study of self-recognition and self-preference in four frontier LLM judges (Claude Opus 4.7, Gemini 3.1 Pro, GPT-5.5, Kimi K2.6), each acting simultaneously as author and judge.

See `DESIGN.md` at the repo root for the full pre-registered design.
See `blogpost/draft.md` for the writeup-in-progress.

## Pipeline

```
prompt_suite.json              (30 prompts, frozen before generation)
    │
    ▼
responses/<author>/prompt-<id>.json        (4 authors × 30 prompts = 120)
    │
    ├── (used directly in C1 / C3 / C4)
    │
    ▼
paraphrased_responses/<paraphraser>/<author>__prompt-<id>.json
                                              (4 × 30 = 120, round-robin)
    │
    └── (used in C2)
```

Per judge, per response, we collect:
- C1: rubric scores (5 dims, 1–10) on the original.
- C2: rubric scores on the paraphrased version.
- C3: rubric scores on the original under a bias warning.
- C4: predicted author + confidence (1–5) on the original.


## Blinded judging workflow

Generate blinded packets before scoring. The default command requires all four conditions to be complete:

```bash
python3 experiments/evaluator-bias/blind_responses.py
```

While C2 paraphrases are still pending, judges can safely start the original-response conditions only:

```bash
python3 experiments/evaluator-bias/blind_responses.py --conditions C1 C3 C4
```

Visible packets are written to `evaluation_packets/packets/<judge>/<condition>.json`. Hidden answer keys are written separately to `evaluation_packets/keys/<judge>/<condition>_key.json`; judges should not inspect keys before submitting scores.

For each judge and condition, export a fillable score sheet, complete every entry, then ingest it into the long-format result CSVs:

```bash
python3 experiments/evaluator-bias/score_collector.py export --judge gpt-5.5 --condition C1
# fill experiments/evaluator-bias/score_sheets/gpt-5.5/C1.json
python3 experiments/evaluator-bias/score_collector.py ingest --judge gpt-5.5 --condition C1
```

For C1/C2/C3, fill integer 1–10 scores for correctness, completeness, clarity, creativity/insight, and constraint adherence. For C4, fill `predicted_author` with one of the four model slugs and confidence 1–5. Re-ingesting is idempotent per judge/condition, so a corrected sheet replaces earlier rows for that judge/condition.

## Files

| File / dir                              | Role                                                                          |
|----------------------------------------|-------------------------------------------------------------------------------|
| `prompt_suite.json`                    | 30 prompts spanning 12 task families. Frozen before generation.                |
| `generate_responses.py`                | Helper stub for generation phase.                                              |
| `blind_responses.py`                   | Blinding + per-judge re-randomization of response IDs.                         |
| `evaluation_packets/`                  | Generated visible packets and hidden keys for each judge/condition.            |
| `score_collector.py`                   | Exports fillable score sheets and ingests completed sheets into result CSVs.    |
| `score_sheets/`                        | Generated per-judge templates to fill during C1-C4 judging.                    |
| `responses/<author>/`                  | One JSON file per (author, prompt) — original generations.                     |
| `paraphrased_responses/<paraphraser>/` | One JSON file per (paraphraser, original_author, prompt) — neutralized text.   |
| `paraphrase_assignment.csv`            | The 120-job round-robin assignment (each author paraphrased by exactly 3 of 4). |
| `paraphrase_worklists/<model>_worklist.json` | Per-model paraphrase task list (30 jobs each).                          |
| `PARAPHRASE_INSTRUCTIONS.md`           | Style-neutralization spec.                                                     |
| `validate_paraphrases.py`              | Schema + length tolerance + coverage check on the paraphrase corpus.           |
| `scoring_template.md`                  | Rubric (5 dimensions, 1–10).                                                   |
| `evaluation_prompts.md`                | Exact judge prompts for each of C1, C2, C3, C4.                                |

## Status

Run `python experiments/evaluator-bias/validate_paraphrases.py` from the repo root to see current paraphrase corpus coverage.

To check response coverage:
```bash
for d in claude-opus-4.7 gemini-3.1-pro gpt-5.5 kimi-k2.6; do
  count=$(ls experiments/evaluator-bias/responses/$d 2>/dev/null | wc -l)
  echo "  $d: $count/30"
done
```

## Reproducibility

The 30-prompt suite was committed before any response was generated, and its commit hash is recorded in `DESIGN.md`. Each response is timestamped via its git commit. Evaluator prompts for each condition are committed verbatim in `evaluation_prompts.md` and must not be edited without a version bump.
