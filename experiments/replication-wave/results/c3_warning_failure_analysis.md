# Analysis of C3 (Bias Warning) Failure

This report analyzes why explicitly warning models about their own self-preference bias (C3) failed to mitigate the effect.

## Self-Preference Gaps (C1 vs C3)

| Judge | C1 Gap | C3 Gap | Change (C3 - C1) |
|-------|--------|--------|------------------|
| `claude-opus-4.7` | 2.433 | 2.433 | 0.000 |
| `gemini-3.1-pro` | 0.627 | 0.913 | 0.287 |
| `gpt-5.5` | 1.327 | 1.327 | 0.000 |
| `kimi-k2.6` | -2.873 | -2.880 | -0.007 |

## Shift in Self-Preference by Dimension (C3 - C1)

| Judge | Correctness | Completeness | Clarity | Creativity | Constraint |
|-------|-------------|--------------|---------|------------|------------|
| `claude-opus-4.7` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `gemini-3.1-pro` | 0.433 | 0.100 | -0.200 | 0.367 | 0.733 |
| `gpt-5.5` | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| `kimi-k2.6` | 0.000 | 0.000 | 0.000 | 0.000 | -0.033 |

## Summary of Findings
- **Claude:** Self-preference gap was unchanged (C1 +2.433; C3 +2.433).
- **Gemini:** Self-preference gap increased by +0.287 (C1 +0.627; C3 +0.913).
- **GPT-5.5:** Self-preference gap was unchanged (C1 +1.327; C3 +1.327).
- **Kimi:** Self-preference gap decreased by -0.007 (C1 -2.873; C3 -2.880).
- Overall, C3 did not reduce the pooled self-preference pattern: two judges were unchanged, Gemini increased, and Kimi's negative gap was essentially unchanged.
- Important caveat: C3 delivery was heterogeneous (Claude/GPT used pre-fix label/order-only rows without a visible warning, while Gemini/Kimi saw the visible warning), so this diagnostic should be read as a delivery-failure/robustness check rather than a clean warning intervention.
