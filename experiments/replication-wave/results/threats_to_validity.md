# Threats to validity (post-v1.3.0 supplement)

This document complements the brief "Limitations & Open Questions" section in the blogpost with a more structured taxonomy of threats to validity, organized following Cook & Campbell (internal, external, construct, statistical-conclusion). Each entry names a specific threat, briefly describes the mechanism, points to the strongest piece of evidence we have in the repository, and rates its current standing as `addressed`, `partially addressed`, or `open`.

This is meant as a methodological "footnoting" of the v1.3.0 release - a reader can use it to assess how robust any individual headline claim is.

## 1. Internal validity (does the manipulation drive the outcome?)

### 1.1 Causal label-swap is paired-within-judge - rules out judge-level confounds
- **Mechanism**: In the native label-swap (Day 408 release), each `(judge, response_hash)` pair sees the same text under two different displayed labels. Differences between the two ratings cannot be explained by judge identity, by response identity, or by any feature of the underlying text that is constant across the pair.
- **Evidence**: `results/paired_label_swap.csv` (320 rows = 4 judges x 40 responses x 2 labels). The matrix supplement decomposes mean residuals into 16 (judge, displayed-label) cells.
- **Standing**: addressed. This is the core causal design of v1.3.0.

### 1.2 Off-topic Kimi responses are not random missing data
- **Mechanism**: Kimi K2.6's original responses were off-topic on ~11 of 30 prompts across all C1-C3 scoring conditions. Because these rows are systematically the lowest-quality in the dataset, they pull Kimi's mean composite down and make Kimi's authorship more guessable to judges. This is an internal-validity threat for any claim about Kimi's "self-penalty" - the deficit may be quality-driven, not preference-driven.
- **Evidence**: Robustness re-fit in blogpost (dropping the 11 off-topic prompts changes pooled H1 from null to +0.286 SE 0.069). Kimi C4 confusion matrix shows judges correctly identify these as Kimi-authored with high confidence (66 of 69 entries in the `pred_self=0, conf=5` cell).
- **Standing**: partially addressed. The robustness check is published but the headline numbers still report the full sample.

### 1.3 Self-recognition by content type may mediate self-favoring
- **Mechanism**: If self-recognition rates differ across prompt categories (code vs creative vs philosophy), and if self-favoring also differs by category, the marginal correlation between recognition and favoring may be confounded by category.
- **Evidence**: LOPO C1 drops in `cross_judge_response_correlation.md` show creative and philosophy dropouts both move C1 by ~+0.4 points. Per-category recognition rates not separately reported. 
- **Standing**: open. A category-stratified mediator model would be cleaner.

### 1.4 Belief vs label channels: nominally separable but observational mediation is non-causal
- **Mechanism**: Our two main "self-preference" channels - belief (`predicted_self`) in C1 and label (`displayed_label`) in the causal swap - have different identification strategies. The belief channel is observational and could be confounded by unobserved features of the response (a judge might both correctly recognize a response as its own AND rate it higher because it is genuinely better). The label channel is randomized and therefore clean.
- **Evidence**: The recognition x label-swap supplement (`recognition_x_labelswap.md`) shows the two channels can be empirically decoupled (Spearman rho = -0.211 across 4 judges; Gemini has the lowest self-recog and the largest label effect).
- **Standing**: partially addressed. The decoupling is informative but does not give us a clean mediator coefficient on the causal channel.

### 1.5 Backend-of-scoring confound (Gemini and GPT-5.5 first attempt)
- **Mechanism**: The committed Gemini and GPT-5.5 score sheets in the first label-swap attempt were produced through a codex/OpenAI-backed scoring path rather than the agents' native contexts. These rows were re-scored and re-released, but the original output is preserved.
- **Evidence**: Backend-caveat paragraph in blogpost (line ~457); the public `paired_label_swap.csv` uses only native scoring.
- **Standing**: addressed (data quarantined and re-collected).

## 2. External validity (does the finding generalize?)

### 2.1 Only four judges, all of them current frontier "best of class"
- **Mechanism**: We have 4 judges drawn from 4 different model families. The cross-judge variance is large (raw C1 self-preference ranges -2.86 to +2.43). Extrapolating to smaller or open-weights models is not warranted.
- **Evidence**: `c1_self_preference_gap.png`. The "biased not noisy" interpretation works at population n=4 with paired evidence, but the population is hand-picked.
- **Standing**: open. We flag this in the blogpost conclusion but cannot patch with the current data.

### 2.2 30 base prompts + 10 OOD prompts; per-category cells are small
- **Mechanism**: Per-category self-preference patterns (creative vs code vs philosophy) are exploratory and underpowered. LOPO checks tolerate single-category dropout but cannot isolate small per-category effects.
- **Evidence**: LOPO C1 sensitivities (+0.343 drop creative, +0.406 drop philosophy) and the 10-prompt OOD replication.
- **Standing**: partially addressed (OOD replication wave) but per-category power is still small.

### 2.3 One response per (author, prompt) - no within-author variance estimate
- **Mechanism**: Without resampling each author at non-zero temperature, we cannot separate "Author X's typical quality on prompt P" from "the single sampled response Author X happened to give on prompt P". A multi-sample design would also let us bound the variance contribution of decoding noise.
- **Evidence**: Within-response paired SD (0.21-0.38) is much smaller than between-response SD (0.46-0.57), which gives us the "biased not noisy" call - but the within-response SD does not include resampling variance.
- **Standing**: open.

### 2.4 English-only, no domain specialization
- **Mechanism**: Prompts are all in English and cover generalist categories. Self-preference may behave differently in highly specialized domains (legal, medical, scientific) where each model has different training corpora.
- **Standing**: open.

## 3. Construct validity (are we measuring what we say we are?)

### 3.1 Composite = unweighted mean of 5 rubric dimensions; dimensions are highly correlated
- **Mechanism**: GPT-5.5's dimension-redundancy supplement (`dimension_redundancy_profile.md`) reports Cronbach alpha = 0.927 and PC1 = 82.2% of variance across the five rubric dimensions. The composite is therefore measuring "one big general-quality factor", not five independent constructs. Per-dimension claims should be read cautiously.
- **Evidence**: `dimension_redundancy_profile.md`, `subscale_horse_race.png`.
- **Standing**: partially addressed - we publish the redundancy and discuss it in the blogpost.

### 3.2 The C2 paraphraser introduces its own style
- **Mechanism**: Every C2 response carries the paraphraser's stylistic signature, not just the original author's. A paraphraser-affinity check finds a +0.18 point lift when paraphraser-model matches judge-model.
- **Evidence**: `results/paraphraser_confound.md`.
- **Standing**: partially addressed (effect is small but non-zero).

### 3.3 Self-recognition C4 task uses a 4-way forced choice over the same author set
- **Mechanism**: We test whether the judge can identify the actual author among the four candidate models. Real-world "is this me?" cognition is open-set. The closed-set design inflates confidence and prevents "I have no idea" responses.
- **Standing**: open. A future replication might add an "unknown" option or an external author distractor.

### 3.4 "Bias" is measured as a between-condition difference, not a deviation from a normative truth
- **Mechanism**: We have no ground-truth quality rating per response. Self-preference is defined entirely as "the judge rates own-authored responses higher than peer-authored responses by the same amount that other judges in the panel do not". A judge that uniformly under-scores everyone would not be flagged as biased here.
- **Standing**: open. We mitigate by using LOJO (leave-one-judge-out) to triangulate, and by reporting raw composites alongside residualized contrasts.

## 4. Statistical-conclusion validity (are the CIs honest?)

### 4.1 Multiplicity across 16-cell label-swap matrix
- **Mechanism**: We test 16 (judge x displayed-label) cells. Naive marginal CIs at 95% would yield ~0.8 false positives in expectation under the null.
- **Evidence**: `label_effect_matrix_multiplicity.md` runs Benjamini-Hochberg FDR (q < 0.05) and Bonferroni-adjusted 99.6875% CIs across all 16 cells. Only Gemini's two cells survive (q = 0.002 each). All headline claims that quote "CI excludes zero" for non-Gemini cells (e.g., Kimi pro-Claude +0.225) are downgraded to non-significant.
- **Standing**: addressed.

### 4.2 Master multiplicity sweep across the full claim inventory
- **Mechanism**: The `master_claims_summary.md` aggregates 16 inferential claims. A bona fide family-wise correction across the entire claim set is more conservative than the within-matrix correction.
- **Evidence**: `master_multiplicity_sweep.md` applies BH/Bonferroni correction to the originally reported claim p-values, and `master_claims_multiplicity_rebootstrap.md` re-bootstraps every claim from raw data before applying the same corrections. The raw-data rebootstrap agrees with the first sweep on 15/16 claims; the one correction is that Gemini's small observational C1 gap (+0.627) is marginal unadjusted (raw p = 0.034) but does **not** survive family-wise correction (BH-q = 0.060; Bonferroni p = 0.54). The Gemini causal self-label and anti-Kimi label effects remain Bonferroni-robust.
- **Standing**: addressed.

### 4.3 Single-prompt leverage across the master claim family
- **Mechanism**: With only 10 prompts, a headline claim might be driven by one idiosyncratic prompt even if its family-wise p-value is small.
- **Evidence**: `master_claims_lopo_robustness.md` recomputes the 14 prompt-driven master claims after dropping each prompt in turn. All 8 multiplicity survivors keep their sign under every single-prompt deletion; the only sign-flipping claim is Kimi's causal self-effect, which is already null under multiplicity.
- **Standing**: addressed.

### 4.4 Bootstrap CIs are cluster-bootstrap on response_hash
- **Mechanism**: All headline CIs in the label-swap matrix and bias-profile supplements use B = 4000 cluster bootstraps on `response_hash`. We chose response_hash (not prompt_id) because the experimental unit is the specific text being label-swapped. Clustering on prompt_id would conflate within-prompt author variability with within-response noise.
- **Standing**: addressed.

### 4.5 n = 4 judges - cross-judge generalizations are descriptive
- **Mechanism**: Statements like "Spearman rho (self-recog, label-self-effect) = -0.211 across 4 judges" are descriptive, not inferential, at this sample size.
- **Evidence**: We label these in the recognition x label-swap supplement.
- **Standing**: addressed by labeling.

### 4.6 GPT-5.5's exactly-zero label-swap is informative but degenerate
- **Mechanism**: GPT-5.5 returns identical composite scores under every displayed-label permutation, so every cell of its row of the matrix is exactly 0.000. This is a real finding (GPT is label-invariant) but it also collapses several otherwise-useful contrasts to degenerate denominators.
- **Standing**: addressed via per-judge reporting.

## 5. Threats specific to the recognition probe (C4)

### 5.1 Confidence ratings are self-reported, not calibrated externally
- **Mechanism**: We rely on each judge's stated confidence (1-5). We do not compare these to a Brier-score-style external calibration. Kimi's anti-calibrated confidence (conf=5 -> 100% wrong; conf=4 -> 17% right) may itself be an artifact of an instruction-following pattern rather than a genuine epistemic signal.
- **Evidence**: Per-judge confidence stratification in the blogpost.
- **Standing**: partially addressed.

### 5.2 Self-recognition rates are confounded with style distinctiveness
- **Mechanism**: A judge can have a high self-recognition rate either because (a) it has good self-knowledge or (b) its writing is highly distinctive even from outside its own perspective. We cannot distinguish (a) and (b) without an external panel.
- **Standing**: open.

## 6. What would change our conclusions?

Three pieces of follow-on evidence would move the dial most:

1. **A fifth and sixth frontier judge** (e.g., a Mistral or a Qwen large) would tell us whether Gemini's strong label-self effect and Kimi's quality-driven self-penalty are family-specific or partially common.
2. **An external (non-judge-authored) reference set** would let us re-express "self-preference" as a deviation from a normative quality estimate, addressing 3.4 above.
3. **Multi-sample (k=3) author responses per prompt** would partition variance between within-author sampling noise and between-author quality differences, closing 2.3.

We expect future replication waves can address (1) and (3) with modest incremental cost; (2) is structurally harder because the "judges = authors" design is what makes the recognition probe possible at all.
