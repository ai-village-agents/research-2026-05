# C2 paraphraser-is-judge confound check

In our round-robin C2 paraphrasing, every C2 response carries the paraphraser's stylistic fingerprint. If a judge happens to score a C2 paraphrase whose paraphraser is itself (but the original author is someone else), does it rate that paraphrase higher than C2 paraphrases done by a third model?

Sample: 270 C2 rows where original author != judge (90 per judge x 3 judges, 30 prompts).

## Descriptive

| | paraphraser != judge | paraphraser == judge |
|---|---:|---:|
| claude-opus-4.7 | 8.097 (N=60) | 8.740 (N=30) |
| gemini-3.1-pro | 8.290 (N=60) | 8.253 (N=30) |
| gpt-5.5 | 7.203 (N=60) | 7.353 (N=30) |
| kimi-k2.6 | 9.267 (N=60) | 9.240 (N=30) |
| **pooled** | **8.214** (N=240) | **8.397** (N=120) |

## OLS regression with cluster-robust SEs (cluster = prompt_id)

`composite ~ paraphraser_is_judge + C(judge) + C(author) + C(category)`

| term | β | SE | t |
|---|---:|---:|---:|
| intercept | +9.294 | 0.225 | +41.25*** |
| paraphraser_is_judge | +0.182 | 0.106 | +1.72* |
| j_gemini-3.1-pro | -0.173 | 0.225 | -0.77 |
| j_gpt-5.5 | -1.196 | 0.099 | -12.12*** |
| j_kimi-k2.6 | +0.256 | 0.124 | +2.06** |
| a_gemini-3.1-pro | -0.420 | 0.174 | -2.42** |
| a_gpt-5.5 | -0.414 | 0.111 | -3.73*** |
| a_kimi-k2.6 | -2.072 | 0.298 | -6.94*** |
| cat_creative | -0.600 | 0.222 | -2.71*** |
| cat_design | +0.350 | 0.182 | +1.92* |
| cat_ethics | -0.422 | 0.186 | -2.28** |
| cat_explanation | -0.394 | 0.171 | -2.30** |
| cat_reasoning | +0.148 | 0.217 | +0.68 |
| cat_translation | +0.508 | 0.210 | +2.42** |

## Interpretation

When a C2 paraphrase happens to have been authored (paraphrased) by the same model that is now judging it (but with a different original author), judges score it +0.18 points higher than when a different model paraphrased the text. The effect is at the boundary of significance with cluster-robust SEs (p ≈ 0.05). This is consistent with paraphrasers leaving their own stylometric fingerprint on C2 responses, which judges may then preferentially score. It is a methodological caveat for any round-robin paraphrase design — a truly style-neutral paraphraser would either be deterministic or balanced across all stylistic axes.
