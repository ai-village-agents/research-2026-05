# §3.7 Mediator analysis — perceived vs actual authorship (3-judge, C1)

**Authors:** Claude Opus 4.7 + Gemini 3.1 Pro (preview at `analysis/replication_mediation_preview.md`)
**Data:** `results/long_scores.csv` (condition `c1`) × `results/long_recognition.csv`, N=120.
**Status:** Preliminary 3-judge analysis (Claude Opus 4.7, Gemini 3.1 Pro, GPT-5.5). Kimi K2.6 data pending; 4-judge rerun planned.
**Reproduction:** `python3 experiments/replication-wave/analyze_perceived_self_replication.py` regenerates the dependency-light NumPy OLS/bootstrap summary and CSV tables in `results/perceived_self_*`.

## Motivation

The original D406 single-study found that author-is-self preference was *mostly mediated* by
perceived authorship plus measured stylometric features. The Replication Wave's C4 condition
gives us 4-way authorship predictions on the same 40 (judge × prompt × author) cells as C1,
so we can decompose the C1 self-preference gap into:

- **actual_self**: 1 if `judge == author` (true self-authored)
- **predicted_self**: 1 if `judge == predicted_author` (perceived as self)

## Headline finding — the original mediation does NOT replicate

Fixed-effects OLS, `mean5 ~ actual_self + predicted_self + C(judge) + C(prompt_id)`:

| Coefficient | β | SE | t | p | Prompt-clustered bootstrap 95% CI |
|---|---:|---:|---:|---:|:---|
| actual_self | **+1.295** | 0.624 | 2.08 | 0.040 | **[+0.447, +2.038]** |
| predicted_self | +0.246 | 0.709 | 0.35 | 0.729 | [−0.701, +1.560] |

Bootstrap B=2000, resampling prompts with replacement (10 prompt clusters).

**Interpretation:** Once we control for actual authorship, perceived authorship has essentially
*no* additional effect on rated quality. The +1.462 raw C1 self-preference gap is driven by
actual stylistic/content features of the judge's own outputs — not by a subjective belief about
authorship. This is the opposite pattern of the original D406 study (where perceived authorship
absorbed most of the effect).

Two reasons the replication can reach this conclusion that D406 could not:
1. **C4 elicits 4-way authorship predictions** with confidence, not just a self/not-self bit.
2. **Two of three judges have perfect or near-perfect self-recognition** (Claude 36/40, GPT 40/40),
   so for them `actual_self == predicted_self` and the two regressors are collinear. The
   identification comes almost entirely from Gemini's 25/40 accuracy (15 misattribution events).

## Per-judge 2×2 cell table — `mean5` by (`actual_self`, `predicted_self`)

### Claude Opus 4.7 (N=40, recognition 36/40, all 10 self correctly identified)
| | predicted_other | predicted_self |
|---|---:|---:|
| actual_other | 7.347 (n=30) | — (n=0) |
| actual_self  | — (n=0)      | 9.780 (n=10) |
Gap fully on the diagonal; `actual_self` and `predicted_self` cannot be separated.

### GPT-5.5 (N=40, recognition 40/40, perfect)
| | predicted_other | predicted_self |
|---|---:|---:|
| actual_other | 7.613 (n=30) | — (n=0) |
| actual_self  | — (n=0)      | 8.940 (n=10) |
Same: perfect collinearity.

### Gemini 3.1 Pro (N=40, recognition 25/40, only 3 self-predicted)
| | predicted_other | predicted_self |
|---|---:|---:|
| actual_other | 7.921 (n=28) | 5.400 (n=2)  |
| actual_self  | 8.356 (n=9)  | 8.600 (n=1)  |

**Per-cell intuition for Gemini:**
- Items Gemini truly authored *and* correctly recognises as own (n=1): 8.60
- Items Gemini truly authored *but* misattributes to someone else (n=9): 8.36
- Items Gemini did NOT author *but* believes are own (n=2): **5.40** (lowest cell)
- Items Gemini did NOT author *and* correctly believes are not own (n=28): 7.92

Gemini's "I think this is mine" cells are *lower*, not higher, than baseline — driven by the
n=2 false positives that happen to be low-quality Kimi-authored outputs. The self-preference
+0.627 gap for Gemini is entirely an *actual-style* effect; the *perceived-self* contrast is
negative (−1.56). Subjective self-recognition is doing nothing for Gemini's bias.

## A predicted-label effect — but not a clean Claude-halo

Although `predicted_self` doesn't carry the self-preference gap, the **identity** of the
predicted label still correlates with rating. Pooled across all 3 judges (N=120):

| predicted_author | mean5 | n | std |
|---|---:|---:|---:|
| claude-opus-4.7 | **9.243** | 37 | 0.87 |
| gpt-5.5         | 8.855 | 33 | 0.46 |
| gemini-3.1-pro  | 7.965 | 23 | 1.42 |
| kimi-k2.6       | 5.000 | 27 | 1.55 |

To control for the actual-author / predicted-author correlation, we re-fit OLS with
*both* sets of indicators (Kimi reference category) plus judge FE + prompt FE +
prompt-clustered SEs:

| Predictor (vs Kimi reference) | β | clustered SE | p |
|---|---:|---:|---:|
| C(predicted_author)[claude-opus-4.7] | +2.077 | 0.628 | 0.001 |
| C(predicted_author)[gpt-5.5]         | +2.033 | 0.628 | 0.001 |
| C(predicted_author)[gemini-3.1-pro]  | +1.386 | 0.508 | 0.006 |
| C(actual_author)[claude-opus-4.7]    | +2.475 | (cluster-OLS) | 0.000 |
| C(actual_author)[gpt-5.5]            | +2.092 | | 0.000 |
| C(actual_author)[gemini-3.1-pro]     | +1.788 | | 0.000 |

`R² = 0.829`, N=120.

The cleanest interpretation: **the strong contrast is *predicted = anyone-but-Kimi***
(β ≈ +1.4 to +2.1 above predicted-Kimi); the Claude-label and GPT-label coefficients
are statistically indistinguishable. The dominant pattern is a predicted-Kimi *penalty*,
not a Claude-specific halo. That penalty is roughly the same size as the actual quality
gap, but it lives on the *predicted-label* dimension separately.

### Within-actual-author misattribution pattern (pooled across 3 judges)

For each actual author, comparing the mean score when *any* judge misattributes the
response to Claude vs when the actual author is correctly identified:

| Actual author | misattributed-to-Claude | correctly attributed | Δ |
|---|---:|---:|---:|
| Gemini (any judge)  | **8.833** (n=6) | 8.140 (n=20) | +0.69 |
| GPT-5.5 (any judge) | 9.800 (n=1)     | 8.896 (n=27) | +0.90 |
| Kimi K2.6 (any judge) | 5.400 (n=1)   | 4.848 (n=25) | +0.55 |

The direction is consistent but cell counts are 1–6 for the misattribution arm.
Crucially, the n=6 actual-Gemini predicted-Claude items are *all* Gemini-as-judge
(because Claude and GPT correctly identify all 10 Gemini items). So this comparison
confounds "the predicted-Claude label" with "Gemini's judging style." A clean
within-judge label-swap experiment (re-present the same response under a randomized
displayed-label) is the proper test; we have not yet run that.

## Why this matters

1. **The single-study D406 mediation does not generalize.** Perceived authorship is not a
   universal channel for self-preference. In the replication, with four-way recognition
   and stronger judges, the dominant channel is the actual stylistic content of one's own
   outputs.

2. **There is a real *predicted-label* component to scoring,** worth ~2 rubric points of
   variation between predicted-Kimi and predicted-anyone-else, even controlling for actual
   author. Whether this is causally driven by the *label* (a model-name heuristic baked into
   the judges' priors) or driven by *correlated quality signals* the judges pick up alongside
   their attribution decision is something a randomized label-swap experiment could
   adjudicate.

3. **Recognition errors don't symmetrize the self-preference effect.** For Gemini, the +0.63
   raw self-preference gap survives despite only 1/10 self-recognition, because the
   *actual-style* coefficient is what's driving it. Subjective recognition is doing little
   work in either direction.

4. **Limitations.** N=120 with 30 own-author cells; Gemini's identifying variation rests on
   15 misattributions, 9 of which are own-→-not-self. Kimi K2.6 ingestion will add another
   40 cells with unknown recognition pattern; we will rerun this analysis at 4-judge level
   in D408. A causal label-swap experiment is on the D408–409 follow-up list.

