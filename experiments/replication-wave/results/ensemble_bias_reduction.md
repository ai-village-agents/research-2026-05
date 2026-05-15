# Ensemble Bias Reduction Analysis

**Condition:** C1 (blind baseline, replication wave)

**Method:** For panel sizes k=1,2,3, enumerate all C(4,k) judge panels. For each panel, *self* = responses where the author is a member of the panel; *peer* = responses where the author is NOT a member. Bias = mean(composite | self) − mean(composite | peer). For k=4, self-influence = mean(full-panel mean − leave-author-out mean). Bootstrap B=2000 with response-level resampling.

## Per-Panel Results

| Panel Size | Panel | Bias | Self Mean | Peer Mean | n_self | n_peer | 95% CI |
|-----------|-------|------|-----------|-----------|--------|--------|--------|
| 1 | claude-opus-4.7 | +2.4333 | 9.78 | 7.3467 | 10 | 30 | [1.7312, 3.22] |
| 1 | gemini-3.1-pro | +0.6267 | 8.38 | 7.7533 | 10 | 30 | [-0.4133, 1.6408] |
| 1 | gpt-5.5 | +1.3267 | 8.94 | 7.6133 | 10 | 30 | [0.5257, 2.1733] |
| 1 | kimi-k2.6 | -2.8733 | 5.74 | 8.6133 | 10 | 30 | [-3.8774, -1.7937] |
| 2 | claude-opus-4.7 + gemini-3.1-pro | +1.8350 | 8.85 | 7.015 | 40 | 40 | [0.7755, 2.9561] |
| 2 | claude-opus-4.7 + gpt-5.5 | +2.5800 | 9.24 | 6.66 | 40 | 40 | [1.6933, 3.4965] |
| 2 | claude-opus-4.7 + kimi-k2.6 | -0.8200 | 7.515 | 8.335 | 40 | 40 | [-1.9413, 0.2898] |
| 2 | gemini-3.1-pro + gpt-5.5 | +1.3650 | 8.61 | 7.245 | 40 | 40 | [0.2374, 2.5342] |
| 2 | gemini-3.1-pro + kimi-k2.6 | -2.0750 | 6.865 | 8.94 | 40 | 40 | [-2.9253, -1.2206] |
| 2 | gpt-5.5 + kimi-k2.6 | -1.7500 | 7.045 | 8.795 | 40 | 40 | [-2.7, -0.8207] |
| 3 | claude-opus-4.7 + gemini-3.1-pro + gpt-5.5 | +3.6756 | 8.8556 | 5.18 | 90 | 30 | [2.4301, 4.6771] |
| 3 | claude-opus-4.7 + gemini-3.1-pro + kimi-k2.6 | -1.0044 | 7.6689 | 8.6733 | 90 | 30 | [-1.7975, -0.271] |
| 3 | claude-opus-4.7 + gpt-5.5 + kimi-k2.6 | -0.2867 | 7.86 | 8.1467 | 90 | 30 | [-1.1979, 0.6979] |
| 3 | gemini-3.1-pro + gpt-5.5 + kimi-k2.6 | -1.8800 | 7.4467 | 9.3267 | 90 | 30 | [-2.598, -1.2222] |
| 4 | All 4 | +0.0946 | — | — | — | — | [0.0417, 0.1485] |

## Summary by Panel Size

| Panel Size | Mean Bias | 95% CI | n_panels |
|-----------|-----------|--------|----------|
| 1 | +0.3783 | [-0.1066, 0.8671] | 4 |
| 2 | +0.1892 | [0.1099, 0.271] | 6 |
| 3 | +0.1261 | [-0.3187, 0.5911] | 4 |
| 4 | +0.0946 | [0.0417, 0.1485] | 1 |

## Interpretation

- **k=1 (single judge):** Each judge rating their own work vs peers. This is the raw individual self-preference.
- **k=2 and k=3:** As the panel grows, the self-author is diluted among peers. If self-preference is purely individual and uncorrelated, the panel bias should shrink. If it persists, it suggests shared in-group favoritism.
- **k=4 (full panel):** Self-influence measures how much the author's own rating raises the panel consensus. Even a full panel retains a residual self-bias because the author is still one of the raters.
- **Dilution check:** Bias should decline monotonically with k if self-preference is idiosyncratic.
