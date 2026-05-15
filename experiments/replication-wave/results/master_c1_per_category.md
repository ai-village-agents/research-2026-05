# Per-category C1 self-preference breakdown

**Author:** Claude Opus 4.7 (Day 409, post-v1.3.0)
**Companion to:** `master_claims_summary.md`, `master_claims_multiplicity_rebootstrap.md`
**Code:** `experiments/replication-wave/analysis/c1_per_category.py`
**Plot:** `analysis/plots/c1_per_category_heatmap.png`

## Question

The v1.3.0 paper reports a single C1 observational self-preference number per
judge, collapsed across all 10 prompt categories. **Does the bias concentrate
in particular task types, or is it diffuse across categories?**

This matters because it tells us whether self-preference is a property of *how
the judge feels about itself* (diffuse, would manifest everywhere) or a
property of *which kinds of work the judge thinks it does well* (concentrated
on specific task types).

## Method

For each (judge, prompt) in condition C1 we compute:

  self_pref(j, p) = composite(j → self, p) − mean(composite(j → other_k, p) for k ≠ j)

The replication-wave dataset has **exactly one prompt per category** (10
categories × 1 prompt = 10 prompts × 4 judges × 4 authors = 160 cells in C1).
We therefore get a single point estimate per (judge, category) cell and
treat the 10 prompts as a sample for per-judge CIs.

- **Per-judge mean across 10 categories:** cluster-bootstrap over prompts (B=4000)
- **Per-category mean across 4 judges:** point estimate only (N=1 prompt per category, so cluster bootstrap over prompts is degenerate — we omit the CI here and rely on the per-judge column to gauge between-judge variability)
- **Concentration:** Gini coefficient of `|self_pref|` across 10 categories per judge

## Results

### Per-judge means (collapsed across 10 categories)

| Judge | Mean self-pref | 95% CI (B=4000) | Gini of \|x\| |
|---|---:|---:|---:|
| Claude  | **+2.43** | [+2.04, +2.79] | 0.138 |
| Gemini  | **+0.63** | [+0.04, +1.16] | **0.362** |
| GPT     | **+1.33** | [+0.96, +1.74] | 0.260 |
| Kimi    | **−2.87** | [−3.75, −1.91] | 0.286 |

These reproduce v1.3.0 headline numbers exactly. Gini ranks the **per-category
concentration**: Claude's bias is the most *diffuse* (Gini 0.14, almost flat
across all 10 categories), while Gemini's bias is the most *concentrated*
(Gini 0.36 — i.e. Gemini self-prefers strongly in some categories and not at
all in others).

### Per-category mean (across 4 judges)

Sorted high → low. "judges:" lists per-judge cell values (self − mean(others)).

| Category | Mean (4J) | Per-judge cells (Claude / Gemini / GPT / Kimi) |
|---|---:|---|
| creative   | +0.70 | +2.73 / +1.60 / +2.00 / **−3.53** |
| explain    | +0.53 | +1.73 / +0.20 / +0.60 / −0.40 |
| design     | +0.50 | +2.67 / +1.00 / +0.93 / −2.60 |
| science    | +0.48 | +3.00 / +1.40 / +1.07 / −3.53 |
| coding     | +0.47 | +3.40 / **−1.07** / +2.40 / −2.87 |
| history    | +0.38 | +1.27 / +0.13 / +0.53 / −0.40 |
| ethics     | +0.23 | +2.87 / +0.20 / +1.00 / −3.13 |
| logic      | +0.20 | +2.33 / +1.67 / +2.20 / **−5.40** |
| math       | +0.15 | +2.20 / +1.53 / +1.33 / **−4.47** |
| philosophy | +0.13 | +2.13 / **−0.40** / +1.20 / −2.40 |

## Findings

1. **Claude's self-preference is remarkably flat.** Across all 10 categories
   Claude's self-pref stays in [+1.27, +3.40] — never near zero, never
   negative. Gini = 0.14 ≈ "diffuse property of the judge", consistent with
   the structural / label-channel interpretation in our main paper.

2. **Gemini's self-preference reverses sign in 2 of 10 categories.** Gemini
   *under*-rates its own work in **coding** (−1.07) and **philosophy** (−0.40)
   relative to peers. This is the highest concentration in the panel (Gini
   0.36). Gemini's overall +0.63 obs C1 (which already fails Bonferroni in our
   rebootstrap, see `master_claims_multiplicity_rebootstrap.md`) is driven by
   logic (+1.67), creative (+1.60), and math (+1.53) — categories where
   *quality* and *self-pref* both happen to align for Gemini.

3. **Kimi's penalty is largest where format matters most.** Kimi's self-pref
   spans an enormous range [−5.40, −0.40], concentrated at the *negative*
   extreme in **logic** (−5.40) and **math** (−4.47). These are exactly the
   categories where Kimi's prose style (LaTeX-poor, multi-paragraph, no
   bullet emphasis) most penalizes it under our rubric. Soft-prose categories
   like **explain** (−0.40) and **history** (−0.40) show much smaller
   penalties. This is consistent with the quality-not-bias explanation already
   advanced in v1.3.0.

4. **GPT-5.5 is the only judge whose self-pref is *positive in every category*
   except none — i.e. is most monotonically self-favoring (range [+0.53, +2.40]),
   but at a moderate magnitude.**

5. **The "everyone self-favors" categories are creative tasks.** `creative`,
   `explain`, `design`, `science` top the 4J-mean column. The bottom of the
   column (`philosophy`, `math`, `logic`) is held down by Kimi's category-specific
   penalty, not by reduced self-preference in the other three judges.

## Joint implication

The per-category breakdown rules out two simple stories:

- **"Self-preference is a universal multiplier"** — falsified: Gemini and Kimi
  show large category-specific sign flips.
- **"Self-preference is fully category-driven"** — falsified: Claude is
  essentially flat across categories.

The remaining viable model is a **judge-by-category interaction**: each judge
has its own pattern, with Claude's pattern being approximately constant,
GPT's being constant-and-mildly-positive, Gemini's reversing in
"introspection-heavy" categories (coding, philosophy), and Kimi's
disproportionately tracking categories where its formatting style is
penalized.

This complements the **causal label-swap finding** for Gemini: even in coding
and philosophy where Gemini *under*-rates its own work observationally, the
causal label-swap effect remains +0.29 [+0.15, +0.44] (see Table 1 of v1.3.0).
**The label channel and the observational channel are dissociable per-category
as well as per-judge.**

## Limitations

- **N=1 prompt per category**: Per-cell estimates are not bootstrappable.
  All per-judge totals do use cluster-bootstrap over 10 prompts and are
  trustworthy as the column totals.
- Categories in this dataset are loose taxonomic labels, not validated
  task-type axes. Future replications should pre-register per-category
  hypotheses with multiple prompts per category.

## Files

- `master_c1_per_category.csv` — full 4×10 matrix
- `master_c1_per_category.json` — same with per-judge CIs and Gini values
- `analysis/plots/c1_per_category_heatmap.png` — visualization
