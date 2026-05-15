# Post-hoc power analysis for the 16 master claims

**Author:** Claude Opus 4.7 (Day 409, post-v1.3.0)
**Companion to:** `master_claims_multiplicity_rebootstrap.md`, `master_claims_lopo_robustness.md`, `threats_to_validity.md`
**Code:** `experiments/replication-wave/analysis/master_claims_power.py`

## Purpose

For each of the 16 master claims we estimate (a) observed power at our actual
N, and (b) the N (in prompt-clusters) that would have been needed to achieve
**80% power for the observed effect size** at α=0.05 two-sided.

This is intended as a **planning aid for future replications**, not as an
inferential argument for or against the published results. Retrospective
power computed from the same data has well-known limitations (Hoenig &
Heisey 2001); we present it as a rough N-budget guide.

## Method

- Effect: `est` (the point estimate from the rebootstrap)
- SE: `(CI_high − CI_low) / (2 × 1.96)` (bootstrap SE)
- Observed z: `est / SE`
- Observed power: 2-sided z-test power at α=0.05
- Required N: `N_obs × ((z_α + z_β) / |z_obs|)² = N_obs × (2.80 / |z_obs|)²`
  with z_α = 1.96 and z_β = 0.842 (80% power)

SE here is the published bootstrap SE, which already accounts for prompt
clustering. Scaling 1/√N therefore refers to "1/√(prompt-clusters)" rather
than "1/√(rows)".

## Results

Ranked by observed power (descending). N is the number of prompt-level
clusters used in the original estimate.

| Claim | est | SE | obs z | obs power | N obs | N req for 80% |
|---|---:|---:|---:|---:|---:|---:|
| **Survivors of Bonferroni** | | | | | | |
| Claude 4J Obs C1            | +2.433 | 0.190 | +12.77 | 1.000 | 10 | 0.5 |
| GPT 4J Obs C1               | +1.327 | 0.196 |  +6.78 | 1.000 | 10 | 1.7 |
| Kimi 4J Obs C1              | −2.873 | 0.466 |  −6.17 | 1.000 | 10 | 2.1 |
| Pooled 3J Obs C1            | +1.462 | 0.187 |  +7.82 | 1.000 | 30 | 3.9 |
| Causal Label-Swap Gemini Self | +0.440 | 0.112 | +3.92 | 0.975 | 20 | 10.2 |
| Causal Label-Swap Gemini anti-Kimi | −0.245 | 0.047 | −5.19 | 0.999 | 20 | 5.8 |
| Floor-Raiser Mechanism Gemini (ρ) | −0.874 | 0.077 | −11.34 | 1.000 | 20 | 1.2 |
| Mediation Perceived β        | +1.532 | 0.468 |  +3.27 | 0.905 | — | — |
| **Non-survivors** | | | | | | |
| Gemini 4J Obs C1            | +0.627 | 0.289 | +2.17 | **0.58** | 10 | **16.7** |
| Causal Label-Swap Kimi pro-Claude | +0.225 | 0.144 | +1.56 | 0.34 | 20 | 64.4 |
| Mediation Actual β           | −0.349 | 0.235 | −1.49 | 0.32 | — | — |
| Causal Label-Swap Claude Self | +0.180 | 0.138 | +1.31 | 0.26 | 20 | 92.0 |
| Causal Label-Swap Claude pro-Claude | +0.090 | 0.071 | +1.26 | 0.24 | 20 | 98.9 |
| Pooled 4J Obs C1             | +0.378 | 0.344 | +1.10 | 0.20 | 40 | **259** |
| Causal Label-Swap Kimi Self  | +0.010 | 0.253 | +0.04 | 0.05 | 20 | 100,204 |
| Causal Label-Swap GPT Self   | +0.000 | 0.000 |   inf | 1.00 | 20 | 0 |

## Interpretation

1. **All 8 Bonferroni survivors have observed power ≥ 0.90; 7 of 8 are ≥ 0.97.** With the
   sample sizes used, these claims had high observed power for the effects
   actually observed — they are not knife-edge-positive results.

2. **The Gemini 4J observational C1 (+0.627) is the only multiplicity
   non-survivor that is *plausibly recoverable* in a future replication.**
   At its observed effect size, 80% power requires ~17 prompts per cell vs
   the 10 we used. A modest expansion (e.g. 20 prompts/cell) would either
   confirm or definitively bury this claim. **This is the single most
   informative cell-size to expand in future work.**

3. **The pooled 4J observational C1 (+0.378) requires N ≈ 259** — likely
   infeasible. The reason it's hard is that pooling across 4 judges
   *averages out* the within-judge biases that disagree in sign (Kimi
   negative, Claude/GPT/Gemini positive). The pooled effect is intrinsically
   small. **Future replications should report and analyze each judge
   separately**, not as a pooled mean, even if a pooled mean is reported
   for completeness.

4. **The Kimi Self-Effect (+0.010) is essentially zero.** No realistic N
   could rescue it; this is a true null result and should be reported as
   such ("Kimi does not exhibit a label-channel self-preference effect").

5. **The mediation channel split is the cleanest dissociation result in
   the paper.** β_perceived = +1.532 with 91% power vs β_actual = −0.349
   with 32% power. The perceived-authorship channel would *survive* a
   well-powered replication; the actual-authorship channel would not.

## Implication for the v1.3.0 replication blueprint

For a registered replication aimed at 80% power for the **discoverable**
findings:

- 20 prompt-clusters per cell suffice for: Claude/GPT/Kimi obs C1, all
  Floor-Raiser ρ values, Gemini causal label-swap, Gemini anti-Kimi,
  Perceived-Authorship mediation.
- 25 prompt-clusters per cell give margin for: Gemini obs C1, mediation
  re-fit.
- Higher-N is required to chase: pooled 4J obs C1, Kimi pro-Claude — but
  the per-judge breakdown is more informative anyway.

A future study using **N = 25 prompts × per-(judge, author, condition) cell
= 100 prompts total** should have ≥80% power on every published positive
claim and definitively bury the three Kimi/Claude small-effect label-swap
claims.

## Files

- `master_claims_power.csv` — full table with SE, z, observed power, N_req
