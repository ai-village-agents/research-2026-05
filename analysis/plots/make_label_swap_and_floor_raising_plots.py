"""Two headline figures for the v1.2.0 blogpost.

Figure 4 — label_swap_per_judge.png : per-judge paired SELF − OTHER mean Δ with 95% bootstrap CI.
Figure 5 — floor_raising_scatter.png : per-response Δ vs baseline composite with Spearman ρ + CI.

Run from anywhere:
    python3 /path/to/make_label_swap_and_floor_raising_plots.py
"""
import csv
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

# Repo root: this file lives at <repo>/analysis/plots/.
REPO = Path(__file__).resolve().parents[2]
OUT = REPO / 'analysis' / 'plots'
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(20260515)
B = 2000

mpl.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})

def _rankdata_average(values):
    """Return average ranks for a 1D numeric array, handling ties."""
    arr = np.asarray(values)
    order = np.argsort(arr, kind='mergesort')
    ranks = np.empty(len(arr), dtype=float)
    i = 0
    while i < len(arr):
        j = i + 1
        while j < len(arr) and arr[order[j]] == arr[order[i]]:
            j += 1
        # 1-indexed average rank for the tied block.
        avg_rank = (i + 1 + j) / 2.0
        ranks[order[i:j]] = avg_rank
        i = j
    return ranks


def spearmanr_np(x, y):
    """Spearman rho for two arrays; returns nan if either side is constant."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 2 or np.all(x == x[0]) or np.all(y == y[0]):
        return float('nan')
    rx = _rankdata_average(x)
    ry = _rankdata_average(y)
    return float(np.corrcoef(rx, ry)[0, 1])


COLORS = {
    'claude-opus-4.7': '#D87447',
    'gemini-3.1-pro':  '#4080D0',
    'gpt-5.5':         '#1A8F4C',
    'kimi-k2.6':       '#7A4F9B',
}
PRETTY = {
    'claude-opus-4.7': 'Claude Opus 4.7',
    'gemini-3.1-pro':  'Gemini 3.1 Pro',
    'gpt-5.5':         'GPT-5.5',
    'kimi-k2.6':       'Kimi K2.6',
}

psr = list(csv.DictReader(open(REPO/'experiments/replication-wave/results/paired_self_response_level.csv')))
JUDGES = ['claude-opus-4.7', 'gemini-3.1-pro', 'gpt-5.5']

# ===== Figure 4: per-judge paired SELF-OTHER mean Δ =====
results = {}
for j in JUDGES:
    deltas = np.array([float(r['delta']) for r in psr if r['judge'] == j])
    mean = deltas.mean()
    boots = np.array([RNG.choice(deltas, size=len(deltas), replace=True).mean() for _ in range(B)])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    results[j] = (mean, lo, hi, len(deltas))
    print(f'  {j}: mean={mean:+.3f} CI=[{lo:+.3f},{hi:+.3f}] n={len(deltas)}')

fig, ax = plt.subplots(figsize=(7, 3.6))
ys = np.arange(len(JUDGES))[::-1]
for i, j in enumerate(JUDGES):
    m, lo, hi, _ = results[j]
    ax.errorbar(m, ys[i], xerr=[[m-lo],[hi-m]], fmt='o', color=COLORS[j], capsize=4,
                markersize=10, linewidth=2)
    ax.annotate(f'{m:+.3f}  [{lo:+.3f}, {hi:+.3f}]',
                xy=(m, ys[i]), xytext=(8, 6), textcoords='offset points',
                color=COLORS[j], fontsize=9)
ax.axvline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.7)
ax.set_yticks(ys); ax.set_yticklabels([PRETTY[j] for j in JUDGES])
ax.set_xlabel(r'Mean within-response  $\Delta = $ (self-labelled score) $-$ (other-labelled score)')
ax.set_title('Causal label-swap: per-judge paired self-preference effect\n'
             '(D408 native re-run, 3 native judges, 20 responses, 95% bootstrap CI)')
ax.grid(axis='x', alpha=0.3, linestyle=':')
ax.text(0.99, -0.18, 'Kimi K2.6: no native label-swap data (open question)',
        transform=ax.transAxes, ha='right', va='top', fontsize=8.5, color='#7A4F9B', style='italic')
plt.tight_layout()
plt.savefig(OUT/'label_swap_per_judge.png', dpi=150, bbox_inches='tight')
plt.close()

# ===== Figure 5: floor-raising scatter =====
fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
for ax, j in zip(axes, JUDGES):
    rows = [r for r in psr if r['judge'] == j]
    base = np.array([float(r['other_composite']) for r in rows])
    delta = np.array([float(r['delta']) for r in rows])
    col = COLORS[j]
    ax.scatter(base, delta, color=col, alpha=0.7, s=42, edgecolors='white', linewidths=0.6)
    if delta.std() == 0:
        title = f'{PRETTY[j]}\nρ undefined (Δ = 0 for all)'
    else:
        rho_pt = spearmanr_np(base, delta)
        # bootstrap CI on Spearman
        rhos = []
        n = len(base)
        for _ in range(B):
            idx = RNG.integers(0, n, n)
            try:
                rr = spearmanr_np(base[idx], delta[idx])
                if rr == rr:  # not nan
                    rhos.append(rr)
            except Exception:
                pass
        if rhos:
            lo, hi = np.percentile(rhos, [2.5, 97.5])
            title = f'{PRETTY[j]}\nρ = {rho_pt:+.2f}  [{lo:+.2f}, {hi:+.2f}]'
        else:
            title = f'{PRETTY[j]}\nρ = {rho_pt:+.2f}'
        if base.std() > 0:
            z = np.polyfit(base, delta, 1)
            xs = np.linspace(base.min(), base.max(), 50)
            ax.plot(xs, np.polyval(z, xs), color=col, linewidth=1.3, alpha=0.6, linestyle='--')
    ax.axhline(0, color='gray', linewidth=0.8, alpha=0.6)
    ax.set_title(title, fontsize=10)
    ax.set_xlabel('Baseline composite (other-labelled)')
    ax.grid(alpha=0.3, linestyle=':')
axes[0].set_ylabel('Within-response Δ\n(self-labelled − other-labelled)')
fig.suptitle('Floor-raising: the self-preference effect is largest when the baseline score is low\n'
             '(per-response, n=20 per judge, 95% bootstrap CI on Spearman ρ)',
             fontsize=11, y=1.04)
plt.tight_layout()
plt.savefig(OUT/'floor_raising_scatter.png', dpi=150, bbox_inches='tight')
plt.close()
print('done')
