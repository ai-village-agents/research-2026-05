#!/usr/bin/env python3
"""
3-panel bar chart of per-judge label-swap bias profile (self_favor, anti_kimi, pro_claude),
with 95% cluster-bootstrap CIs from results/judge_bias_profile.csv (B=4000).
"""
from pathlib import Path
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT.parent / "experiments" / "replication-wave" / "results" / "judge_bias_profile.csv"
OUT = ROOT / "plots" / "judge_bias_profile.png"

JUDGE_ORDER = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
JUDGE_SHORT = {"claude-opus-4.7": "Claude\nOpus 4.7", "gemini-3.1-pro": "Gemini\n3.1 Pro",
               "gpt-5.5": "GPT-5.5", "kimi-k2.6": "Kimi\nK2.6"}
JUDGE_COLOR = {"claude-opus-4.7": "#D97757", "gemini-3.1-pro": "#4A90E2",
               "gpt-5.5": "#2E8B57", "kimi-k2.6": "#9B59B6"}

METRICS = [
    ("self_favor",  "Self-favoritism\n(own label - others' labels)"),
    ("anti_kimi",   "Anti-Kimi tilt\n(non-Kimi labels - Kimi label)"),
    ("pro_claude",  "Pro-Claude tilt\n(Claude label - non-Claude labels)"),
]


def load():
    data = {}  # data[metric][judge] = (mean, lo, hi, sig)
    with SRC.open() as fh:
        rows = list(csv.DictReader(fh))
    for r in rows:
        m = r["metric"]
        j = r["judge"]
        data.setdefault(m, {})[j] = (
            float(r["mean"]), float(r["ci_lo"]), float(r["ci_hi"]),
            int(r["ci_excludes_zero"])
        )
    return data


def main():
    data = load()
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6), sharey=True)
    x = np.arange(len(JUDGE_ORDER))
    for ax, (metric, title) in zip(axes, METRICS):
        means = []
        errs_low = []
        errs_high = []
        colors = []
        sigs = []
        for j in JUDGE_ORDER:
            m, lo, hi, sig = data[metric][j]
            means.append(m)
            errs_low.append(m - lo)
            errs_high.append(hi - m)
            colors.append(JUDGE_COLOR[j])
            sigs.append(sig)
        bars = ax.bar(x, means, color=colors, edgecolor="black", linewidth=0.6, alpha=0.85, width=0.6)
        ax.errorbar(x, means, yerr=[errs_low, errs_high], fmt="none",
                    ecolor="black", elinewidth=1.0, capsize=4)
        for i, (m, sig) in enumerate(zip(means, sigs)):
            if sig:
                y = m + (errs_high[i] + 0.02 if m >= 0 else -(errs_low[i] + 0.04))
                ax.text(i, y, "*", ha="center", va="bottom" if m >= 0 else "top",
                        fontsize=18, fontweight="bold", color="black")
        ax.axhline(0, color="black", linewidth=0.7, alpha=0.7)
        ax.set_xticks(x)
        ax.set_xticklabels([JUDGE_SHORT[j] for j in JUDGE_ORDER], fontsize=9)
        ax.set_title(title, fontsize=10)
        ax.grid(axis="y", alpha=0.25, linestyle="--", linewidth=0.5)
        ax.set_ylim(-0.55, 0.85)
    axes[0].set_ylabel("Mean residual contrast (composite points)\n95% cluster-bootstrap CI, B=4000", fontsize=9)
    fig.suptitle("Per-judge label-swap bias profile (paired native label swap, N=320 rows / 40 responses)",
                 fontsize=12, fontweight="bold", y=1.02)
    fig.text(0.5, -0.02, "* CI excludes 0 (Bonferroni-tolerant; see results/judge_bias_profile.md and label_effect_matrix_multiplicity.md).",
             ha="center", fontsize=8, style="italic")
    plt.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(OUT, dpi=140, bbox_inches="tight")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
