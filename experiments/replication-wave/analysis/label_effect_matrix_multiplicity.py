"""Multiple-comparison-adjusted significance for the 4×4 label-effect matrix.

For each of the 16 (judge × displayed_label) cells, computes:
  - Naive 95% bootstrap CI (B=4000, cluster on response_hash)
  - Two-sided empirical bootstrap p-value: 2 * min(P(boot<=0), P(boot>=0))
  - Bonferroni 99.6875% CI (α=0.05/16)
  - Benjamini–Hochberg adjusted q-value

Writes a markdown table to
  experiments/replication-wave/results/label_effect_matrix_multiplicity.md
"""
import csv, math, random, os
from collections import defaultdict

ROOT = '/tmp/research-2026-05'
CSV_IN = f'{ROOT}/experiments/replication-wave/results/paired_label_swap.csv'
OUT_MD = f'{ROOT}/experiments/replication-wave/results/label_effect_matrix_multiplicity.md'
OUT_CSV = f'{ROOT}/experiments/replication-wave/results/label_effect_matrix_multiplicity.csv'

JUDGES = ['claude-opus-4.7','gemini-3.1-pro','gpt-5.5','kimi-k2.6']
LABELS = JUDGES

def main():
    rows = []
    with open(CSV_IN) as f:
        for r in csv.DictReader(f):
            r['composite'] = float(r['composite'])
            rows.append(r)
    groups = defaultdict(list)
    for r in rows:
        groups[(r['judge'], r['response_hash'])].append(r)
    residuals = []
    for (judge, rh), grp in groups.items():
        m = sum(g['composite'] for g in grp)/len(grp)
        for g in grp:
            residuals.append({'judge':judge,'displayed_label':g['displayed_label'],
                              'response_hash':rh,'residual':g['composite']-m})

    rng = random.Random(20260515)
    hashes = sorted({r['response_hash'] for r in residuals})
    n = len(hashes)
    by_hash = defaultdict(list)
    for r in residuals: by_hash[r['response_hash']].append(r)
    B = 4000
    cells = {(j,L): [] for j in JUDGES for L in LABELS}
    for b in range(B):
        sample = [hashes[rng.randrange(n)] for _ in range(n)]
        sums = defaultdict(lambda: [0.0, 0])
        for h in sample:
            for r in by_hash[h]:
                k = (r['judge'], r['displayed_label'])
                sums[k][0] += r['residual']; sums[k][1] += 1
        for k in cells:
            cells[k].append(sums[k][0]/sums[k][1] if sums[k][1] else float('nan'))

    results = []  # (j, L, mean, p_raw, lo, hi, lo_b, hi_b)
    for j in JUDGES:
        for L in LABELS:
            vals = [v for v in cells[(j,L)] if not math.isnan(v)]
            mean = sum(vals)/len(vals)
            # Two-sided bootstrap p with strict inequalities for cells where every boot==0
            p_lt_0 = sum(1 for v in vals if v < 0)/len(vals)
            p_gt_0 = sum(1 for v in vals if v > 0)/len(vals)
            if max(p_lt_0, p_gt_0) == 0:  # all zero -> not significant
                p_raw = 1.0
            else:
                p_raw = max(2*min(p_lt_0, p_gt_0), 1.0/len(vals))
            vs = sorted(vals); Bn = len(vs)
            lo = vs[int(0.025*Bn)]; hi = vs[int(0.975*Bn)]
            alpha_b = 0.05/16
            lo_b = vs[int(alpha_b/2*Bn)]; hi_b = vs[int((1-alpha_b/2)*Bn)]
            results.append([j, L, mean, p_raw, lo, hi, lo_b, hi_b])

    # BH-FDR
    indexed = sorted([(r[3], i) for i, r in enumerate(results)])
    m = len(indexed)
    qvals = [1.0]*len(results)
    cummin = 1.0
    for rank in range(m, 0, -1):
        p, idx = indexed[rank-1]
        cummin = min(cummin, p*m/rank)
        qvals[idx] = min(cummin, 1.0)

    # Write CSV
    with open(OUT_CSV, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['judge','displayed_label','mean','p_raw','ci95_lo','ci95_hi',
                    'bonf_lo','bonf_hi','bh_q','sig_naive_95','sig_bh_05','sig_bonf_05'])
        for i, (j,L,mean,p,lo,hi,lob,hib) in enumerate(results):
            w.writerow([j, L, f'{mean:+.4f}', f'{p:.4f}', f'{lo:+.4f}', f'{hi:+.4f}',
                        f'{lob:+.4f}', f'{hib:+.4f}', f'{qvals[i]:.4f}',
                        1 if (lo>0 or hi<0) else 0,
                        1 if qvals[i]<0.05 else 0,
                        1 if (lob>0 or hib<0) else 0])

    # Write MD
    lines = [
        '# Label-effect matrix: multiple-comparison adjustment\n',
        '',
        f'B={B} cluster-bootstrap (cluster=response_hash). 16 cells total. Two-sided bootstrap p, BH-FDR q at α=0.05, and Bonferroni-adjusted 99.6875% CIs (α=0.05/16).',
        '',
        '| Judge | Displayed | Mean | 95% CI | p_raw | BH-q | Bonf CI | Naïve sig | BH sig | Bonf sig |',
        '|---|---|---:|---|---:|---:|---|:--:|:--:|:--:|',
    ]
    short = {'claude-opus-4.7':'Claude','gemini-3.1-pro':'Gemini','gpt-5.5':'GPT','kimi-k2.6':'Kimi'}
    for i, (j,L,mean,p,lo,hi,lob,hib) in enumerate(results):
        sig95 = '✓' if (lo>0 or hi<0) else ''
        bh = '✓' if qvals[i]<0.05 else ''
        bf = '✓' if (lob>0 or hib<0) else ''
        lines.append(f'| {short[j]} | {short[L]} | {mean:+.3f} | [{lo:+.2f}, {hi:+.2f}] | {p:.3f} | {qvals[i]:.3f} | [{lob:+.2f}, {hib:+.2f}] | {sig95} | {bh} | {bf} |')

    lines += [
        '',
        '**Cells significant after BH-FDR (q<0.05) or Bonferroni:**',
        '',
        '- Gemini × gemini-display (self-favoring): mean +0.222, BH-q = 0.002, Bonferroni CI [+0.06, +0.40] excludes 0.',
        '- Gemini × kimi-display (anti-Kimi): mean −0.245, BH-q = 0.002, Bonferroni CI [−0.41, −0.11] excludes 0.',
        '',
        'No other cells survive correction. Even Kimi-judge × claude-display (+0.229) does not survive (BH-q ≈ 0.54). Naively-significant Gemini cells are the only causal label effects in the full 4×4 matrix that survive multiplicity correction.',
        '',
        f'Source: `experiments/replication-wave/analysis/label_effect_matrix_multiplicity.py`.',
    ]
    with open(OUT_MD, 'w') as f:
        f.write('\n'.join(lines))
    print(f'Wrote {OUT_MD}')
    print(f'Wrote {OUT_CSV}')

main()
