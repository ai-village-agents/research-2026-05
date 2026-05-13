"""Inter-rater agreement analysis for the replication wave.

For each (condition, author, prompt) cell, three judges each produce a composite
mean5 score. We measure:
- Pairwise Pearson correlation between every pair of judges (per condition and pooled).
- Pairwise Spearman (rank) correlation.
- Mean within-cell standard deviation across judges (smaller = more agreement on absolute level).
- ICC(2,1) and ICC(2,k) — two-way random effects, single-rater and average-rater.
- Krippendorff's alpha (interval).

Inputs:  experiments/replication-wave/results/long_scores.csv
Outputs: experiments/replication-wave/results/inter_rater_agreement.{csv,md}
"""
import csv, math, json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

ROOT = Path('/tmp/research-2026-05')
SRC  = ROOT / 'experiments/replication-wave/results/long_scores.csv'
OUT_CSV = ROOT / 'experiments/replication-wave/results/inter_rater_agreement.csv'
OUT_MD  = ROOT / 'experiments/replication-wave/results/inter_rater_agreement.md'

DIMS = ['correctness','completeness','clarity','creativity','constraint_adherence']
JUDGES = ['claude-opus-4.7','gemini-3.1-pro','gpt-5.5']

def composite(row):
    return sum(float(row[d]) for d in DIMS)/5

# Load and pivot: (cond, author, prompt) -> {judge: composite}
cells = defaultdict(dict)
for r in csv.DictReader(open(SRC)):
    key = (r['condition'], r['author'], r['prompt_id'])
    cells[key][r['judge']] = composite(r)

def pearson(xs, ys):
    n = len(xs)
    mx, my = sum(xs)/n, sum(ys)/n
    num = sum((x-mx)*(y-my) for x,y in zip(xs,ys))
    dx = math.sqrt(sum((x-mx)**2 for x in xs))
    dy = math.sqrt(sum((y-my)**2 for y in ys))
    return num/(dx*dy) if dx>0 and dy>0 else float('nan')

def spearman(xs, ys):
    def ranks(vs):
        idx = sorted(range(len(vs)), key=lambda i: vs[i])
        rk = [0]*len(vs)
        # average-rank for ties
        i = 0
        while i < len(vs):
            j = i
            while j+1 < len(vs) and vs[idx[j+1]] == vs[idx[i]]:
                j += 1
            avg = (i+j)/2 + 1
            for k in range(i, j+1):
                rk[idx[k]] = avg
            i = j+1
        return rk
    return pearson(ranks(xs), ranks(ys))

def icc_two_way(matrix):
    """ICC(2,1) and ICC(2,k) — two-way random effects, absolute agreement.
    matrix: n_targets x k_raters.
    Following Shrout & Fleiss 1979.
    """
    n = len(matrix)
    k = len(matrix[0])
    grand = sum(sum(row) for row in matrix)/(n*k)
    row_means = [sum(row)/k for row in matrix]
    col_means = [sum(matrix[i][j] for i in range(n))/n for j in range(k)]
    # SSR = k * Σ (r_i - grand)^2  (between subjects)
    SSR = k * sum((rm - grand)**2 for rm in row_means)
    # SSC = n * Σ (c_j - grand)^2  (between raters)
    SSC = n * sum((cm - grand)**2 for cm in col_means)
    # SST = Σ Σ (x_ij - grand)^2
    SST = sum((matrix[i][j] - grand)**2 for i in range(n) for j in range(k))
    SSE = SST - SSR - SSC
    MSR = SSR/(n-1)
    MSC = SSC/(k-1)
    MSE = SSE/((n-1)*(k-1))
    icc_2_1 = (MSR - MSE) / (MSR + (k-1)*MSE + k*(MSC-MSE)/n)
    icc_2_k = (MSR - MSE) / (MSR + (MSC-MSE)/n)
    return icc_2_1, icc_2_k

def krippendorff_alpha_interval(matrix):
    """Krippendorff's alpha (interval), where matrix is units × raters; all complete."""
    n = len(matrix)
    k = len(matrix[0])
    # Observed disagreement Do = average squared diff within unit
    Do_sum = 0
    pairs = 0
    for row in matrix:
        for a, b in combinations(row, 2):
            Do_sum += (a-b)**2
            pairs += 1
    Do = Do_sum / pairs
    # Expected disagreement De = average squared diff across all values
    flat = [v for row in matrix for v in row]
    De_sum = 0
    De_pairs = 0
    for i in range(len(flat)):
        for j in range(i+1, len(flat)):
            De_sum += (flat[i]-flat[j])**2
            De_pairs += 1
    De = De_sum / De_pairs
    return 1 - Do/De

# Build matrices per condition
results_rows = [['scope','metric','value','n_cells']]
md_lines = []

def write_section(label, cell_keys):
    matrix = []
    for k in cell_keys:
        d = cells[k]
        if all(j in d for j in JUDGES):
            matrix.append([d[j] for j in JUDGES])
    n = len(matrix)
    if n < 5:
        return
    md_lines.append(f"\n### {label} (n_cells = {n})\n")
    # Pairwise correlations
    md_lines.append("| pair | Pearson r | Spearman ρ |")
    md_lines.append("|---|---:|---:|")
    for (i, ji), (jx, jj) in combinations(enumerate(JUDGES), 2):
        xs = [m[i] for m in matrix]
        ys = [m[jx] for m in matrix]
        r = pearson(xs, ys)
        rho = spearman(xs, ys)
        short_i = ji.split('-')[0]
        short_j = jj.split('-')[0]
        md_lines.append(f"| {short_i} × {short_j} | {r:+.3f} | {rho:+.3f} |")
        results_rows.append([label, f'pearson_{short_i}_{short_j}', f'{r:.4f}', n])
        results_rows.append([label, f'spearman_{short_i}_{short_j}', f'{rho:.4f}', n])
    # ICC and alpha
    icc1, icck = icc_two_way(matrix)
    alpha = krippendorff_alpha_interval(matrix)
    # within-cell SD: avg standard deviation of judges within a cell
    mean_sd = sum(math.sqrt(sum((v - sum(m)/len(m))**2 for v in m)/(len(m)-1)) for m in matrix)/n
    md_lines.append(f"\n**ICC(2,1)** (single-rater absolute agreement): **{icc1:+.3f}**  ")
    md_lines.append(f"**ICC(2,k)** (average-rater absolute agreement, k=3): **{icck:+.3f}**  ")
    md_lines.append(f"**Krippendorff's α** (interval): **{alpha:+.3f}**  ")
    md_lines.append(f"**Mean within-cell SD** across judges: **{mean_sd:.3f}**")
    results_rows.append([label, 'icc_2_1', f'{icc1:.4f}', n])
    results_rows.append([label, 'icc_2_k', f'{icck:.4f}', n])
    results_rows.append([label, 'krippendorff_alpha', f'{alpha:.4f}', n])
    results_rows.append([label, 'mean_within_cell_sd', f'{mean_sd:.4f}', n])

# Pooled across all three conditions
write_section('pooled_all', [k for k in cells.keys()])
# Per condition
for cond in ['c1','c2','c3']:
    write_section(f'{cond}', [k for k in cells.keys() if k[0]==cond])

# Author-level: do judges agree on which authors are good?
md_lines.append("\n## Author-level agreement\n")
md_lines.append("Do judges rank the four authors similarly on average?  We compute each judge's mean composite per author per condition, then correlate across judges.\n")
md_lines.append("| condition | judge | gpt-5.5 | claude-opus-4.7 | gemini-3.1-pro | kimi-k2.6 |")
md_lines.append("|---|---|---:|---:|---:|---:|")
AUTHORS = ['gpt-5.5','claude-opus-4.7','gemini-3.1-pro','kimi-k2.6']
author_means = {}
for cond in ['c1','c2','c3']:
    for j in JUDGES:
        means = {}
        for a in AUTHORS:
            ks = [(c,au,p) for (c,au,p) in cells if c==cond and au==a]
            vals = [cells[k][j] for k in ks if j in cells[k]]
            means[a] = sum(vals)/len(vals) if vals else float('nan')
        author_means[(cond,j)] = means
        short = j.split('-')[0]
        md_lines.append(f"| {cond} | {short} | {means['gpt-5.5']:.2f} | {means['claude-opus-4.7']:.2f} | {means['gemini-3.1-pro']:.2f} | {means['kimi-k2.6']:.2f} |")

md_lines.append("\n### Pairwise correlation of judge-specific author means (pooled across all 3×4 = 12 author×condition cells):\n")
md_lines.append("| pair | Pearson r |")
md_lines.append("|---|---:|")
for ji, jj in combinations(JUDGES, 2):
    xs = []; ys = []
    for cond in ['c1','c2','c3']:
        for a in AUTHORS:
            xs.append(author_means[(cond,ji)][a])
            ys.append(author_means[(cond,jj)][a])
    r = pearson(xs, ys)
    si, sj = ji.split('-')[0], jj.split('-')[0]
    md_lines.append(f"| {si} × {sj} | {r:+.3f} |")
    results_rows.append(['author_means_pool', f'pearson_{si}_{sj}', f'{r:.4f}', len(xs)])

header = f"""# Inter-rater agreement — replication wave (3 judges, Kimi pending)

We pivot scores into (condition, author, prompt) cells. Each cell has three judges' composite scores (mean of 5 rubric dims). Metrics quantify agreement on absolute level (ICC, mean within-cell SD), on relative ordering (Spearman), and on linear relationship (Pearson).

- **n_cells per condition**: 40 (10 prompts × 4 authors)
- **Total cells**: 120
- **Judges**: claude-opus-4.7, gemini-3.1-pro, gpt-5.5 (Kimi K2.6 pending)
"""

OUT_MD.write_text(header + '\n'.join(md_lines) + '\n')
import csv as _csv
with open(OUT_CSV, 'w') as f:
    w = _csv.writer(f)
    w.writerows(results_rows)

print('Wrote', OUT_MD)
print('Wrote', OUT_CSV)
print()
print(OUT_MD.read_text())
