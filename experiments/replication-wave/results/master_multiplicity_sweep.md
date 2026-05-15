# Master Multiplicity Sweep

This document presents a family-wise multiple comparisons correction across the 16 core inferential claims reported in `master_claims_summary.md`. We apply both Benjamini-Hochberg False Discovery Rate (FDR) and the more conservative Bonferroni correction (α = 0.05 / 16 = 0.003125).

This directly addresses Threat 4.2 in the `threats_to_validity.md` supplement.

| Claim                                 |   p-value |   BH-q | Bonf Sig (α=0.05/16)   | BH-FDR Sig (q<0.05)   |
|:--------------------------------------|----------:|-------:|:-----------------------|:----------------------|
| Causal Label-Swap: Gemini Self-Effect |    0.0003 | 0.0018 | Yes                    | Yes                   |
| Causal Label-Swap: Gemini anti-Kimi   |    0.0003 | 0.0018 | Yes                    | Yes                   |
| Pooled 3J Observational Baseline (C1) |    0.001  | 0.0018 | Yes                    | Yes                   |
| Claude 4J Observational Baseline (C1) |    0.001  | 0.0018 | Yes                    | Yes                   |
| Gemini 4J Observational Baseline (C1) |    0.0335 | 0.0596 | No                     | No                    |
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

**Conclusion:** Under multiplicity control, 8 of 16 core claims survive (not 9 of 16). The Gemini C1 observational gap does not survive correction (p=0.0335, BH-q=0.0596), indicating Gemini's bias is primarily a causal label effect rather than a robust observational baseline gap.
