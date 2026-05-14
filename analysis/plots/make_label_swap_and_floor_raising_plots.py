"""Two new figures for the v1.2.0 blogpost."""
import csv
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

REPO = Path('/tmp/research-2026-05')
OUT = REPO / 'analysis' / 'plots'
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(20260515)
B = 2000

mpl.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})

# Brand colors per judge
COLORS = {
    'claude-opus-4.7': '#D87447',   # warm orange
    'gemini-3.1-pro':  '#4080D0',   # blue
    'gpt-5.5':         '#1A8F4C',   # green
    'kimi-k2.6':       '#7A4F9B',   # purple
}
PRETTY = {
    'claude-opus-4.7': 'Claude Opus 4.7',
    'gemini-3.1-pro':  'Gemini 3.1 Pro',
    'gpt-5.5':         'GPT-5.5',
    'kimi-k2.6':       'Kimi K2.6',
}

# ===== 1. Label-swap per-judge SELF-OTHER paired effect =====
psr = list(csv.DictReader(open(REPO/'experiments/replication-wave/results/paired_self_response_level.csv')))

JUDGES = ['claude-opus-4.7', 'gemini-3.1-pro', 'gpt-5.5']
results = {}
for j in JUDGES:
    deltas = [float(r['delta']) for r in psr if r['judge'] == j]
    deltas = np.array(deltas)
    mean = deltas.mean()
    # bootstrap CI on the mean
    boot = []
    for _ in range(B):
        sample = RNG.choice(deltas, size=len(deltas), replace=True)
        boot.append(sample.mean())
    lo, hi = np.percentile(boot, [2.5, 97.5])
    results[j] = (mean, lo, hi, len(deltas))
    print(f'  {j}: mean={mean:+.3f} CI=[{lo:+.3f},{hi:+.3f}] n={len(deltas)}')

# Plot
fig, ax = plt.subplots(figsize=(7, 3.6))
ys = np.arange(len(JUDGES))[::-1]
for i, j in enumerate(JUDGES):
    m, lo, hi, n = results[j]
    y = ys[i]
    col = COLORS[j]
    ax.errorbar(m, y, xerr=[[m-lo],[hi-m]], fmt='o', color=col, capsize=4,
                markersize=10, linewidth=2, label=PRETTY[j])
    ax.annotate(f'{m:+.3f}  [{lo:+.3f}, {hi:+.3f}]',
                xy=(m, y), xytext=(8, 6), textcoords='offset points',
                color=col, fontsize=9)
ax.axvline(0, color='gray', linewidth=0.8, linestyle='--', alpha=0.7)
ax.set_yticks(ys)
ax.set_yticklabels([PRETTY[j] for j in JUDGES])
ax.set_xlabel(r'Mean within-response  $\Delta = $ (self-labelled score) $-$ (other-labelled score)')
ax.set_title('Causal label-swap: per-judge paired self-preference effect\n(D408 native re-run, 3 native judges, 20 responses, 95% bootstrap CI)')
ax.grid(axis='x', alpha=0.3, linestyle=':')
# Annotate Kimi-not-available
ax.text(0.99, -0.18, 'Kimi K2.6: no native label-swap data (open question)',
        transform=ax.transAxes, ha='right', va='top', fontsize=8.5, color='#7A4F9B', style='italic')
plt.tight_layout()
out1 = OUT/'label_swap_per_judge.png'
plt.savefig(out1, dpi=150, bbox_inches='tight')
print(f'wrote {out1}')
plt.close()

# ===== 2. Floor-raising scatter: Δ vs baseline (other-label) per judge =====
fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
for ax, j in zip(axes, JUDGES):
    rows = [r for r in psr if r['judge'] == j]
    base = np.array([float(r['other_composite']) for r in rows])
    delta = np.array([float(r['delta']) for r in rows])
    col = COLORS[j]
    ax.scatter(base, delta, color=col, alpha=0.7, s=42, edgecolors='white', linewidths=0.6)
    # Spearman ρ
    if base.std() > 0 and delta.std() > 0:
        rho = np.corrcoef(np.argsort(np.argsort(base)), np.argsort(np.argsort(delta)))[0,1]
    else:
        rho = float('nan')
    # bootstrap CI on Spearman
    rhos = []
    n = len(base)
    for _ in range(B):
        idx = RNG.integers(0, n, n)
        b = base[idx]; d = delta[idx]
        if b.std() > 0 and d.std() > 0:
            rr = np.corrcoef(np.argsort(np.argsort(b)), np.argsort(np.argsort(d)))[0,1]
            rhos.append(rr)
    if rhos:
        lo, hi = np.percentile(rhos, [2.5, 97.5])
    else:
        lo = hi = float('nan')
    # Fit OLS
    if base.std() > 0:
        z = np.polyfit(base, delta, 1)
        xs = np.linspace(base.min(), base.max(), 50)
        ax.plot(xs, np.polyval(z, xs), color=col, linewidth=1.3, alpha=0.6, linestyle='--')
    ax.axhline(0, color='gray', linewidth=0.8, alpha=0.6)
    ax.set_title(f'{PRETTY[j]}\nρ = {rho:+.2f}  [{lo:+.2f}, {hi:+.2f}]', fontsize=10)
    ax.set_xlabel('Baseline composite (other-labelled)')
    ax.grid(alpha=0.3, linestyle=':')
axes[0].set_ylabel('Within-response Δ\n(self-labelled − other-labelled)')
fig.suptitle('Floor-raising: the self-preference effect is largest when the baseline score is low\n(per-response, n=20 per judge, 95% bootstrap CI on Spearman ρ)',
             fontsize=11, y=1.04)
plt.tight_layout()
out2 = OUT/'floor_raising_scatter.png'
plt.savefig(out2, dpi=150, bbox_inches='tight')
print(f'wrote {out2}')
plt.close()

print('done')
