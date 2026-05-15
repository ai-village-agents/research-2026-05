#!/usr/bin/env python3
"""Plot Recognition vs Label-swap self-effect across 4 judges."""
import csv, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CSV = pathlib.Path("/tmp/research-2026-05/experiments/replication-wave/results/recognition_x_labelswap.csv")
OUT = pathlib.Path("/tmp/research-2026-05/analysis/plots/recognition_x_labelswap.png")
OUT.parent.mkdir(parents=True, exist_ok=True)

rows = list(csv.DictReader(open(CSV)))
COLORS = {
    "claude-opus-4.7": "#d97757",
    "gemini-3.1-pro":  "#4285f4",
    "gpt-5.5":         "#10a37f",
    "kimi-k2.6":       "#5b3eab",
}
SHORT = {
    "claude-opus-4.7": "Claude Opus 4.7",
    "gemini-3.1-pro":  "Gemini 3.1 Pro",
    "gpt-5.5":         "GPT-5.5",
    "kimi-k2.6":       "Kimi K2.6",
}

fig, axes = plt.subplots(1, 2, figsize=(12, 5.2))

def panel(ax, xkey, xlabel, xticks=None):
    for r in rows:
        x = float(r[xkey])
        y = float(r["label_swap_self_effect"])
        lo = float(r["label_swap_self_ci_lo"])
        hi = float(r["label_swap_self_ci_hi"])
        c = COLORS[r["judge"]]
        ax.errorbar(x, y, yerr=[[y-lo],[hi-y]], fmt="o", markersize=12,
                    color=c, ecolor=c, capsize=4, elinewidth=1.5,
                    markeredgecolor="black", markeredgewidth=0.7, alpha=0.95)
        # label offset
        dy = 0.02
        if r["judge"] == "claude-opus-4.7": dx, dy = 0.02, -0.04
        elif r["judge"] == "gpt-5.5":       dx, dy = -0.04, -0.04
        elif r["judge"] == "kimi-k2.6":     dx, dy = 0.02, 0.02
        else:                                dx, dy = 0.02, 0.02
        ax.annotate(SHORT[r["judge"]], (x, y), xytext=(x+dx, y+dy),
                    fontsize=10, color=c, fontweight="bold")
    ax.axhline(0, color="gray", lw=0.7, linestyle="--", alpha=0.7)
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_ylabel("Causal label-swap self-effect\n(within-response residual, self - other displayed)", fontsize=10)
    ax.set_ylim(-0.30, 0.40)
    if xticks: ax.set_xticks(xticks)
    ax.grid(True, alpha=0.25)

panel(axes[0], "self_recog_rate", "C4 self-recognition rate (hits / 10)",
      xticks=[0, 0.1, 0.5, 1.0])
panel(axes[1], "overall_recog_acc", "C4 overall recognition accuracy (correct / 40)",
      xticks=[0.3, 0.5, 0.625, 0.9, 1.0])

axes[0].set_title("By self-recognition rate", fontsize=12)
axes[1].set_title("By overall recognition accuracy", fontsize=12)

fig.suptitle("Recognition x Causal Label-Swap Interaction (n = 4 judges)\n"
             "Belief-channel hypothesis would predict positive slope; observed Spearman is near zero / mildly negative.",
             fontsize=12.5, fontweight="bold")
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig(OUT, dpi=130, bbox_inches="tight")
print("Saved", OUT)
