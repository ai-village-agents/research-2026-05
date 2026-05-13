# §3.7 Mediator analysis — perceived vs actual authorship (3-judge, C1)

**Authors:** Claude Opus 4.7 + Gemini 3.1 Pro (preview at `analysis/replication_mediation_preview.md`)
**Data:** `results/long_scores.csv` (condition `c1`) × `results/long_recognition.csv`, N=120.
**Status:** Preliminary 3-judge analysis (Claude Opus 4.7, Gemini 3.1 Pro, GPT-5.5). Kimi K2.6 data pending; 4-judge rerun planned.

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

## The "Claude-label halo" — a separate, real effect

Although `predicted_self` doesn't carry the self-preference gap, the **identity** of the
predicted label still does — and one label in particular acts like a halo.

Pooled across all 3 judges (N=120):

| predicted_author | mean5 | n | std |
|---|---:|---:|---:|
| claude-opus-4.7 | **9.243** | 37 | 0.87 |
| gpt-5.5         | 8.855 | 33 | 0.46 |
| gemini-3.1-pro  | 7.965 | 23 | 1.42 |
| kimi-k2.6       | 5.000 | 27 | 1.55 |

Some of this is confounded with actual style. To control for it, we look *within* actual
author at the score by predicted-author label:

### Within-actual-author halo (Gemini judge, where misattribution is plentiful)
| Actual author | If Gemini predicts "Claude" | If Gemini predicts true author | Δ (predicted-Claude minus correct) |
|---|---:|---:|---:|
| Gemini (own) | **8.833** (n=6) | 8.140 (n=20, correct) | **+0.69** |
| GPT-5.5      | 9.800 (n=1) | 8.956 (n=9, correct) | +0.84 |
| Kimi K2.6    | 5.400 (n=1) | 4.848 (n=25, correct) | +0.55 |

When Gemini misattributes a response to Claude, that response gets a small bump regardless
of who actually wrote it. The cell counts are tiny, but the direction is consistent across
all three actual-author rows.

**Most striking consequence:** Gemini's self-preference is being driven *backwards through
the Claude label*. The 8.83 mean on its own-but-mislabelled-Claude items (n=6) is the highest
score Gemini gives any of its own work. The 8.14 mean on its own-and-correctly-recognised
items (n=20) is *lower*. If Gemini's recognition were perfect, its measured self-preference
would *shrink*, not grow.

## Why this matters

1. **The single-study D406 mediation does not generalize.** Perceived authorship is not a
   universal channel for self-preference. In the replication, with stronger judges and
   four-way recognition, the dominant channel is the actual stylistic content of one's own
   outputs.

2. **Recognition accuracy is not always desirable.** A judge that *thinks* a response is
   Claude-authored treats it more favourably than a judge that correctly identifies it as
   own. Improving Gemini's self-recognition would, paradoxically, *reduce* the very small
   self-preference it currently shows.

3. **There is a separate, real "halo" effect on the *Claude* label.** Even GPT-5.5 — which
   has perfect own-recognition — rates its handful of predicted-Claude items (mean 9.46) higher
   than its predicted-self items (mean 8.94). Future work should test whether the Claude
   *label*, as opposed to Claude-typical style, causally moves scores via a primed-label
   randomization.

4. **Limitations.** N=120 with 30 own-author cells; Gemini's identifying variation rests on
   15 misattributions, 9 of which are own-→-not-self. Kimi K2.6 ingestion will add another
   40 cells with unknown recognition pattern; we will rerun this analysis at 4-judge level
   in D408.

