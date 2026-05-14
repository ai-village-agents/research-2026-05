# Replication-wave result artifact index

This index groups the main D407/D408 replication outputs and exploratory supplements. It is a navigation aid only; the canonical narrative remains `blogpost.md`, `elevator_pitch.md`, and `findings_summary_table.md`.

## Primary narrative outputs

- [`abstract.md`](abstract.md) — concise research abstract for final-release readers.
- [`blogpost.md`](blogpost.md) — full accessible write-up of the replication and native paired label-swap follow-up.
- [`elevator_pitch.md`](elevator_pitch.md) — short version of the headline findings.
- [`findings_summary_table.md`](findings_summary_table.md) — one-page table contrasting observational gaps, causal label-swap gaps, paraphrase gaps, recognition, author quality, and quality-adjusted residuals.
- [`headline_number_audit.md`](headline_number_audit.md) — reproducibility/audit check that recomputes headline values and confirms key snippets are present in public-facing summaries.

## Canonical data tables

- [`long_scores.csv`](long_scores.csv) — 480 score rows: 4 judges × 40 response cells × C1/C2/C3.
- [`long_recognition.csv`](long_recognition.csv) — 160 C4 authorship-recognition rows.
- [`condition_summary.csv`](condition_summary.csv) and [`self_preference_gaps.csv`](self_preference_gaps.csv) — condition-level and judge-level self-preference summaries.
- [`recognition_accuracy.csv`](recognition_accuracy.csv) — per-judge recognition accuracy and self-recognition.

## Native paired label-swap causal outputs

- [`paired_label_swap.md`](paired_label_swap.md) and [`paired_label_swap.csv`](paired_label_swap.csv) — within-response paired displayed-label residuals; currently Claude, Gemini, and GPT-5.5 native S1+S2 complete, Kimi pending.
- [`paired_label_swap_by_dim.md`](paired_label_swap_by_dim.md) and [`paired_label_swap_by_dim.csv`](paired_label_swap_by_dim.csv) — per-dimension paired label residuals.
- [`paired_label_swap_by_prompt.csv`](paired_label_swap_by_prompt.csv) — per-prompt paired label residuals used for sign checks.
- [`paired_self_response_level.md`](paired_self_response_level.md) and [`paired_self_response_level.csv`](paired_self_response_level.csv) — per-response causal SELF-label contrast with exact sign tests on responses that were shown once with self label and once with non-self label.
- [`cross_judge_response_level.md`](cross_judge_response_level.md) and [`cross_judge_response_level.csv`](cross_judge_response_level.csv) — overlap diagnostic asking whether response-level SELF-label deltas are shared across judges.
- [`cross_judge_response_correlation.md`](cross_judge_response_correlation.md) and [`cross_judge_response_correlation.csv`](cross_judge_response_correlation.csv) — pairwise Spearman/Pearson agreement among native judges on per-response composite scores in the label-swap data (40 responses), plus 4×3 author-by-judge mean matrix and author-rank concordance (mean Spearman 0.867).
- [`floor_raising_test.md`](floor_raising_test.md) and [`floor_raising_test.csv`](floor_raising_test.csv) — per-response self-label uplift Δ regressed on non-self baseline composite. Both non-null judges show strong negative correlation (Claude r=−0.672; Gemini r=−0.874), confirming self-label is a floor-raiser on weak content, not a uniform bonus.
- [`floor_raising_within_author.md`](floor_raising_within_author.md) and [`floor_raising_within_author.csv`](floor_raising_within_author.csv) — author-controlled follow-up to the floor-raising test. Residualizing Δ and baseline on `actual_author` leaves the negative correlation essentially intact (Claude within ρ=−0.661 [−0.911, −0.240]; Gemini within ρ=−0.777 [−0.909, −0.457]; both CIs exclude 0), so the mechanism is response-quality, not author-identity.
- [`floor_raising_c1_observational.md`](floor_raising_c1_observational.md) and [`floor_raising_c1_observational.csv`](floor_raising_c1_observational.csv) — C1 observational analog of the label-swap floor-raising test (all 4 judges, n=10 prompts each). Headline: all 4 judges (including Kimi +0.56) show a positive mean Δ between their own composite and cross-judge consensus on their own author. Floor-raising negative ρ is directionally present for Claude (ρ=−0.62 [−0.93, +0.05]) and GPT (ρ=−0.62 [−0.96, +0.04]) but underpowered at this N.
- [`floor_raising_per_dim.md`](floor_raising_per_dim.md) and [`floor_raising_per_dim.csv`](floor_raising_per_dim.csv) — per-dimension extension of the floor-raising test (n=100 cells per judge, cluster-bootstrap CI by prompt_id). Pooled Claude ρ=−0.472 [−0.588, −0.306], Gemini ρ=−0.754 [−0.826, −0.638] (both CIs exclude 0). Floor-raising present in all 5 rubric dims; slightly stronger on objective dims (clarity, correctness) than the most subjective (creativity).
- [`paired_lojo.md`](paired_lojo.md) and [`paired_lojo.csv`](paired_lojo.csv) — leave-one-judge-out sensitivity for the currently available native paired SELF−OTHER causal gaps.

## Quality, recognition, and heterogeneity diagnostics

- [`author_length_diagnostic.md`](author_length_diagnostic.md) and [`author_length_diagnostic.csv`](author_length_diagnostic.csv) — exploratory check asking whether an author's peer-quality deficit is purely driven by raw response word count.
- [`cross_judge_correlation.md`](cross_judge_correlation.md) and [`cross_judge_correlation.csv`](cross_judge_correlation.csv) — cross-judge response-level correlation in C1, checking if judges agree on which responses are good/bad independent of authorship.
- [`author_quality_diagnostics.md`](author_quality_diagnostics.md) plus `author_quality_*.csv` — non-self C1 author-quality checks showing Kimi-authored originals are independently lower-rated on this prompt set.
- [`author_quality_by_prompt.md`](author_quality_by_prompt.md) plus `author_quality_*_by_prompt.csv` — prompt-level version of the author-quality diagnostic.
- [`quality_adjusted_residual.md`](quality_adjusted_residual.md) and [`quality_adjusted_residual.csv`](quality_adjusted_residual.csv) — decomposes observational C1 self gaps into peer-quality expected component plus residual.
- [`confidence_stratification.md`](confidence_stratification.md) and [`confidence_stratification.csv`](confidence_stratification.csv) — perceived-self score gaps stratified by C4 confidence, with sparse-cell counts.
- [`prompt_category_bias.md`](prompt_category_bias.md) and [`prompt_category_bias.csv`](prompt_category_bias.csv) — C1 self-preference gaps by prompt category, using the standard 1–10 composite scale.
- [`radar_chart_data.md`](radar_chart_data.md) and [`radar_chart_data.csv`](radar_chart_data.csv) — per-dimension judge × condition gap table for radar/spider plots.
- [`length_bias_report.md`](length_bias_report.md) and [`length_bias_correlation.csv`](length_bias_correlation.csv) — exploratory check of response-length correlations with C1/C2/C3 scores.
- [`prompt_response_length.md`](prompt_response_length.md) — prompt-level breakdown of baseline C1 response lengths by author.
- [`prompt_response_format.md`](prompt_response_format.md) and [`format_bias.md`](format_bias.md) — prompt-level format features and exploratory correlations between formatting elements (bold tags, list items, code blocks) and composite scores.

## Robustness, provenance, and implementation diagnostics

- [`leave_one_out_sensitivity.md`](leave_one_out_sensitivity.md) — observational leave-one-prompt and leave-one-judge sensitivity.
- [`inter_rater_agreement.md`](inter_rater_agreement.md) and [`icc_agreement_report.md`](icc_agreement_report.md) — inter-rater agreement summaries.
- [`c3_warning_failure_analysis.md`](c3_warning_failure_analysis.md) — C1→C3 delta diagnostic with caveat about heterogeneous C3 delivery.
- [`paraphrase_shifts_report.md`](paraphrase_shifts_report.md) — stylometric changes introduced by C2 paraphrasers.
- [`packet_order_diagnostic.md`](packet_order_diagnostic.md) plus `packet_order_*.csv` — packet-position/fatigue smoke test using public score-sheet order and exact response-text author matching, with item/judge adjusted residuals.
- [`scale_normalized_self_gap.md`](scale_normalized_self_gap.md) and [`scale_normalized_self_gap.csv`](scale_normalized_self_gap.csv) — recomputes self-preference gaps after within-judge/condition z-score and percentile normalization to check whether heterogeneity is a score-scale artifact.
- [`c2_stimulus_sheet_audit.csv`](c2_stimulus_sheet_audit.csv) and related C2-v2 preview reports — provenance checks for the Kimi-paraphraser v1→v2 refresh.

## Pending follow-up

- Kimi K2.6 native label-swap S1+S2 rows are still pending. When they land, rerun the paired label-swap analyzers, `paired_label_swap_lojo.py`, and the headline audit, then update the primary narrative outputs.
- Quality-balanced follow-up responses are complete for Claude, Gemini, and GPT-5.5; Kimi responses are still pending before packets and native scoring can proceed.
