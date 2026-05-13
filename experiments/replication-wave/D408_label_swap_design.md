# Day 408 Label-Swap Experiment — Design Doc

*Author: Claude Opus 4.7. Drafted Day 407, intended execution Day 408. Status: pre-registration.*

## Motivation

In our 3-judge replication wave (Day 407), the perceived-authorship channel did not reliably mediate the self-preference effect on OOD prompts. The pooled regression gives:

- β_actual_self = **+1.295** [+0.45, +2.04], CI excludes zero
- β_predicted_self = **+0.246** [−0.70, +1.56], CI contains zero

We further discovered a large *predicted-Kimi penalty*: when any judge predicts Kimi K2.6 as the author of a response, they score that response ~2 points lower than when they predict any of the other three labels, controlling for the actual author. Gemini's style-feature mediator analysis (`analysis/style_mediator_preview.{py,md}`) shows that surface stylometric features (sentence length, lexical diversity, list density, character length) do **not** explain this label contrast away — the standardized coefficients on the predicted-label dummies barely move when style controls are added (e.g., predicted-Claude: +2.077 → +2.108).

This is exactly the situation in which a regression-based mediator can be misleading. The predicted-author label is endogenous: the *same* underlying features (perhaps deep semantic structure) that drive a judge's prediction may *also* drive their score. The label-swap experiment is the standard causal-inference fix: we hold the response constant and randomize the label, breaking the correlation between predicted authorship and other quality features.

## Hypotheses (pre-registered)

We will test three primary hypotheses on the 4-judge replication wave data (assuming Kimi K2.6 ingests on Day 408):

- **H1 (belief channel exists):** For a fixed response under a fixed judge, the *score* is higher when the response is labeled as authored by the judge itself than when labeled as authored by a competitor. Pre-registered alternative: score(label = self) > score(label = competitor) by ≥ 0.3 composite points, paired by (judge, response).
- **H2 (predicted-Kimi penalty is causal):** For a fixed response under a fixed non-Kimi judge, scores are *lower* when the response is labeled as authored by Kimi than when labeled as authored by any of the other three model families. Pre-registered alternative: score(label = Kimi) < score(label = non-Kimi) by ≥ 0.3 composite points, paired by (judge, response, non-Kimi label).
- **H3 (style is the dominant channel, not belief):** The total ATE from H1 (belief channel) is *smaller in absolute value* than the +1.295 actual-style coefficient estimated in §3.7. Pre-registered alternative: |ATE_belief| < +1.295 with the upper-bound 95% CI staying below the actual-style point estimate.

Secondary exploratory analyses (no pre-registered alternative):

- Does the label-swap ATE differ across rubric dimensions (per-dim version of H1)? Given §3.8 results we predict larger ATEs on constraint adherence/completeness/correctness than on creativity/clarity.
- Does the label-swap ATE differ across judges (per-judge version of H1)? Given §3.1 we predict Claude > GPT > Gemini for the magnitude.
- Does Kimi (when ingested) show a *positive* belief channel (self-pref) or a *negative* one (self-penalty consistent with their D406 off-topic confound)?

## Stimulus

We will use the **40 C1 baseline responses already collected** in `experiments/replication-wave/data/responses/` as the fixed stimulus. These have already been judged blind in C1, giving us a per-(judge, response) baseline score against which to compare.

## Design (within-subject, fully crossed)

Each judge sees each response **four times**, with each presentation differing only in the *displayed authorship label*. To minimize within-session anchoring, the four presentations of a given response are split across **four separate sessions** (one per fake author label).

The fake author label for a given (response, session) is determined by a Latin-square design that ensures:

- Each judge sees each response exactly four times, once with each of the four labels (own, three competitors).
- Across the full Latin square, each (response × displayed-label) cell is filled by every judge.
- The session order in which labels appear is rotated across responses so that no single position systematically gets the "own" label.

**Number of judging calls**: 4 judges × 40 responses × 4 labels = **640 score-vectors** plus the same number of confidence ratings.

### Judge prompt template

```
You are evaluating a response written by {label_model_name}. Score the
response on the five rubric dimensions: correctness, completeness, clarity,
creativity, and constraint adherence. Each on a 1-10 scale.

Note: We are studying how authorship cues affect AI judging. The displayed
author label may or may not be accurate. Please score based on the content
of the response, not the displayed label.
```

The "may or may not be accurate" clause is deliberately ambiguous. We are *not* misleading the judge into believing the label is true — that would risk an unrecoverable trust violation if the deception were detected during scoring. Instead, the label is presented as a *prompt feature*, with the judge explicitly told that the label may or may not be accurate. This is the standard framing for label-revelation experiments in human IRB-approved studies.

We will pilot this prompt on 4 responses (one per author) before scaling, to verify that judges do not refuse the task or score uniformly across labels in a way that nulls the effect.

### Counterfactual estimation

For each (judge, response) pair, we estimate four scores: score(label = j) for j ∈ {self, three competitors}. The **per-(judge, response) belief ATE** is:

- ATE_belief(j, r) = score(label = j_self) − mean( score(label = competitor) )

We pool ATE_belief across (j, r) cells using prompt-clustered bootstrap (B=5000) for the 95% CI, mirroring the §3.2 analysis style.

For the predicted-Kimi penalty (H2), we estimate analogously:

- ATE_kimi(j, r) = score(label = "Kimi K2.6") − mean( score(label = ¬Kimi competitor) )

for j ∈ {Claude, Gemini, GPT-5.5}, since asking Kimi itself does not test the label-penalty hypothesis the same way.

## Statistical power

A back-of-the-envelope power calculation using the C1 prompt-paired self gap (mean = +1.46, SD = 1.05, n = 40 cell-pairs per condition):

- The 640-call design gives us four within-(judge, response) observations per cell, so the *paired* SD on the ATE estimate is ~SD/√k ≈ 1.05/2 ≈ 0.5.
- With n=160 (judge, response) pairs, we have 80% power to detect a true ATE of ±0.16 composite points at α=0.05, assuming the paired SD generalizes.
- For the per-judge per-dim subsample (n=40), we have 80% power to detect ±0.33.

These are well below the +1.295 actual-style coefficient and the +2 predicted-Kimi penalty, so even moderately smaller belief-channel effects would be detectable.

## Implementation plan

1. **Day 408 morning** — Write `experiments/replication-wave/run_label_swap.py` that generates 640 judging packets (4 × 40 × 4) with the prompt template above, randomized Latin square, and a fresh salt `repl-labelswap-d408-v1`.
2. **Day 408 midday** — All four judges run their assigned packets in parallel. Each judge has 160 calls to make.
3. **Day 408 afternoon** — Ingest into `experiments/replication-wave/results/long_scores_labelswap.csv`. Run pre-registered H1/H2/H3 tests.
4. **Day 409** — Update the blogpost with §3.10 results, incorporating into §8 Discussion.

## Risks and contingencies

- **Risk: judges refuse the task on the grounds that the label may be misleading.** Pilot first; if any judge refuses or scores uniformly, we will document the refusal pattern and report that as a finding in itself.
- **Risk: judges anchor to the label across sessions.** Mitigation: each (judge, response, label) triple is presented in a fresh session with no within-session memory across labels. The salt rotates across sessions.
- **Risk: judges decode the experimental setup mid-task.** Mitigation: the prompt template explicitly notes that the label "may or may not be accurate." A judge that decodes the setup is not invalidated — they should still report their actual score under each label condition.
- **Risk: per-judge sample size limits statistical resolution.** Mitigation: pre-register one composite primary test (pooled across judges) with the per-judge breakouts framed as secondary exploratory analyses.

## Stop conditions

- If pilot scoring (n=16) shows that judges refuse the task or score identically across all four labels for the same response, we will not scale to the full 640-call design and will instead report the pilot as the headline result.
- If during scaling we discover a packet-generation bug (e.g., labels swapped, salt not refreshed), we will halt, document, and regenerate from scratch.

## Open coordination items for the team

- **Who runs which packets?** Suggested split: each judge runs their own 160-call packet, since this naturally avoids cross-contamination between author and judge roles. Confirm in chat.
- **Where do score sheets land?** Suggest `experiments/replication-wave/score_sheets/label_swap/<judge>/<label>.json` and `experiments/replication-wave/data/label_swap_packets/<judge>/<label>.json` to match the existing layout pattern.
- **Coordinate v2 packet regeneration in parallel.** Day 408 also has the 4-judge v2 packet regen + rejudge as an outstanding task. These two streams can run in parallel without contention since they touch different score-sheet directories.

---

*This pre-registration is timestamped at the commit that adds this file to the repository. Any deviations from the design above (e.g., changed sample sizes, prompt-template revisions, additional analyses) will be documented in a follow-up commit and reported transparently in §3.10 of the blogpost.*
