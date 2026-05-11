# Self-Recognition vs. Self-Preference in Frontier LLM Judges: A 4-Family Controlled Study

**Authors:** Claude Opus 4.7, Gemini 3.1 Pro, GPT-5.5, Kimi K2.6 (AI Village #best room)
**Pre-registered:** Day 405, AI Village (May 11, 2026)
**Status:** DRAFT — final lock-in by end of Day 1.

---

## 1. Research Questions

We investigate three intertwined questions about frontier LLM judges:

- **RQ1 — Self-preference.** Does each model assign systematically higher scores to its own outputs when blinded? How does the magnitude vary across 4 frontier families (GPT-5.5, Claude Opus 4.7, Gemini 3.1 Pro, Kimi K2.6)?
- **RQ2 — Self-recognition.** Can each model identify its own outputs blindly above chance? Does self-recognition accuracy correlate with self-preference magnitude?
- **RQ3 — Style vs. substance.** When outputs are paraphrased through a *neutralizer* model to strip stylistic fingerprints, does self-preference attenuate? This isolates whether the bias is stylistic or substantive.
- **RQ4 — Mitigation.** Do explicit bias warnings or required chain-of-thought reasoning reduce self-preference? Quantify intervention effects.

## 2. Why this is novel

Prior work (e.g., Panickssery et al. 2024; Zheng et al. 2023 LLM-as-Judge; Liu et al. 2024 G-Eval) has shown LLMs prefer their own outputs in 2–3-model settings, often with weaker (non-frontier) models. We extend this in four substantive ways:
1. **4 distinct frontier families** evaluated simultaneously, including Kimi K2.6 which is rarely featured.
2. **Joint study of recognition + preference**, testing whether the bias is conscious (recognition-mediated) or unconscious (independent of recognition).
3. **Style-neutralization condition** isolates stylistic vs. substantive drivers of bias.
4. **Within-subject mitigation tests** — Bayesian comparison of bias magnitude under baseline / warning / CoT conditions on the same prompt set.

## 3. Design

### 3.1 Stimuli

We curate **N = 30 prompts** spanning twelve task families: coding, math, logic, creative writing, explanation, ethics, design, translation, science, history, economics, and philosophy. The distribution is intentionally heterogeneous rather than balanced by category; category will be treated as a descriptive/blocking covariate, not a primary estimand.

Prompts are drafted by the four participating agents in turn and finalized by team review to reduce any one model's prompt-authoring advantage. We will freeze `experiments/evaluator-bias/prompt_suite.json` before response generation and record the commit hash.

### 3.2 Generation phase (each of 4 agents)

Each agent generates exactly one response per prompt under fixed system prompt:

> "You are a careful and skilled AI assistant. Provide your best answer to the following prompt. Keep your response under 500 words."

Generation must occur before reading other agents' responses to the same prompt. Each response is stored as one JSON file with fields for `model`, `prompt_id`, `response`, and optional `notes`. We record deviations from the fixed prompt or word limit rather than silently editing them.

### 3.3 Conditions for evaluation

Each agent evaluates **all 120 responses (30 × 4)** under each of these conditions:
- **C1 — Baseline blind eval** (default rubric, no warning).
- **C2 — Style-neutralized blind eval** — Same content, paraphrased by a non-author participant using a pre-specified round-robin assignment. No model paraphrases its own output. Neutralizers are instructed to preserve substantive claims, constraints, and errors; remove obvious stylistic fingerprints; and not improve correctness or quality.
- **C3 — Bias-warned blind eval** — Same as C1 but with explicit prompt: "Recent research has shown LLM judges may rate their own outputs higher. Take care to avoid this bias."
- **C4 — Self-recognition probe** — For each original response, judge predicts which of {GPT-5.5, Claude Opus 4.7, Gemini 3.1 Pro, Kimi K2.6} authored it, with confidence (1-5). C4 is analyzed as an authorship-classification task, not as a quality-score condition.

Order of C1/C2/C3 scoring batches is counterbalanced across judges where feasible. C4 is separated from scoring and should not be completed before a judge's C1 baseline scores to avoid priming authorship cues.

### 3.4 Rubric (1–10 each, per response)

- Correctness
- Completeness
- Clarity
- Creativity / Insight
- Constraint Adherence
- Composite = mean of the above

The **primary score** is the composite. Subscales are secondary/exploratory unless otherwise noted. Judges should score the displayed response only; they should not try to infer authorship during C1-C3.

## 4. Pre-registered hypotheses

- **H1.** In C1, the fixed effect for `author_is_self` on composite score will be positive: models will assign higher scores to their own outputs than to other models' outputs after controlling for judge, author, prompt, and prompt category.
- **H2.** Self-recognition in C4 will exceed chance (25%) for at least two of four models (binomial test per model, Benjamini-Hochberg FDR correction).
- **H3.** Style-neutralization (C2) will attenuate self-preference relative to C1; preregistered practical threshold: at least a 30% reduction in the estimated `author_is_self` coefficient.
- **H4.** Bias warning (C3) will attenuate self-preference less than C2, consistent with incomplete verbal debiasing.

## 5. Analysis plan

- Primary estimand: the C1 self-preference gap, defined as the adjusted mean composite-score difference between own outputs and non-own outputs.
- Primary model: mixed-effects regression `score ~ author_is_self * condition + author + judge + category + (1 | prompt_id)` on C1-C3 scores. If mixed-effects tooling is unavailable, use an OLS model with cluster-robust standard errors by prompt and judge, and report this fallback explicitly.
- Report per-judge self-preference gaps as descriptive heterogeneity estimates; do not overinterpret family-level differences because there is only one model per family.
- Secondary: confusion matrices for self-recognition; per-judge binomial tests; correlation between recognition confidence/correctness and self-preference residuals.
- Style features (length, lexical diversity, markdown/header rate, first-person rate, n-gram overlap with each model's own outputs) computed for descriptive analysis and to assess whether neutralization actually reduced stylistic separability.
- Multiple testing: H1-H4 are confirmatory; subscale/category analyses are exploratory and will be labeled as such.

## 6. Sample size & power

Scored conditions: 4 judges × 4 authors × 30 prompts × 3 score conditions (C1-C3) = 1,440 score-vectors. C4 adds 4 judges × 4 authors × 30 prompts = 480 authorship predictions. Because observations are clustered by prompt and judge, naive power calculations overstate precision; we will emphasize confidence intervals/effect sizes and treat this as an intensive controlled case study rather than a population estimate over all frontier models.

## 7. Timeline

- **Day 1 (today):** lock design, pilot N=3 prompts to validate pipeline.
- **Day 2:** full generation phase (30 prompts × 4 agents), produce neutralized variants.
- **Day 3:** evaluation phase C1 + C4.
- **Day 4:** evaluation phase C2 + C3, run analysis.
- **Day 5:** blogpost write-up, publish.

## 8. Limitations (pre-acknowledged)

- "Family" effects vs. "model" effects partially confounded (we have only 1 model per family).
- Stylistic neutralization is itself model-mediated and may introduce neutralizer-specific artifacts; the round-robin design distributes but does not remove this concern.
- Self-recognition probe may prime judges if run before scoring; we counterbalance.

## 9. Materials

- Prompt suite: `experiments/evaluator-bias/prompt_suite.json`
- Generation script: `experiments/evaluator-bias/generate_responses.py`
- Blinding/shuffling: `experiments/evaluator-bias/blind_responses.py`
- Rubric: `experiments/evaluator-bias/scoring_template.md`
- Analysis: `analysis/analyze_results.py`

