# Inter-Rater Reliability (ICC) for C1 Baseline

**Overall ICC(2,1) (Absolute Agreement):** 0.925
**Overall ICC(3,1) (Consistency):** 0.924

### By Dimension
| Dimension | ICC(2,1) | ICC(3,1) |
|-----------|----------|----------|
| correctness | 0.851 | 0.849 |
| completeness | 0.871 | 0.871 |
| clarity | 0.782 | 0.812 |
| creativity | 0.868 | 0.874 |
| constraint_adherence | 0.912 | 0.911 |

### Leave-One-Judge-Out ICC(2,1)
- Dropping `claude-opus-4.7`: 0.921
- Dropping `gemini-3.1-pro`: 0.914
- Dropping `gpt-5.5`: 0.908
- Dropping `kimi-k2.6`: 0.955

### Commentary
The Leave-One-Judge-Out analysis shows that overall inter-rater reliability increases when Kimi K2.6 is excluded. This helps quantify the extent to which each judge's idiosyncratic scoring patterns (e.g., Kimi's harsh self-penalization) disrupt overall consensus.
