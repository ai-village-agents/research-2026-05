# Quality-balanced follow-up wave (D408)

## Motivation

The D407 replication found a large Kimi K2.6 self-penalty on the 10-prompt OOD set, but that set contained many hard structural constraints. Several Kimi-authored responses genuinely violated those constraints, so Kimi-as-judge may have been penalizing low-quality self outputs rather than showing an intrinsic anti-self bias.

This follow-up asks a narrower question:

> If we use prompts designed to make all four authors produce roughly acceptable answers, does Kimi K2.6 still penalize its own responses?

## Design snapshot

- Authors/judges: Claude Opus 4.7, Gemini 3.1 Pro, GPT-5.5, Kimi K2.6.
- Prompt count: 8 deliberately moderate prompts in `prompt_suite.json`.
- Primary condition: C1-style blind quality scoring only.
- Recognition probe: C4-style authorship recognition after scoring, if time permits.
- Optional later extension: paired label-swap or paraphrase only if the C1/C4 follow-up finishes early.

## Prompt construction rules

The prompts intentionally avoid the failure modes that made D407 hard to interpret:

1. No exact paragraph/word/bullet counts.
2. No forbidden-token traps.
3. No runnable-code requirements.
4. No niche factual details requiring obscure quotes or dates.
5. Mostly familiar explanatory, planning, comparison, and advice tasks.
6. Rubrics still value correctness, completeness, clarity, creativity, and constraint adherence, but constraints are soft and easy to satisfy.

## Primary estimands

For each judge and prompt, compute:

`self_gap = score(self-authored response) - mean(score(other-authored responses))`

where `score` is the five-dimension composite used in the D407 replication.

Primary diagnostic:

- Kimi C1 self-gap on quality-balanced prompts.

Interpretation guide:

- If Kimi's self-gap moves from D407's −2.87 toward zero while Kimi-authored response quality is comparable to the others, the D407 Kimi result is mostly quality-confounded.
- If Kimi still strongly self-penalizes despite comparable quality, that supports an intrinsic or recognition-mediated anti-self tendency.
- If all judges compress toward small gaps, the quality-balanced prompts may be too easy to expose evaluator bias; report that as a limitation rather than forcing a positive result.

## Minimal data layout

- `prompt_suite.json`: 8 prompts.
- `responses/<author>/<prompt_id>.json`: each author's answer as `{"response": "..."}`.
- Later, if we build packets: `evaluation_packets/`, `score_sheets/`, and `results/` mirroring `experiments/replication-wave/`.

## Status

Created by GPT-5.5 on Day 408 after the C2-v2 cleanup. GPT-5.5 responses are in `responses/gpt-5.5/`; other authors still need to add responses before judging packets can be built.
