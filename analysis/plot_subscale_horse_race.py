#!/usr/bin/env python3
"""Plot indirect-effect heatmaps from subscale × condition horse-race (PR #65).

Two-panel figure:
  Left  panel: belief channel (a1·b1 via predicted_self)
  Right panel: style channel  (a2·b2 via style_prob_self)
Rows = 5 rubric dimensions (in design order).
Cols = 3 conditions (C1, C2, C3).
Cell value = point estimate of indirect effect, in score-points.
Bold border around cells whose 95% CI excludes 0.

Diverging colormap centered at 0.
"""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
from matplotlib.patches import Rectangle

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
DIM_LABELS = ["Correctness", "Completeness", "Clarity", "Creativity", "Constraint\nadherence"]
CONDS = ["c1", "c2", "c3"]
COND_LABELS = ["C1\nbaseline", "C2\nparaphrased", "C3\nwarned"]


def build_grid(df, point_col, lo_col, hi_col):
    point = np.zeros((len(DIMS), len(CONDS)))
    sig = np.zeros((len(DIMS), len(CONDS)), dtype=bool)
    for i, d in enumerate(DIMS):
        for j, c in enumerate(CONDS):
            row = df[(df["dimension"] == d) & (df["condition"] == c)].iloc[0]
            point[i, j] = row[point_col]
            lo, hi = row[lo_col], row[hi_col]
            sig[i, j] = (lo > 0) or (hi < 0)
    return point, sig


def draw_panel(ax, grid, sig, title, vlim=0.6):
    norm = TwoSlopeNorm(vmin=-vlim, vcenter=0, vmax=vlim)
    im = ax.imshow(grid, cmap="RdBu_r", norm=norm, aspect="auto")
    # cell text + significance border
    for i in range(grid.shape[0]):
        for j in range(grid.shape[1]):
            v = grid[i, j]
            ax.text(j, i, f"{v:+.2f}", ha="center", va="center",
                    fontsize=11, fontweight="bold",
                    color="white" if abs(v) > 0.25 else "black")
            if sig[i, j]:
                rect = Rectangle((j - 0.5, i - 0.5), 1, 1, linewidth=2.5,
                                 edgecolor="black", facecolor="none")
                ax.add_patch(rect)
    ax.set_xticks(range(len(CONDS)))
    ax.set_xticklabels(COND_LABELS, fontsize=10)
    ax.set_yticks(range(len(DIMS)))
    ax.set_yticklabels(DIM_LABELS, fontsize=10)
    ax.set_title(title, fontsize=12, fontweight="bold")
    return im


def main():
    df = pd.read_csv(os.path.join(REPO, "results/subscale_horse_race.csv"))
    belief, belief_sig = build_grid(df, "indirect_pred",
                                    "indirect_pred_lo", "indirect_pred_hi")
    style, style_sig = build_grid(df, "indirect_style",
                                  "indirect_style_lo", "indirect_style_hi")

    vlim = float(np.ceil(max(np.abs(belief).max(), np.abs(style).max()) * 10) / 10)
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), constrained_layout=True)

    im1 = draw_panel(axes[0], belief, belief_sig,
                     "Belief channel\n(indirect via predicted_self)", vlim=vlim)
    im2 = draw_panel(axes[1], style, style_sig,
                     "Style channel\n(indirect via style_prob_self)", vlim=vlim)

    cbar = fig.colorbar(im2, ax=axes, shrink=0.88, pad=0.02)
    cbar.set_label("Indirect effect on score (rubric points)", fontsize=10)

    fig.suptitle(
        "Belief vs style channel by rubric dimension × condition (pooled, N=480/cell)\n"
        "Bold border = 95% bootstrap CI excludes 0",
        fontsize=13, y=1.06)

    out = os.path.join(REPO, "results/figures/subscale_horse_race.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fig.savefig(out, dpi=160, bbox_inches="tight")
    print(f"Wrote {out}")
    print(f"vlim used: ±{vlim}")
    print(f"Belief grid (rows=dims, cols=conds):\n{belief}")
    print(f"Style grid:\n{style}")


if __name__ == "__main__":
    main()
