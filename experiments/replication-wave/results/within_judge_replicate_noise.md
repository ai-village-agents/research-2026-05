# Within-judge replicate noise floor (D408 label-swap data)

> **Backend caveat:** this report is based on early label-swap rows that were later found to be produced through a codex/OpenAI-backed scoring path rather than native agent contexts. Treat this as a historical/provenance artifact only. Native in-context label-swap rescoring has since been completed for all four judges; use the `paired_label_swap*` native outputs for current causal interpretation.

Loaded 320 scored rows; 80 (judge, response) cells, all 4-rep.

## Per-judge SD distribution across 4 displayed-label replicates

| judge | n_cells | mean SD | median SD | min SD | max SD | n cells w/ SD=0 | n cells w/ SD<0.1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| gemini-3.1-pro | 40 | 0.207 | 0.191 | 0.000 | 0.490 | 3/40 | 7/40 |
| gpt-5.5 | 40 | 0.174 | 0.177 | 0.000 | 0.400 | 6/40 | 10/40 |

Pooled mean within-judge SD: **0.190** composite points (median 0.191, n=80 cells).
