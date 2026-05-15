# Master Multiplicity Sweep

This document presents a family-wise multiple comparisons correction across the 16 core inferential claims reported in `master_claims_summary.md`. We apply both Benjamini-Hochberg False Discovery Rate (FDR) and the more conservative Bonferroni correction (α = 0.05 / 16 = 0.003125).

This directly addresses Threat 4.2 in the `threats_to_validity.md` supplement.

| Claim                                 |   p-value |   BH-q | Bonf Sig (α=0.05/16)   | BH-FDR Sig (q<0.05)   |
|:--------------------------------------|----------:|-------:|:-----------------------|:----------------------|
| Causal Label-Swap: Gemini Self-Effect |    0.0003 | 0.0018 | Yes                    | Yes                   |
| Causal Label-Swap: Gemini anti-Kimi   |    0.0003 | 0.0018 | Yes                    | Yes                   |
| Pooled 3J Observational Baseline (C1) |    0.001  | 0.0018 | Yes                    | Yes                   |
| Claude 4J Observational Baseline (C1) |    0.001  | 0.0018 | Yes                    | Yes                   |
| Gemini 4J Observational Baseline (C1) |    0.001  | 0.0018 | Yes                    | Yes                   |
| GPT 4J Observational Baseline (C1)    |    0.001  | 0.0018 | Yes                    | Yes                   |
| Kimi 4J Observational Baseline (C1)   |    0.001  | 0.0018 | Yes                    | Yes                   |
| Mediation: Perceived Authorship       |    0.001  | 0.0018 | Yes                    | Yes                   |
| Floor-Raiser Mechanism (Gemini)       |    0.001  | 0.0018 | Yes                    | Yes                   |
| Causal Label-Swap: Kimi pro-Claude    |    0.1165 | 0.1864 | No                     | No                    |
| Mediation: Actual Authorship          |    0.15   | 0.2182 | No                     | No                    |
| Causal Label-Swap: Claude Self-Effect |    0.2125 | 0.2615 | No                     | No                    |
| Causal Label-Swap: Claude pro-Claude  |    0.2125 | 0.2615 | No                     | No                    |
| Pooled 4J Observational Baseline (C1) |    0.28   | 0.32   | No                     | No                    |
| Causal Label-Swap: Kimi Self-Effect   |    0.975  | 1      | No                     | No                    |
| Causal Label-Swap: GPT Self-Effect    |    1      | 1      | No                     | No                    |

**Conclusion:** The structural findings (observational biases, mediation pathways, floor-raiser mechanism) and Gemini's causal label effects easily survive both FDR and Bonferroni corrections at the family-wise level. The null causal effects for Claude and Kimi remain null.