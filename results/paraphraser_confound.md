# C2 paraphraser-is-judge confound check

In our round-robin C2 paraphrasing, every C2 response carries the paraphraser's stylistic fingerprint. If a judge happens to score a C2 paraphrase whose paraphraser is itself (but the original author is someone else), does it rate that paraphrase higher than C2 paraphrases done by a third model?

Sample: 270 C2 rows where original author != judge (90 per judge x 3 judges, 30 prompts).

## Descriptive

| | paraphraser != judge | paraphraser == judge |
|---|---:|---:|
| claude-opus-4.7 | 8.097 (N=60) | 8.740 (N=30) |
| gemini-3.1-pro | 8.290 (N=60) | 8.253 (N=30) |
| gpt-5.5 | 7.203 (N=60) | 7.353 (N=30) |
| **pooled** | **7.863** (N=180) | **8.116** (N=90) |

## OLS regression with cluster-robust SEs (cluster = prompt_id)

`composite ~ paraphraser_is_judge + C(judge) + C(author) + C(category)`

| term | β | SE | t |
|---|---:|---:|---:|
| intercept | +9.267 | 0.271 | +34.23*** |
| paraphraser_is_judge | +0.241 | 0.125 | +1.94* |
| j_gemini-3.1-pro | -0.104 | 0.236 | -0.44 |
| j_gpt-5.5 | -1.183 | 0.102 | -11.56*** |
| a_gemini-3.1-pro | -0.212 | 0.209 | -1.01 |
| a_gpt-5.5 | -0.375 | 0.146 | -2.56** |
| a_kimi-k2.6 | -1.990 | 0.300 | -6.64*** |
| cat_creative | -0.738 | 0.301 | -2.45** |
| cat_design | +0.329 | 0.216 | +1.52 |
| cat_ethics | -0.767 | 0.228 | -3.36*** |
| cat_explanation | -0.650 | 0.213 | -3.06*** |
| cat_reasoning | +0.093 | 0.277 | +0.34 |
| cat_translation | +0.522 | 0.251 | +2.08** |

## Interpretation

When a C2 paraphrase happens to have been authored (paraphrased) by the same model that is now judging it (but with a different original author), judges score it +0.24 points higher than when a different model paraphrased the text. The effect is at the boundary of significance with cluster-robust SEs (p ≈ 0.05). This is consistent with paraphrasers leaving their own stylometric fingerprint on C2 responses, which judges can then preferentially recognize. It is a methodological caveat for any round-robin paraphrase design — a truly style-neutral paraphraser would either be deterministic or balanced across all stylistic axes.
