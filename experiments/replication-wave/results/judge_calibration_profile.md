# Judge calibration and disagreement profile (post-v1.3.0 exploratory supplement)
This supplement does **not** change the headline v1.3.0 results. It describes how each judge used the composite 1–10 scale in the completed replication wave, and how far each judge's score sat from the peer consensus for the same `(condition, prompt, author)` response cell.
Definitions:
- `composite` = mean of correctness, completeness, clarity, creativity, and constraint adherence.
- `peer_consensus` = mean composite from the other three judges on the same condition/prompt/author cell.
- `signed_vs_peer_consensus` = judge composite minus peer consensus; positive means more lenient than peers on matched cells.
- `abs_vs_peer_consensus` = absolute distance from peer consensus; lower means closer calibration to peers.

## Overall judge profiles

| Judge | n | Mean composite | SD | Mean signed vs peers | Mean abs vs peers | Median abs vs peers | % within 0.5 | % within 1.0 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| claude-opus-4.7 | 120 | 7.727 | 2.110 | 0.029 | 0.398 | 0.267 | 68.3% | 91.7% |
| gemini-3.1-pro | 120 | 7.710 | 2.027 | 0.007 | 0.350 | 0.267 | 78.3% | 95.0% |
| gpt-5.5 | 120 | 7.727 | 2.059 | 0.029 | 0.313 | 0.267 | 80.0% | 98.3% |
| kimi-k2.6 | 120 | 7.657 | 1.871 | -0.064 | 0.493 | 0.367 | 62.5% | 88.3% |

Scale-use rank, highest to lowest mean composite: claude-opus-4.7 (7.727) > gpt-5.5 (7.727) > gemini-3.1-pro (7.710) > kimi-k2.6 (7.657).

Peer-calibration rank, closest to farthest by mean absolute peer deviation: gpt-5.5 (0.313) > gemini-3.1-pro (0.350) > claude-opus-4.7 (0.398) > kimi-k2.6 (0.493).

## By condition

| Condition | Judge | Mean composite | SD | Mean signed vs peers | Mean abs vs peers |
|---|---|---:|---:|---:|---:|
| C1 | claude-opus-4.7 | 7.955 | 2.056 | 0.038 | 0.472 |
| C1 | gemini-3.1-pro | 7.910 | 1.950 | -0.022 | 0.395 |
| C1 | gpt-5.5 | 7.945 | 1.973 | 0.025 | 0.328 |
| C1 | kimi-k2.6 | 7.895 | 1.651 | -0.042 | 0.635 |
| C2 | claude-opus-4.7 | 7.270 | 2.193 | 0.013 | 0.227 |
| C2 | gemini-3.1-pro | 7.305 | 2.216 | 0.060 | 0.200 |
| C2 | gpt-5.5 | 7.290 | 2.204 | 0.040 | 0.263 |
| C2 | kimi-k2.6 | 7.175 | 2.210 | -0.113 | 0.237 |
| C3 | claude-opus-4.7 | 7.955 | 2.056 | 0.035 | 0.495 |
| C3 | gemini-3.1-pro | 7.915 | 1.890 | -0.018 | 0.455 |
| C3 | gpt-5.5 | 7.945 | 1.973 | 0.022 | 0.348 |
| C3 | kimi-k2.6 | 7.900 | 1.649 | -0.038 | 0.608 |

## Pairwise matched-cell disagreement

| Judge A | Judge B | n cells | Mean A−B | Mean absolute difference | Median absolute difference | Spearman ρ | Pearson r |
|---|---|---:|---:|---:|---:|---:|---:|
| gemini-3.1-pro | gpt-5.5 | 120 | -0.017 | 0.320 | 0.200 | 0.915 | 0.975 |
| claude-opus-4.7 | gpt-5.5 | 120 | 0.000 | 0.430 | 0.400 | 0.896 | 0.961 |
| claude-opus-4.7 | gemini-3.1-pro | 120 | 0.017 | 0.463 | 0.400 | 0.824 | 0.952 |
| gpt-5.5 | kimi-k2.6 | 120 | 0.070 | 0.530 | 0.400 | 0.880 | 0.937 |
| gemini-3.1-pro | kimi-k2.6 | 120 | 0.053 | 0.533 | 0.400 | 0.842 | 0.934 |
| claude-opus-4.7 | kimi-k2.6 | 120 | 0.070 | 0.547 | 0.400 | 0.912 | 0.940 |

## Largest individual deviations from peer consensus

These rows are useful for diagnosing where disagreement concentrates; they are not evidence of error by themselves.

| Condition | Prompt | Author | Judge | Composite | Peer consensus | Signed gap | Abs gap |
|---|---|---|---|---:|---:|---:|---:|
| C3 | repl-history-001 | claude-opus-4.7 | gemini-3.1-pro | 7.200 | 9.333 | -2.133 | 2.133 |
| C1 | repl-code-001 | kimi-k2.6 | kimi-k2.6 | 5.000 | 3.133 | 1.867 | 1.867 |
| C1 | repl-philosophy-001 | gemini-3.1-pro | kimi-k2.6 | 8.800 | 7.067 | 1.733 | 1.733 |
| C3 | repl-code-001 | gemini-3.1-pro | gpt-5.5 | 4.600 | 6.333 | -1.733 | 1.733 |
| C3 | repl-code-001 | kimi-k2.6 | kimi-k2.6 | 5.000 | 3.333 | 1.667 | 1.667 |
| C3 | repl-philosophy-001 | gemini-3.1-pro | claude-opus-4.7 | 6.600 | 8.267 | -1.667 | 1.667 |
| C1 | repl-creative-001 | kimi-k2.6 | kimi-k2.6 | 5.800 | 4.200 | 1.600 | 1.600 |
| C3 | repl-history-001 | claude-opus-4.7 | claude-opus-4.7 | 10.000 | 8.400 | 1.600 | 1.600 |
| C1 | repl-code-001 | gemini-3.1-pro | gpt-5.5 | 4.600 | 6.133 | -1.533 | 1.533 |
| C3 | repl-creative-001 | kimi-k2.6 | kimi-k2.6 | 5.800 | 4.333 | 1.467 | 1.467 |
| C1 | repl-code-001 | kimi-k2.6 | gemini-3.1-pro | 2.600 | 3.933 | -1.333 | 1.333 |
| C3 | repl-design-001 | gpt-5.5 | kimi-k2.6 | 7.400 | 8.667 | -1.267 | 1.267 |
| C1 | repl-design-001 | gpt-5.5 | kimi-k2.6 | 7.400 | 8.667 | -1.267 | 1.267 |
| C3 | repl-philosophy-001 | gemini-3.1-pro | kimi-k2.6 | 8.800 | 7.533 | 1.267 | 1.267 |
| C1 | repl-science-001 | kimi-k2.6 | claude-opus-4.7 | 3.800 | 5.067 | -1.267 | 1.267 |
| C1 | repl-philosophy-001 | claude-opus-4.7 | gemini-3.1-pro | 8.000 | 9.267 | -1.267 | 1.267 |
| C1 | repl-history-001 | claude-opus-4.7 | claude-opus-4.7 | 10.000 | 8.733 | 1.267 | 1.267 |
| C3 | repl-philosophy-001 | claude-opus-4.7 | gemini-3.1-pro | 8.000 | 9.267 | -1.267 | 1.267 |
| C1 | repl-philosophy-001 | gemini-3.1-pro | claude-opus-4.7 | 6.600 | 7.800 | -1.200 | 1.200 |
| C3 | repl-creative-001 | kimi-k2.6 | claude-opus-4.7 | 3.800 | 5.000 | -1.200 | 1.200 |

## Interpretation

- The closest judge to peer consensus is **gpt-5.5** (mean absolute peer deviation 0.313); the farthest is **kimi-k2.6** (0.493).
- The most lenient matched-cell calibration is **gpt-5.5** (signed vs peers 0.029); the harshest is **kimi-k2.6** (-0.064).
- These calibration profiles complement, but do not replace, the self-preference and label-swap estimands. A judge can be globally lenient or harsh while still showing little causal sensitivity to displayed self-labels.
