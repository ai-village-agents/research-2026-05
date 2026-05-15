"""Compute and plot the 4x4 (judge, displayed_label) residual matrix.

For each (judge, response_hash) pair compute the mean composite, then take
each row's deviation from that mean. Mean those deviations within (judge,
displayed_label) cells. Bootstrap by response_hash with B=2000 to get
95% CIs. Outputs:
  experiments/replication-wave/results/label_effect_matrix.csv
  experiments/replication-wave/results/label_effect_matrix.md
  analysis/plots/label_effect_matrix.png
"""

import csv
import os
import sys
import math
import random
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE) if HERE.endswith('plots') else HERE
# Better: hardcode known root
ROOT = '/tmp/research-2026-05'

CSV_IN = os.path.join(ROOT, 'experiments/replication-wave/results/paired_label_swap.csv')
OUT_CSV = os.path.join(ROOT, 'experiments/replication-wave/results/label_effect_matrix.csv')
OUT_MD = os.path.join(ROOT, 'experiments/replication-wave/results/label_effect_matrix.md')
OUT_PNG = os.path.join(ROOT, 'analysis/plots/label_effect_matrix.png')

JUDGES = ['claude-opus-4.7', 'gemini-3.1-pro', 'gpt-5.5', 'kimi-k2.6']
LABELS = ['claude-opus-4.7', 'gemini-3.1-pro', 'gpt-5.5', 'kimi-k2.6']

def load_rows():
    rows = []
    with open(CSV_IN, newline='') as f:
        r = csv.DictReader(f)
        for row in r:
            row['composite'] = float(row['composite'])
            rows.append(row)
    return rows

def compute_residuals(rows):
    """Group by (judge, response_hash); subtract within-group mean."""
    groups = defaultdict(list)
    for r in rows:
        groups[(r['judge'], r['response_hash'])].append(r)
    residuals = []  # list of dicts: judge, displayed_label, response_hash, residual
    for (judge, rh), grp in groups.items():
        mean = sum(g['composite'] for g in grp) / len(grp)
        for g in grp:
            residuals.append({
                'judge': judge,
                'displayed_label': g['displayed_label'],
                'response_hash': rh,
                'residual': g['composite'] - mean,
                'n_in_group': len(grp),
            })
    return residuals

def matrix_means(residuals):
    out = {}
    for j in JUDGES:
        for L in LABELS:
            xs = [r['residual'] for r in residuals if r['judge']==j and r['displayed_label']==L]
            out[(j,L)] = (sum(xs)/len(xs) if xs else float('nan'), len(xs))
    return out

def boot_cis(residuals, B=2000, seed=20260515):
    rng = random.Random(seed)
    # Bootstrap clusters by response_hash (across all judges share the same hashes).
    hashes = sorted({r['response_hash'] for r in residuals})
    n = len(hashes)
    # Pre-index residuals by hash
    by_hash = defaultdict(list)
    for r in residuals:
        by_hash[r['response_hash']].append(r)
    # Accumulators
    cells = {(j,L): [] for j in JUDGES for L in LABELS}
    for b in range(B):
        sample_hashes = [hashes[rng.randrange(n)] for _ in range(n)]
        sums = defaultdict(lambda: [0.0, 0])
        for h in sample_hashes:
            for r in by_hash[h]:
                k = (r['judge'], r['displayed_label'])
                sums[k][0] += r['residual']
                sums[k][1] += 1
        for k in cells:
            if sums[k][1] > 0:
                cells[k].append(sums[k][0]/sums[k][1])
            else:
                cells[k].append(float('nan'))
    cis = {}
    for k, vals in cells.items():
        vals2 = sorted(v for v in vals if not math.isnan(v))
        if len(vals2) < 20:
            cis[k] = (float('nan'), float('nan'))
        else:
            lo = vals2[int(0.025*len(vals2))]
            hi = vals2[int(0.975*len(vals2))]
            cis[k] = (lo, hi)
    return cis

def write_outputs(point, cis):
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['judge','displayed_label','mean_residual','n','ci_lo','ci_hi','ci_excludes_zero'])
        for j in JUDGES:
            for L in LABELS:
                mean, n = point[(j,L)]
                lo, hi = cis[(j,L)]
                excl = (lo > 0 or hi < 0) if not (math.isnan(lo) or math.isnan(hi)) else False
                w.writerow([j, L, f'{mean:+.4f}', n, f'{lo:+.4f}', f'{hi:+.4f}', '1' if excl else '0'])

    lines = ['# Label Effect Matrix (judge × displayed_label)\n',
             '',
             'Mean within-(judge, response) residual by displayed label, with 2000-iter cluster-bootstrap 95% CI (cluster = response_hash).',
             '',
             '| Judge \\ Displayed label | claude | gemini | gpt | kimi |',
             '|---|---:|---:|---:|---:|']
    for j in JUDGES:
        row = [f'**{j}**']
        for L in LABELS:
            mean, n = point[(j,L)]
            lo, hi = cis[(j,L)]
            excl = (lo > 0 or hi < 0) if not (math.isnan(lo) or math.isnan(hi)) else False
            star = ' *' if excl else ''
            row.append(f'{mean:+.3f} [{lo:+.2f}, {hi:+.2f}]{star}')
        lines.append('| ' + ' | '.join(row) + ' |')
    lines.append('')
    lines.append('Cells marked with * have 95% CI excluding zero. Diagonal cells (judge==displayed_label) are the *self-label* causal effect for each judge. Off-diagonal cells reveal **directed** label biases: e.g., how does Gemini score `kimi-k2.6`-labelled responses relative to those same responses under other labels?')
    lines.append('')
    lines.append(f'Source: `experiments/replication-wave/results/paired_label_swap.csv` (N={sum(n for (m,n) in point.values())} per-row scores; 4×4=16 cells).')
    with open(OUT_MD, 'w') as f:
        f.write('\n'.join(lines))

def make_plot(point, cis):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    M = np.array([[point[(j,L)][0] for L in LABELS] for j in JUDGES])
    fig, ax = plt.subplots(figsize=(6.8, 5.4))
    vmax = max(abs(M.min()), abs(M.max()))
    im = ax.imshow(M, cmap='RdBu_r', vmin=-vmax, vmax=vmax, aspect='auto')
    short = {'claude-opus-4.7':'Claude','gemini-3.1-pro':'Gemini','gpt-5.5':'GPT-5.5','kimi-k2.6':'Kimi'}
    ax.set_xticks(range(len(LABELS))); ax.set_xticklabels([short[L] for L in LABELS], rotation=0)
    ax.set_yticks(range(len(JUDGES))); ax.set_yticklabels([short[j] for j in JUDGES])
    ax.set_xlabel('Displayed author label')
    ax.set_ylabel('Judge')
    ax.set_title('Causal label-effect matrix: mean within-response residual by displayed label\n(4 judges × 4 displayed labels; * = 95% bootstrap CI excludes 0)')
    for i, j in enumerate(JUDGES):
        for k, L in enumerate(LABELS):
            mean, n = point[(j,L)]
            lo, hi = cis[(j,L)]
            excl = (lo > 0 or hi < 0) if not (math.isnan(lo) or math.isnan(hi)) else False
            star = '*' if excl else ''
            # Highlight diagonal with bold edge
            ax.text(k, i, f'{mean:+.2f}{star}', ha='center', va='center',
                    color='black' if abs(mean) < vmax*0.55 else 'white',
                    fontsize=11, fontweight='bold' if i==k else 'normal')
    # Diagonal outline
    for i in range(len(JUDGES)):
        ax.add_patch(plt.Rectangle((i-0.5, i-0.5), 1, 1, fill=False, edgecolor='black', linewidth=1.5))
    cb = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label('Residual (display-label effect, points)')
    plt.tight_layout()
    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    plt.savefig(OUT_PNG, dpi=160, bbox_inches='tight')
    print(f'Wrote {OUT_PNG}')

def main():
    rows = load_rows()
    print(f'Loaded {len(rows)} score rows')
    residuals = compute_residuals(rows)
    print(f'Computed {len(residuals)} residuals')
    point = matrix_means(residuals)
    cis = boot_cis(residuals, B=2000)
    write_outputs(point, cis)
    print(f'Wrote {OUT_CSV}')
    print(f'Wrote {OUT_MD}')
    try:
        make_plot(point, cis)
    except Exception as e:
        print(f'Plot error: {e}')

if __name__ == '__main__':
    main()
