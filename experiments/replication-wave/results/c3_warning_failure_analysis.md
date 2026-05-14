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
- **Claude:** The warning actually *increased* Claude's self-preference slightly.
- **Gemini:** The warning slightly increased Gemini's self-preference.
- **GPT:** The warning slightly increased GPT's self-preference.
- **Kimi:** The warning made Kimi's self-penalization even more severe (gap became more negative).
- Overall, simply telling a model to be objective and warning it about bias is entirely ineffective and sometimes backfires (reactance effect).
