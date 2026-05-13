# Inter-rater agreement — replication wave (4 judges: claude-opus-4.7, gemini-3.1-pro, gpt-5.5, kimi-k2.6)

We pivot scores into (condition, author, prompt) cells. Each cell has all detected judges' composite scores (mean of 5 rubric dims). Metrics quantify agreement on absolute level (ICC, mean within-cell SD), on relative ordering (Spearman), and on linear relationship (Pearson).

- **n_cells per condition**: 40 (10 prompts × 4 authors)
- **Total cells**: 120
- **Judges**: claude-opus-4.7, gemini-3.1-pro, gpt-5.5, kimi-k2.6

### pooled_all (n_cells = 120)

| pair | Pearson r | Spearman ρ |
|---|---:|---:|
| claude × gemini | +0.927 | +0.757 |
| claude × gpt | +0.930 | +0.842 |
| claude × kimi | +0.899 | +0.880 |
| gemini × gpt | +0.967 | +0.912 |
| gemini × kimi | +0.888 | +0.760 |
| gpt × kimi | +0.895 | +0.811 |

**ICC(2,1)** (single-rater absolute agreement): **+0.914**
**ICC(2,k)** (average-rater absolute agreement, k=4): **+0.977**
**Krippendorff's α** (interval): **+0.913**
**Mean within-cell SD** across judges: **0.503**

### c1 (n_cells = 40)

| pair | Pearson r | Spearman ρ |
|---|---:|---:|
| claude × gemini | +0.943 | +0.746 |
| claude × gpt | +0.948 | +0.843 |
| claude × kimi | +0.910 | +0.873 |
| gemini × gpt | +0.975 | +0.912 |
| gemini × kimi | +0.891 | +0.725 |
| gpt × kimi | +0.908 | +0.820 |

**ICC(2,1)** (single-rater absolute agreement): **+0.925**
**ICC(2,k)** (average-rater absolute agreement, k=4): **+0.980**
**Krippendorff's α** (interval): **+0.924**
**Mean within-cell SD** across judges: **0.461**

### c2 (n_cells = 40)

| pair | Pearson r | Spearman ρ |
|---|---:|---:|
| claude × gemini | +0.932 | +0.843 |
| claude × gpt | +0.917 | +0.849 |
| claude × kimi | +0.901 | +0.919 |
| gemini × gpt | +0.969 | +0.938 |
| gemini × kimi | +0.879 | +0.830 |
| gpt × kimi | +0.870 | +0.798 |

**ICC(2,1)** (single-rater absolute agreement): **+0.901**
**ICC(2,k)** (average-rater absolute agreement, k=4): **+0.973**
**Krippendorff's α** (interval): **+0.899**
**Mean within-cell SD** across judges: **0.571**

### c3 (n_cells = 40)

| pair | Pearson r | Spearman ρ |
|---|---:|---:|
| claude × gemini | +0.916 | +0.695 |
| claude × gpt | +0.948 | +0.843 |
| claude × kimi | +0.912 | +0.873 |
| gemini × gpt | +0.956 | +0.868 |
| gemini × kimi | +0.894 | +0.722 |
| gpt × kimi | +0.909 | +0.820 |

**ICC(2,1)** (single-rater absolute agreement): **+0.918**
**ICC(2,k)** (average-rater absolute agreement, k=4): **+0.978**
**Krippendorff's α** (interval): **+0.917**
**Mean within-cell SD** across judges: **0.477**

## Author-level agreement

Do judges rank the four authors similarly on average?  We compute each judge's mean composite per author per condition, then correlate across judges.

| condition | judge | gpt-5.5 | claude-opus-4.7 | gemini-3.1-pro | kimi-k2.6 |
|---|---|---:|---:|---:|---:|
| c1 | claude | 8.78 | 9.78 | 8.18 | 5.08 |
| c1 | gemini | 9.04 | 9.06 | 8.38 | 5.16 |
| c1 | gpt | 8.94 | 9.46 | 8.08 | 5.30 |
| c1 | kimi | 8.20 | 9.46 | 8.18 | 5.74 |
| c2 | claude | 7.86 | 8.82 | 8.54 | 5.60 |
| c2 | gemini | 8.08 | 7.68 | 8.44 | 5.34 |
| c2 | gpt | 7.96 | 7.70 | 8.16 | 5.28 |
| c2 | kimi | 7.20 | 8.04 | 8.00 | 5.70 |
| c3 | claude | 8.78 | 9.78 | 8.18 | 5.08 |
| c3 | gemini | 8.94 | 8.92 | 8.60 | 5.20 |
| c3 | gpt | 8.94 | 9.46 | 8.08 | 5.30 |
| c3 | kimi | 8.20 | 9.46 | 8.20 | 5.74 |

### Pairwise correlation of judge-specific author means (pooled across all 3×4 = 12 author×condition cells):

| pair | Pearson r |
|---|---:|
| claude × gemini | +0.955 |
| claude × gpt | +0.975 |
| claude × kimi | +0.975 |
| gemini × gpt | +0.983 |
| gemini × kimi | +0.932 |
| gpt × kimi | +0.963 |
