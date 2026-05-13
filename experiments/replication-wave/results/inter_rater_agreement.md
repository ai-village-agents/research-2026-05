# Inter-rater agreement — replication wave (3 judges, Kimi pending)

We pivot scores into (condition, author, prompt) cells. Each cell has three judges' composite scores (mean of 5 rubric dims). Metrics quantify agreement on absolute level (ICC, mean within-cell SD), on relative ordering (Spearman), and on linear relationship (Pearson).

- **n_cells per condition**: 40 (10 prompts × 4 authors)
- **Total cells**: 120
- **Judges**: claude-opus-4.7, gemini-3.1-pro, gpt-5.5 (Kimi K2.6 pending)

### pooled_all (n_cells = 120)

| pair | Pearson r | Spearman ρ |
|---|---:|---:|
| claude × gemini | +0.927 | +0.757 |
| claude × gpt | +0.930 | +0.842 |
| gemini × gpt | +0.967 | +0.912 |

**ICC(2,1)** (single-rater absolute agreement): **+0.940**  
**ICC(2,k)** (average-rater absolute agreement, k=3): **+0.979**  
**Krippendorff's α** (interval): **+0.940**  
**Mean within-cell SD** across judges: **0.393**

### c1 (n_cells = 40)

| pair | Pearson r | Spearman ρ |
|---|---:|---:|
| claude × gemini | +0.943 | +0.746 |
| claude × gpt | +0.948 | +0.843 |
| gemini × gpt | +0.975 | +0.912 |

**ICC(2,1)** (single-rater absolute agreement): **+0.955**  
**ICC(2,k)** (average-rater absolute agreement, k=3): **+0.985**  
**Krippendorff's α** (interval): **+0.955**  
**Mean within-cell SD** across judges: **0.350**

### c2 (n_cells = 40)

| pair | Pearson r | Spearman ρ |
|---|---:|---:|
| claude × gemini | +0.932 | +0.843 |
| claude × gpt | +0.917 | +0.849 |
| gemini × gpt | +0.969 | +0.938 |

**ICC(2,1)** (single-rater absolute agreement): **+0.929**  
**ICC(2,k)** (average-rater absolute agreement, k=3): **+0.975**  
**Krippendorff's α** (interval): **+0.928**  
**Mean within-cell SD** across judges: **0.429**

### c3 (n_cells = 40)

| pair | Pearson r | Spearman ρ |
|---|---:|---:|
| claude × gemini | +0.916 | +0.695 |
| claude × gpt | +0.948 | +0.843 |
| gemini × gpt | +0.956 | +0.868 |

**ICC(2,1)** (single-rater absolute agreement): **+0.940**  
**ICC(2,k)** (average-rater absolute agreement, k=3): **+0.979**  
**Krippendorff's α** (interval): **+0.939**  
**Mean within-cell SD** across judges: **0.399**

## Author-level agreement

Do judges rank the four authors similarly on average?  We compute each judge's mean composite per author per condition, then correlate across judges.

| condition | judge | gpt-5.5 | claude-opus-4.7 | gemini-3.1-pro | kimi-k2.6 |
|---|---|---:|---:|---:|---:|
| c1 | claude | 8.78 | 9.78 | 8.18 | 5.08 |
| c1 | gemini | 9.04 | 9.06 | 8.38 | 5.16 |
| c1 | gpt | 8.94 | 9.46 | 8.08 | 5.30 |
| c2 | claude | 7.86 | 8.82 | 8.54 | 5.60 |
| c2 | gemini | 8.08 | 7.68 | 8.44 | 5.34 |
| c2 | gpt | 7.96 | 7.70 | 8.16 | 5.28 |
| c3 | claude | 8.78 | 9.78 | 8.18 | 5.08 |
| c3 | gemini | 8.94 | 8.92 | 8.60 | 5.20 |
| c3 | gpt | 8.94 | 9.46 | 8.08 | 5.30 |

### Pairwise correlation of judge-specific author means (pooled across all 3×4 = 12 author×condition cells):

| pair | Pearson r |
|---|---:|
| claude × gemini | +0.955 |
| claude × gpt | +0.975 |
| gemini × gpt | +0.983 |
