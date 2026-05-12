# Style-as-mediator analysis

## TL;DR

We constructed a continuous, *text-derived* mediator `style_prob_self`: the
probability that an 11-feature, leave-one-prompt-out multinomial logistic
regression assigns the judge's own author label to the text the judge actually
scored (the original in C1/C3, the paraphrase in C2). We then re-ran the
PR #54 formal mediation analysis with this style mediator alone, and ran a
**two-mediator horse-race** that includes both the original belief mediator
`predicted_self` (the verbalised C4 recognition) *and* `style_prob_self`.

Headline numbers (pooled across 4 judges, 2000-iter cluster bootstrap on
`prompt_id`, seed 20260512):

| Cond | Indirect via `predicted_self` | Indirect via `style_prob_self` |
|---|---:|---:|
| C1 | **+0.172** [+0.059, +0.346] | **−0.113** [−0.245, +0.004] |
| C2 | **+0.162** [+0.050, +0.323] | −0.050 [−0.151, +0.043] |
| C3 | **+0.145** [+0.031, +0.320] | **−0.159** [−0.306, −0.017] |

Two key findings:

1. **The recognition channel does not reduce to style detection.** After
   partialling out `style_prob_self`, the indirect effect via the *verbalised*
   mediator `predicted_self` is essentially unchanged from PR #54
   (+0.17/+0.16/+0.15 vs. the PR #54 estimates of +0.17/+0.16/+0.15). Believing
   "this is me" adds score variance beyond raw stylometric similarity to one's
   own writing.

2. **Style similarity and verbalised belief pull in opposite directions
   pooled.** The pooled `b` coefficient on `style_prob_self` is *negative*
   (b ≈ −0.33 in C1, −0.47 in C3, after controlling for `author_is_self`).
   In other words, once we condition on actual authorship, responses that look
   *more like the judge's style* tend to get slightly *lower* scores. The
   pooled "self-preference" we have been chasing is entirely concentrated in
   the verbalised belief mediator, not in style.

Per-judge it is heterogeneous (the per-judge tables below confirm and extend
the per-judge story from PR #54):

- **Claude Opus 4.7**: both mediators positive in C1 horse-race
  (pred indirect +0.10, style indirect +0.40). Style is the *larger* channel
  for Claude — Claude likes Claude-like prose.
- **GPT-5.5**: pred indirect positive (+0.33), style indirect strongly
  negative (−0.51). After controlling for actual author, GPT-5.5 *down*-scores
  GPT-5.5-style writing.
- **Gemini 3.1 Pro**: both indirects ≈ 0 (consistent with its uniform-prior
  recognition heuristic — see @Gemini 3.1 Pro's 88% own-name finding).
- **Kimi K2.6**: confounded by the off-topic Spanish responses; pred indirect
  ≈ 0, style indirect −0.27 but CI crosses zero.

LOO classifier accuracy: 65.0% on originals, 50.8% on paraphrases. The
mediator is therefore far from perfect, and the horse-race result is a
*lower-bound* statement on how much the recognition channel can shrink under
a stylometric control. A stronger style model could in principle absorb more
of `predicted_self`; with the features we have, it absorbs essentially none.

## Full tables

Continuous mediator `style_prob_self` = stylometric LR probability that the response text would be classified as authored by the judge (LOO multinomial LR, 11 features, separate models for originals and paraphrases).

- LOO accuracy: originals = 0.650; paraphrases = 0.508

- 2000-iter cluster bootstrap on prompt_id, seed 20260512. B=2000.


## A. Mediation through style_prob_self alone

| Subset | Cond | N | c (total) | c' (direct) | a | b | indirect a·b |
|---|---|---:|---:|---:|---:|---:|---:|
| pooled | c1 | 480 | +0.004 [-0.144, +0.146] | +0.117 [-0.084, +0.310] | +0.340 [+0.283, +0.399] | -0.333 [-0.697, +0.011] | **-0.113** [-0.245, +0.004] |
| pooled | c2 | 480 | -0.155 [-0.317, +0.003] | -0.105 [-0.289, +0.083] | +0.220 [+0.175, +0.268] | -0.225 [-0.706, +0.191] | **-0.050** [-0.151, +0.043] |
| pooled | c3 | 480 | -0.064 [-0.194, +0.064] | +0.095 [-0.124, +0.301] | +0.340 [+0.283, +0.399] | -0.467 [-0.893, -0.052] | **-0.159** [-0.306, -0.017] |
| judge=claude-opus-4.7 | c1 | 120 | +1.738 [+1.473, +2.040] | +1.333 [+0.835, +1.948] | +0.503 [+0.408, +0.603] | +0.804 [-0.273, +1.657] | **+0.404** [-0.137, +0.900] |
| judge=claude-opus-4.7 | c2 | 120 | +1.202 [+0.733, +1.698] | +0.529 [-0.340, +1.261] | +0.431 [+0.337, +0.536] | +1.560 [+0.399, +2.913] | **+0.673** [+0.167, +1.270] |
| judge=claude-opus-4.7 | c3 | 120 | +1.467 [+1.147, +1.816] | +1.208 [+0.714, +1.799] | +0.503 [+0.408, +0.603] | +0.515 [-0.642, +1.359] | **+0.259** [-0.314, +0.741] |
| judge=gemini-3.1-pro | c1 | 120 | +0.009 [-0.031, +0.053] | +0.012 [-0.040, +0.070] | +0.230 [+0.152, +0.305] | -0.014 [-0.161, +0.109] | **-0.003** [-0.035, +0.028] |
| judge=gemini-3.1-pro | c2 | 120 | -0.011 [-0.056, +0.033] | -0.021 [-0.073, +0.026] | +0.156 [+0.083, +0.230] | +0.063 [-0.108, +0.236] | **+0.010** [-0.015, +0.043] |
| judge=gemini-3.1-pro | c3 | 120 | +0.009 [-0.031, +0.053] | +0.012 [-0.040, +0.070] | +0.230 [+0.152, +0.305] | -0.014 [-0.161, +0.109] | **-0.003** [-0.035, +0.028] |
| judge=gpt-5.5 | c1 | 120 | +1.124 [+0.747, +1.491] | +1.635 [+1.241, +2.143] | +0.234 [+0.178, +0.293] | -2.187 [-3.670, -1.061] | **-0.511** [-0.910, -0.230] |
| judge=gpt-5.5 | c2 | 120 | +1.153 [+0.798, +1.511] | +1.554 [+1.157, +1.976] | +0.075 [+0.048, +0.102] | -5.361 [-7.520, -3.576] | **-0.401** [-0.642, -0.228] |
| judge=gpt-5.5 | c3 | 120 | +1.124 [+0.747, +1.491] | +1.635 [+1.241, +2.143] | +0.234 [+0.178, +0.293] | -2.187 [-3.670, -1.061] | **-0.511** [-0.910, -0.230] |
| judge=kimi-k2.6 | c1 | 120 | -2.856 [-4.002, -1.813] | -2.590 [-3.899, -1.344] | +0.395 [+0.291, +0.500] | -0.673 [-2.610, +1.077] | **-0.266** [-1.081, +0.427] |
| judge=kimi-k2.6 | c2 | 120 | -2.964 [-4.103, -1.922] | -2.748 [-3.881, -1.735] | +0.220 [+0.158, +0.284] | -0.986 [-2.416, +0.190] | **-0.217** [-0.513, +0.050] |
| judge=kimi-k2.6 | c3 | 120 | -2.856 [-4.002, -1.813] | -2.590 [-3.899, -1.344] | +0.395 [+0.291, +0.500] | -0.673 [-2.610, +1.077] | **-0.266** [-1.081, +0.427] |

## B. Two-mediator horse-race (predicted_self + style_prob_self)

| Subset | Cond | N | c | c' | a1·b1 (pred) | a2·b2 (style) | b1 | b2 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| pooled | c1 | 480 | +0.004 | -0.053 [-0.403, +0.230] | **+0.172** [+0.039, +0.353] | **-0.115** [-0.264, +0.013] | +0.442 [+0.103, +0.848] | -0.338 [-0.765, +0.038] |
| pooled | c2 | 480 | -0.155 | -0.262 [-0.586, +0.011] | **+0.162** [+0.027, +0.339] | **-0.055** [-0.163, +0.046] | +0.416 [+0.080, +0.816] | -0.248 [-0.740, +0.203] |
| pooled | c3 | 480 | -0.064 | -0.049 [-0.403, +0.245] | **+0.145** [+0.010, +0.326] | **-0.160** [-0.326, -0.006] | +0.374 [+0.027, +0.790] | -0.471 [-0.954, -0.017] |
| judge=claude-opus-4.7 | c1 | 120 | +1.738 | +1.234 [+0.675, +1.907] | **+0.100** [-0.283, +0.420] | **+0.404** [-0.137, +0.906] | +0.136 [-0.361, +0.510] | +0.803 [-0.275, +1.663] |
| judge=claude-opus-4.7 | c2 | 120 | +1.202 | +0.809 [-0.238, +2.152] | **-0.300** [-1.505, +0.553] | **+0.694** [+0.168, +1.329] | -0.410 [-1.920, +0.673] | +1.610 [+0.404, +2.997] |
| judge=claude-opus-4.7 | c3 | 120 | +1.467 | +0.969 [+0.472, +1.653] | **+0.239** [-0.137, +0.570] | **+0.259** [-0.318, +0.735] | +0.326 [-0.177, +0.692] | +0.514 [-0.631, +1.350] |
| judge=gemini-3.1-pro | c1 | 120 | +0.009 | +0.009 [-0.042, +0.060] | **+0.002** [-0.007, +0.019] | **-0.001** [-0.034, +0.029] | -0.078 [-0.145, -0.005] | -0.006 [-0.155, +0.113] |
| judge=gemini-3.1-pro | c2 | 120 | -0.011 | -0.023 [-0.076, +0.023] | **+0.001** [-0.005, +0.014] | **+0.011** [-0.014, +0.043] | -0.049 [-0.124, +0.069] | +0.072 [-0.094, +0.240] |
| judge=gemini-3.1-pro | c3 | 120 | +0.009 | +0.009 [-0.042, +0.060] | **+0.002** [-0.007, +0.019] | **-0.001** [-0.034, +0.029] | -0.078 [-0.145, -0.005] | -0.006 [-0.155, +0.113] |
| judge=gpt-5.5 | c1 | 120 | +1.124 | +1.303 [+0.958, +1.816] | **+0.327** [+0.086, +0.607] | **-0.505** [-0.915, -0.225] | +0.446 [+0.120, +0.763] | -2.162 [-3.689, -1.060] |
| judge=gpt-5.5 | c2 | 120 | +1.153 | +1.152 [+0.705, +1.658] | **+0.406** [+0.090, +0.807] | **-0.404** [-0.646, -0.233] | +0.554 [+0.122, +1.001] | -5.409 [-7.563, -3.684] |
| judge=gpt-5.5 | c3 | 120 | +1.124 | +1.303 [+0.958, +1.816] | **+0.327** [+0.086, +0.607] | **-0.505** [-0.915, -0.225] | +0.446 [+0.120, +0.763] | -2.162 [-3.689, -1.060] |
| judge=kimi-k2.6 | c1 | 120 | -2.856 | -2.580 [-3.884, -1.343] | **-0.007** [-0.150, +0.120] | **-0.269** [-1.077, +0.424] | -0.066 [-0.777, +0.669] | -0.681 [-2.630, +1.061] |
| judge=kimi-k2.6 | c2 | 120 | -2.964 | -2.751 [-3.914, -1.739] | **+0.003** [-0.138, +0.131] | **-0.216** [-0.514, +0.057] | +0.024 [-0.718, +0.707] | -0.981 [-2.434, +0.217] |
| judge=kimi-k2.6 | c3 | 120 | -2.856 | -2.580 [-3.884, -1.343] | **-0.007** [-0.150, +0.120] | **-0.269** [-1.077, +0.424] | -0.066 [-0.777, +0.669] | -0.681 [-2.630, +1.061] |

## C. Interpretation

- In single-mediator form, `style_prob_self` carries an indirect effect if (a) the response text is more 'judge-like' when the author IS the judge, and (b) responses with higher style-similarity to the judge get higher scores. Both `a` and `b` can be inspected per-condition.

- In the horse-race, if the indirect via `predicted_self` shrinks to ~0 and the indirect via `style_prob_self` is significant, the **recognition mediator was essentially a style-detection proxy**. If both remain significant, perceived authorship adds incremental score variance beyond style features.

- C2 uses paraphrased text; therefore `style_prob_self` for C2 reflects whether stylistic fingerprints survive paraphrase.


## Caveats

- LR uses only 11 hand-crafted features. Higher-capacity stylometric models may detect more.

- Style probability is not a manipulated treatment; the same causal caveats from PR #54 apply.

- LOO is at the prompt level, so the LR is leak-protected across prompts but not across authors.
