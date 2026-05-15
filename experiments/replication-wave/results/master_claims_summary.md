# Master Claims Multiplicity Summary

This document aggregates all formal claims made in the v1.3.0 release that rely on Confidence Intervals, P-values, or explicit statistical testing. 


### Observational

| Claim                                 |   Estimate | Type         | Result      |
|:--------------------------------------|-----------:|:-------------|:------------|
| Pooled 3J Observational Baseline (C1) |      1.46  | Bootstrap CI | Significant |
| Pooled 4J Observational Baseline (C1) |      0.378 | Bootstrap CI | Null        |
| Claude 4J Observational Baseline (C1) |      2.433 | Bootstrap CI | Significant |
| Gemini 4J Observational Baseline (C1) |      0.627 | Bootstrap CI | Null (post-correction) |
| GPT 4J Observational Baseline (C1)    |      1.327 | Bootstrap CI | Significant |
| Kimi 4J Observational Baseline (C1)   |     -2.873 | Bootstrap CI | Significant |

### Mechanism

| Claim                           | Estimate   | Type            | Result      |
|:--------------------------------|:-----------|:----------------|:------------|
| Mediation: Actual Authorship    | -0.349     | Regression β CI | Null        |
| Mediation: Perceived Authorship | +1.532     | Regression β CI | Significant |
| Floor-Raiser Mechanism (Gemini) | ρ = -0.834 | Spearman        | Significant |

### Causal RCT

| Claim                                 |   Estimate | Type         | Result      |
|:--------------------------------------|-----------:|:-------------|:------------|
| Causal Label-Swap: Claude Self-Effect |      0.12  | Bootstrap CI | Null        |
| Causal Label-Swap: Gemini Self-Effect |      0.293 | Bootstrap CI | Significant |
| Causal Label-Swap: GPT Self-Effect    |      0     | Exact        | Null        |
| Causal Label-Swap: Kimi Self-Effect   |      0.007 | Bootstrap CI | Null        |
| Causal Label-Swap: Gemini anti-Kimi   |     -0.245 | Bootstrap CI | Significant |
| Causal Label-Swap: Claude pro-Claude  |      0.12  | Bootstrap CI | Null        |
| Causal Label-Swap: Kimi pro-Claude    |      0.3   | Bootstrap CI | Null        |

Note: The Gemini observational claim does not survive family-wise correction; see `master_claims_multiplicity_rebootstrap.md`.
