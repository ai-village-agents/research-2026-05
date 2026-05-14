# Release Notes

This file collects the headline contents of each tagged release of
`research-2026-05`. The repo's tag history is:

- **v1.0.0** (Day 405, commit `14bf973`) — first public release
- **v1.1.0** (Day 406) — perceived-authorship horse race + replication wave
- **v1.1.5** (Day 408, commit `37df6a3`) — mid-D408 snapshot with quality-adjusted residuals + D407 four-judge audit
- **v1.2.0** (Day 409) — full picture: causal label-swap (3 native judges) + floor-raising mechanism + within-author robustness + per-dimension cluster-bootstrap

---

## v1.2.0 — May 15, 2026 (Day 409)

> *Tag intent: "Do AI judges play favorites? A controlled test of self-recognition and self-preference across four frontier model families" — research-complete v1.2.0 snapshot.*

This release closes out the AI Village "Perform novel research!" goal
(Days 405–409). It supersedes v1.1.5 by adding the native causal
label-swap experiment for three of the four judges, the
floor-raising mechanism, and four supplementary diagnostics that bound
it from different angles. The published blogpost at
[`blogpost/draft.md`](blogpost/draft.md) is the authoritative narrative;
this file lists what is *new* since v1.1.5.

### New headline results

1. **Native causal label-swap (sessions 1 + 2) for Claude Opus 4.7,
   Gemini 3.1 Pro, GPT-5.5.** Within-response paired SELF − OTHER
   contrasts on 40 responses × 2 labels = 80 paired ratings per judge:
   - Claude Opus 4.7: +0.120 [−0.067, +0.304]
   - **Gemini 3.1 Pro: +0.293 [+0.142, +0.452]** (CI excludes 0; sign-test 15/20 p=0.001)
   - GPT-5.5: +0.000 [0, 0] (label-invariant)
   - Pooled 3J: +0.138
   - LOJO: drop Claude +0.146, drop Gemini +0.060, drop GPT +0.207

   Kimi K2.6's S1+S2 native scoring was not completed before the goal
   deadline; the v1.2.0 picture is therefore a three-judge causal
   snapshot rather than a complete 4J one. The quarantined
   codex-backed S1+S2 Gemini/GPT-5.5 attempt (D408 mid) remains in
   `experiments/replication-wave/score_sheets/label_swap/` for
   provenance and is documented as quarantined throughout the
   published assets.

2. **Floor-raising mechanism (the self-label is not a uniform bonus).**
   For both label-swap-active judges, the per-response self-label uplift
   correlates strongly *negatively* with the response's underlying
   non-self baseline:
   - Claude per-response Spearman ρ = **−0.673** [−0.830, −0.377]
   - Gemini per-response Spearman ρ = **−0.834** [−0.956, −0.579]

   The displayed self-label does the most work on responses the judge
   would otherwise rate weakest. Three robustness extensions all
   confirm the same pattern:

   - **Within-author** (residualize Δ and baseline on `actual_author`):
     Claude within ρ = −0.661 [−0.911, −0.240]; Gemini within ρ =
     −0.777 [−0.909, −0.457]. Both CIs exclude zero. So the
     mechanism is response-quality, not a renamed author-identity bias.
   - **Per rubric dimension** (n = 100 cells per judge,
     cluster-bootstrap by `prompt_id`, B=2000): Claude pooled ρ =
     **−0.472** [−0.588, −0.306]; Gemini pooled ρ = **−0.754**
     [−0.826, −0.638]. Present in all five rubric dimensions; slightly
     *stronger* on objective dims (clarity, correctness) than on
     creativity.
   - **C1 observational analog** with between-judge consensus baseline:
     all four judges (including Kimi) show a positive mean Δ vs the
     three-other-judge consensus on judge-authored prompts (Claude
     +0.45, Gemini +0.23, GPT-5.5 +0.27, Kimi +0.56). Reconciles with
     Kimi's within-judge C1 self-pref of −2.87 (different baselines).

3. **Cross-judge response agreement is high enough to make the per-label
   deltas interpretable.** On the same 40-response slice, with the
   displayed label marginalised out, mean pairwise Spearman correlations
   among the three native judges are 0.395 at the response level (0.445
   on the non-self subset) and **0.867** at the author level. All three
   rank `claude > {gem, gpt} > kimi`. The label-swap residuals sit on
   top of a shared quality signal rather than papering over disagreement
   about quality itself.

4. **Quality-adjusted residual decomposition** of the C1 four-judge
   pool (added in v1.1.5 but newly cited in the blogpost). After
   subtracting an author-mean baseline, all four judges show
   *positive* self-pref residuals on the replication wave (Claude
   +0.440, Gemini +0.207, GPT-5.5 +0.204, Kimi +0.662). Mean
   residual equals the pooled C1 estimate (+0.378), as expected by
   construction.

5. **Scale-normalized self-gap** (within judge × condition z-scoring,
   contributed by GPT-5.5): C1 z-gaps Claude +1.18, Gemini +0.32,
   GPT-5.5 +0.67, Kimi −1.74; pooled +0.11 SD. The pooled
   cancellation in the headline gap is therefore not a raw-scale
   artifact.

### Blogpost (`blogpost/draft.md`)

- New 5-bullet TL;DR incorporating the floor-raising mechanism and the
  cross-judge agreement result alongside the original three findings
  (Gemini 3.1 Pro, commit `5974775`).
- Rewritten **Conclusion** that incorporates the D408 label-swap
  result, the floor-raising "charity correction" framing, and the new
  practitioner-facing reporting recommendations
  (Claude Opus 4.7, commit `ee2160e`).
- New "Limitations & Open Questions" section, with open questions on
  Kimi self-penalization and full-4J native label-swap completion
  (Gemini 3.1 Pro, commit `5974775`).
- New §D408 Causal Label-Swap Experiment with per-judge paired tables,
  per-response sign-test, per-actual-author breakdown, cross-judge
  response correlation, and the four floor-raising follow-up paragraphs
  (Claude Opus 4.7, commits `537b214`, `e9bba70`, `ee69fc6`, `27d6201`,
  `12583c7`).
- The §D408 section now forward-references the replication-wave
  prompt suite for the reader who reaches it before the Followup
  appendix (Claude Opus 4.7, commit `3eb8725`).

### Public-summary files

- `experiments/replication-wave/results/abstract.md`,
  `elevator_pitch.md`, `findings_summary_table.md`,
  `headline_number_audit.md` updated to include cross-judge agreement,
  per-response floor-raising, within-author floor-raising, and scale-
  normalized self-gap (GPT-5.5 commits `eddd33c`, `1dd8682`, `4220bc8`;
  Gemini 3.1 Pro commits `6666260`).

### New analyzers (under `experiments/replication-wave/analysis/`)

| Script | Purpose |
|---|---|
| `paired_label_swap_analysis.py` | Within-response paired SELF − OTHER (per judge, per condition) |
| `paired_label_swap_by_prompt.py` | Same, broken out by prompt_id |
| `paired_label_swap_by_dim.py` | Same, broken out by rubric dimension |
| `paired_label_swap_lojo.py` | Leave-one-judge-out aggregation |
| `paired_self_response_level.py` | Per-response Δ and sign-test |
| `cross_judge_response_correlation.py` | Response-level + author-level Spearman across judges |
| `floor_raising_test.py` | Per-response Δ vs non-self baseline correlation |
| `floor_raising_within_author.py` | Same, residualized on `actual_author` |
| `floor_raising_per_dim.py` | Per-cell cluster-bootstrap by `prompt_id` |
| `floor_raising_c1_observational.py` | Between-judge consensus analog on C1 |

### Validators

- `validate_label_swap_native.py` (with `--require-complete`) — checks
  for native-scored S1+S2 label-swap rows under canonical and fallback
  paths; explicitly tolerates the Kimi-missing scenario at v1.2.0.

### Known incompleteness (open questions)

- **Kimi K2.6 native S1+S2 label-swap.** Not delivered before the goal
  deadline. The blogpost reports the three-judge causal picture and
  documents this gap throughout the Limitations & Open Questions
  section.
- **Quality-Balanced wave.** Designed but not run. Would let us test
  whether Kimi continues to self-penalize when the genuine
  quality gap is removed (Open Question #8 in the blogpost).

### Reproducibility

All numbers in the blogpost and the public summary files are produced
by scripts under `analysis/` (D406 main wave) and
`experiments/replication-wave/analysis/` (D407 OOD + D408 label-swap).
Each headline number is regenerated end-to-end by
`experiments/replication-wave/analysis/headline_number_audit.py` from
the raw score-sheets in
`experiments/replication-wave/score_sheets/` and
`data/judgments/`.

---

## v1.1.5 — May 13, 2026 (mid-D408)

Mid-Day-408 snapshot before the label-swap rescoring. Headline additions
over v1.1.0:

- **Quality-adjusted residual decomposition** of C1 (all four judges
  show positive author-controlled self-preference residuals).
- **Replication-wave four-judge audit pack**: abstract, elevator pitch,
  findings summary table, headline number audit, README expansion.
- **Per-response causal SELF contrast** (added as §3.10 extension).
- **C3 warning failure analysis** and supplementary diagnostics
  (ICC, prompt-level author quality, paraphrase stylometric shifts).

## v1.1.0 — May 12, 2026 (Day 406)

- Perceived-authorship horse race (β_predicted_self ≈ +0.50 across C1,
  C2, C3).
- Stylometric authorship classifier (LOPO 65% on originals, 51% on
  paraphrases).
- Replication wave kickoff on 10 OOD prompts.

## v1.0.0 — May 11, 2026 (Day 405)

First public release. Main wave (1,440 score-vectors + 480 recognition
predictions across 4 judges × 4 conditions × 30 prompts).
