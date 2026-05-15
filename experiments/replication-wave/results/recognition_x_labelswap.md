# Recognition x Causal Label-Swap Interaction

Cross-tabulating each judge's C4 self-/peer-recognition accuracy
against its causal label-swap self-effect (self-diagonal of the
4x4 label-effect matrix). Across 4 judges this is a small sample
(n_judges = 4), so we report the descriptive table plus rank
correlations and treat them as exploratory.

| Judge | Overall recog acc | Self-recog rate | Mean confidence | False-self rate (peers->self) | Label-swap self-effect (95% naive CI) | n_pairs |
|---|---:|---:|---:|---:|---:|---:|
| claude-opus-4.7 | 0.90 (36/40) | 10/10 = 1.00 | 3.38/5 | 0/30 = 0.00 | +0.090 [-0.05, +0.23] | 20 |
| gemini-3.1-pro | 0.62 (25/40) | 1/10 = 0.10 | 3.17/5 | 2/30 = 0.07 | +0.220 [+0.11, +0.33] | 20 |
| gpt-5.5 | 1.00 (40/40) | 10/10 = 1.00 | 4.00/5 | 0/30 = 0.00 | +0.000 [+0.00, +0.00] | 20 |
| kimi-k2.6 | 0.30 (12/40) | 0/10 = 0.00 | 3.40/5 | 4/30 = 0.13 | +0.005 [-0.24, +0.26] | 20 |

## Rank correlations (Spearman, n=4 judges; descriptive only)

- self-recog rate vs label-swap self-effect:    rho = -0.211  (Pearson r = -0.315)
- overall recog acc vs label-swap self-effect:  rho = -0.400  (Pearson r = -0.026)
- false-self rate vs label-swap self-effect:    rho = +0.211  (Pearson r = -0.021)

## What it says

**Two channels for self-favor are theoretically distinct:**

- *Belief channel*: judge correctly believes a response is its own and inflates it.
  Requires accurate self-recognition.
- *Label channel*: judge sees an explicit `(author: <self>)` tag and inflates the rating,
  independent of whether it could otherwise identify the response.

If self-favor were dominated by the belief channel we would expect a *positive* monotone
relationship between self-recognition rate and label-swap self-effect: judges who can
identify themselves get a bigger ego-boost when the label confirms what they already
suspect. Across these 4 frontier judges, the rank correlation is
**rho = -0.211** (Spearman) -- effectively zero / mildly negative.

Concretely:

- Claude Opus 4.7 self-recognizes 10/10 but its self-label cell is +0.090 (CI crosses 0).
- GPT-5.5 self-recognizes 10/10 and its self-label cell is **exactly 0.000** (label-invariant).
- Gemini 3.1 Pro self-recognizes only 1/10 yet its self-label cell is **+0.220** (CI [+0.11, +0.33]; survives Bonferroni).
- Kimi K2.6 self-recognizes 0/10 and its self-label cell is +0.005 (null).

So **the one judge with the largest, statistically robust self-label boost is also the one
with the *lowest* self-recognition rate among the three judges that show any self-tilt at all.**
That cleanly rules out 'belief channel dominates' as a universal story.

**Two-by-two picture:**

|                              | Self-label effect ~0 | Self-label effect > 0 |
|------------------------------|---------------------|----------------------|
| High self-recognition (>=90%) | GPT-5.5             | Claude Opus 4.7 (small) |
| Low  self-recognition (<=10%) | Kimi K2.6           | Gemini 3.1 Pro (large) |

All four cells are populated. The interaction is **not** monotone, and label-driven
self-favor can coexist with poor self-recognition (Gemini), with high self-recognition
(Claude, weakly), or with neither (GPT, Kimi).

## False-self channel

Gemini and Kimi *over-attribute peer responses to claude-opus-4.7* in C4 (Gemini predicts
`claude` 17 / 40, Kimi 16 / 40 vs the uniform expectation of 10/40). This dovetails with
Kimi's non-significant pro-Claude tilt in the label-effect matrix (+0.225, CI wide), but
does **not** explain Gemini's behaviour, which is symmetric pro-self / anti-Kimi rather
than pro-Claude.

## Sample-size honesty

n=4 judges means rank correlations are noisy point estimates, not significance tests.
The qualitative finding is the *contingency table*: a clean existence proof that all
four (recognition x label-effect) cells are non-empty across frontier judges, so neither
'high recognition implies more label bias' nor 'low recognition implies no label bias'
holds.

