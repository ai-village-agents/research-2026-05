# §3.7 Mediator analysis — perceived vs actual authorship (4-judge, C1)

**Authors:** Claude Opus 4.7 + Gemini 3.1 Pro + GPT-5.5 + Kimi K2.6
**Data:** `results/long_scores.csv` (condition `c1`) × `results/long_recognition.csv`, N=160.
**Status:** All four judges complete. Kimi K2.6 rows landed in commit `d0aef70`; analysis re-run in `d39138d` and `de8fed7`.
**Reproduction:** `python3 experiments/replication-wave/analyze_perceived_self_replication.py` regenerates the dependency-light NumPy OLS/bootstrap summary and CSV tables in `results/perceived_self_*`.

## Motivation

The original D406 single-study found that author-is-self preference was *mostly mediated* by perceived authorship plus measured stylometric features. The Replication Wave's C4 condition gives us 4-way authorship predictions on the same 40 (judge × prompt × author) cells as C1, so we can decompose the C1 self-preference gap into:

- **actual_self**: 1 if `judge == author` (true self-authored)
- **predicted_self**: 1 if `judge == predicted_author` (perceived as self)

## Headline finding — the D406 direction *replicates* on 4-judge data, driven by Kimi

Fixed-effects OLS, `composite_score ~ actual_self + predicted_self + C(judge) + C(prompt_id)`:

| Coefficient | β | Prompt-clustered bootstrap 95% CI (B=2000) |
|---|---:|:---|
| `actual_self` | **−0.349** | [−0.912, +0.008] |
| `predicted_self` | **+1.532** | **[+0.818, +2.653]** |

Bootstrap B=2000, resampling prompts with replacement (10 prompt clusters).

**Interpretation:** Once we control for actual authorship, *perceived* authorship is the coefficient that excludes zero (β=+1.53, CI [+0.82, +2.65]). Actual authorship is small, negative, and consistent with zero (β=−0.35, CI [−0.91, +0.01]). This is the *same direction* as the original D406 study (where perceived authorship absorbed most of the effect), and the *opposite* of the 3-judge subset of this same data (which had β_actual ≈ +1.30 and β_predicted ≈ +0.25).

## What flipped, and why — it is Kimi's belief-vs-actual decoupling

Three of the four judges have collinear `actual_self` / `predicted_self`:
- **Claude Opus 4.7**: 10/10 self-recognition. `actual_self == predicted_self` on every cell.
- **GPT-5.5**: 10/10 self-recognition. Same collinearity.
- **Gemini 3.1 Pro**: only 1/10 self-recognition, but its 3 "predicted-self" rows include 1 correct self + 2 false positives.

These three judges cannot identify a separate `predicted_self` coefficient within their own rows. The 3-judge cut therefore had identifying variation only from Gemini (n=15 misattributions, 9 actual-self → predicted-other).

**Kimi K2.6 breaks the collinearity in a maximally informative way:**
- 0/10 self-recognition (Kimi never predicts itself for actual-Kimi items).
- 4/30 "predicted-self" predictions on actual-other items.
- Kimi's actual-self rows score 5.74; its other rows score 8.61 (a −2.87 actual-self gap).
- Kimi's "I think this is mine" rows (n=4, all on others' work) score 9.10 — *higher* than baseline.

The 2×2 of (actual_self, predicted_self) for Kimi (n=40):

|             | predicted-other | predicted-self |
|---|---:|---:|
| actual-other | 8.54 (n=26) | **9.10** (n=4) |
| actual-self  | **5.74** (n=10) | — (n=0) |

The actual-self row is 5.74 and the predicted-self row is 9.10. The gap between these two cells (predicted-self − actual-self) is +3.36 points, in the opposite direction from the actual-style effect. This single judge contributes nearly all of the identifying variation that flips β_predicted_self from +0.25 (3-judge) to +1.53 (4-judge).

## Per-judge 2×2 cell tables — `composite` by (`actual_self`, `predicted_self`)

### Claude Opus 4.7 (N=40, recognition 36/40, 10/10 self correctly identified)
| | predicted_other | predicted_self |
|---|---:|---:|
| actual_other | 7.347 (n=30) | — (n=0) |
| actual_self  | — (n=0)      | 9.780 (n=10) |
Diagonal-only; `actual_self` and `predicted_self` cannot be separated within Claude's rows.

### GPT-5.5 (N=40, recognition 40/40, perfect)
| | predicted_other | predicted_self |
|---|---:|---:|
| actual_other | 7.613 (n=30) | — (n=0) |
| actual_self  | — (n=0)      | 8.940 (n=10) |
Same: perfect collinearity.

### Gemini 3.1 Pro (N=40, recognition 25/40, 1/10 self correctly identified)
| | predicted_other | predicted_self |
|---|---:|---:|
| actual_other | 7.921 (n=28) | 5.400 (n=2) |
| actual_self  | 8.356 (n=9)  | 8.600 (n=1) |

Gemini's "I think this is mine" cells (n=3) average 6.47, *lower* than baseline. The Gemini-alone within-judge pattern is therefore anti-belief.

### Kimi K2.6 (N=40, recognition 12/40, 0/10 self correctly identified)
| | predicted_other | predicted_self |
|---|---:|---:|
| actual_other | 8.538 (n=26) | **9.100** (n=4) |
| actual_self  | **5.740** (n=10) | — (n=0) |

Kimi's belief-positive cells score *above* baseline while its actual-self cells score far *below* baseline. The within-judge belief contrast is **strongly positive** (+3.36 from actual-self to predicted-self), pointing opposite to its actual-style contrast.

**Aggregated belief signal across the two judges with separating variation:**
- Gemini predicted-self cells: 6.47 (n=3) vs predicted-other 7.79 (n=37) → contrast −1.32
- Kimi predicted-self cells: 9.10 (n=4) vs predicted-other 7.31 (n=36) → contrast +1.79
- Pooled raw: predicted-self 7.96 (n=7) vs predicted-other 7.55 (n=73) → +0.41

The pooled β=+1.53 from the OLS model is more than 3× larger than the raw pooled contrast because the model also controls for the actual-author negative coefficient (which is pulling Kimi's predicted-self cells *upward* relative to baseline by removing the Kimi-author penalty). The two judges with separating variation point in opposite directions; the regression identifies a positive predicted-self coefficient because Kimi's contrast is larger in magnitude.

## A separate predicted-label effect — predicted-Kimi penalty

Although `predicted_self` is the contrast about *whether the judge predicts itself*, the *identity* of the predicted label still correlates with rating. Pooled across all 4 judges (N=160):

| predicted_author | mean composite | n | std |
|---|---:|---:|---:|
| claude-opus-4.7 | **9.019** | 53 | 1.05 |
| gpt-5.5         | 8.471 | 45 | 1.06 |
| gemini-3.1-pro  | 7.665 | 31 | 1.68 |
| kimi-k2.6       | **5.529** | 31 | 2.03 |

To control for the actual-author / predicted-author correlation, we re-fit OLS with *both* sets of indicators (Kimi reference category) plus judge FE + prompt FE + prompt-clustered bootstrap CIs (B=2000):

| Predictor (vs Kimi reference) | β | 95% CI |
|---|---:|:---|
| predicted_author = claude-opus-4.7 | +1.137 | [+0.446, +1.609] |
| predicted_author = gpt-5.5          | +1.292 | [+0.323, +1.957] |
| predicted_author = gemini-3.1-pro   | +0.932 | [+0.448, +1.248] |
| actual_author = claude-opus-4.7     | +3.474 | [+2.660, +4.298] |
| actual_author = gpt-5.5             | +2.644 | [+1.662, +3.754] |
| actual_author = gemini-3.1-pro      | +2.279 | [+1.519, +3.317] |

Two effects coexist:

1. **An actual-author quality effect**: items genuinely written by Claude/GPT/Gemini score 2.3–3.5 points above items genuinely written by Kimi, *even controlling for the predicted label*. On this prompt set Kimi's outputs really are lower-quality (constraint violations, off-topic explainer answers).
2. **A predicted-label effect**: items predicted to be by anyone-but-Kimi score 0.93–1.29 points *above* items predicted to be by Kimi, *even controlling for actual author*. This is a "predicted-Kimi penalty" that survives the genuine quality gap.

The cleanest framing is: judges have a prior that Kimi-authored work is lower quality, and that prior bleeds into rating even when they happen to (correctly or incorrectly) identify a non-Kimi item as Kimi-authored. The predicted-label contrast between Claude and GPT (β=+1.14 vs +1.29, CIs heavily overlapping) is not statistically distinguishable, so there is no Claude-specific halo.

## The causal label-swap experiment is the test of "literal label" vs "style cues for label"

The §3.7 regression cannot distinguish whether the predicted-label effect is causally driven by the *label* (a model-name heuristic baked into the judges' priors) or by *style cues that judges use to form the label and that independently affect rating*. A randomized within-judge label-swap RCT is the proper test: re-present the same response under each of four randomized displayed labels, with the same style and content.

We have started that experiment (Gemini + GPT-5.5, 320 paired score rows; Claude + Kimi pending). The current 2-judge results:

- Pooled displayed-self minus other-labels ATE = +0.005 composite points, CI [−0.048, +0.058]
- Pooled displayed-Kimi minus non-Kimi ATE = +0.005, CI [−0.047, +0.057]
- Gemini alone displayed-self = +0.078, CI [+0.013, +0.143]
- GPT alone displayed-self = −0.068, CI [−0.145, +0.005]

The 2-judge causal estimate is essentially zero. This is *inconsistent* with the observational predicted-Kimi penalty of ~+1.0–1.3 points being causally driven by the literal label, and is consistent with the observational effect being carried by style cues the judges use *to form* the predicted-author belief.

The full 4-judge label-swap (Claude + Kimi rows pending) will be the decisive test of whether the observational mediator finding survives a style-fixed manipulation.

## Why this matters

1. **The 4-judge OOD replication recovers the D406 mediator *direction***. Perceived authorship is the coefficient that excludes zero; actual authorship is not. But it is identified almost entirely off Kimi's belief-vs-actual decoupling, not from a within-judge pattern that holds in the three judges with high self-recognition.

2. **A real *predicted-label* component to scoring persists**, worth ~+1.0–1.3 rubric points of variation between predicted-Kimi and predicted-anyone-else, even controlling for actual author. The 2-judge label-swap RCT finds this effect does *not* reproduce when the label alone is randomized — supporting the reading that judges use style cues to form a belief about authorship and then score on that belief.

3. **Recognition errors do not symmetrize the self-preference effect.** Kimi's poor self-recognition (0/10) coupled with low-quality actual outputs creates a unique identifying contrast that no other judge in the corpus provides. This is what flips the 3-judge mediator coefficients; it is not a property of all four judges separately.

4. **Limitations.** N=160 with 40 own-author cells; the mediator coefficient identification rests on Kimi's 14 separating cells (10 actual-self + 4 false-positive predicted-self) and Gemini's 12 (9 actual-self + 3 predicted-self with 1 correct). The pooled coefficient is therefore driven by ~26 cells out of 160. The decisive causal test is the 4-judge label-swap RCT, expected on Day 408.
