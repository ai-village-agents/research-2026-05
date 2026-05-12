"""Plot per-judge confusion matrices for C4 self-recognition.

Reads data/judgments/*/long_recognition.csv and produces
analysis/plots/c4_confusion_matrices.png — a 2x2 (or 1xN) grid of heatmaps,
one per judge, with rows = true_author, cols = predicted_author.

Run from repo root:
    python3 analysis/plot_confusion_matrices.py
"""

from __future__ import annotations

import glob
import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "analysis" / "plots"
OUT_DIR.mkdir(parents=True, exist_ok=True)

AUTHORS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
SHORT = {
    "claude-opus-4.7": "Claude\nO4.7",
    "gemini-3.1-pro": "Gemini\n3.1P",
    "gpt-5.5": "GPT-5.5",
    "kimi-k2.6": "Kimi\nK2.6",
}


def load_recognition() -> pd.DataFrame:
    paths = sorted(glob.glob(str(ROOT / "data" / "judgments" / "*" / "long_recognition.csv")))
    frames = []
    for p in paths:
        df = pd.read_csv(p)
        frames.append(df)
    if not frames:
        raise SystemExit("No recognition CSVs found under data/judgments/*/.")
    return pd.concat(frames, ignore_index=True)


def confusion_matrix(df_judge: pd.DataFrame) -> np.ndarray:
    M = np.zeros((len(AUTHORS), len(AUTHORS)), dtype=int)
    for _, r in df_judge.iterrows():
        try:
            i = AUTHORS.index(r["true_author"])
            j = AUTHORS.index(r["predicted_author"])
        except ValueError:
            continue
        M[i, j] += 1
    return M


def plot_grid(df: pd.DataFrame) -> Path:
    judges = sorted(df["judge"].unique())
    n = len(judges)
    cols = 2 if n >= 2 else 1
    rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(5.6 * cols, 4.8 * rows), squeeze=False)
    for ax in axes.ravel()[len(judges):]:
        ax.axis("off")
    short_labels = [SHORT[a] for a in AUTHORS]
    for idx, judge in enumerate(judges):
        ax = axes[idx // cols][idx % cols]
        sub = df[df["judge"] == judge]
        M = confusion_matrix(sub)
        # Row-normalize (each true author has 30 items) so heatmap is "% predicted as X"
        row_sums = M.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1
        pct = M / row_sums
        im = ax.imshow(pct, cmap="Blues", vmin=0, vmax=1, aspect="equal")
        ax.set_xticks(range(len(AUTHORS)))
        ax.set_yticks(range(len(AUTHORS)))
        ax.set_xticklabels(short_labels, fontsize=9)
        ax.set_yticklabels(short_labels, fontsize=9)
        ax.set_xlabel("predicted author", fontsize=10)
        ax.set_ylabel("true author", fontsize=10)
        # Highlight diagonal (correct) with a thicker border
        for k in range(len(AUTHORS)):
            ax.add_patch(plt.Rectangle((k - 0.5, k - 0.5), 1, 1, fill=False,
                                        edgecolor="black", lw=1.6))
        # Annotate counts (raw N out of 30)
        for i in range(len(AUTHORS)):
            for j in range(len(AUTHORS)):
                cnt = M[i, j]
                if cnt == 0:
                    text = ""
                else:
                    text = str(cnt)
                color = "white" if pct[i, j] > 0.55 else "black"
                ax.text(j, i, text, ha="center", va="center", color=color, fontsize=10)
        # Show self-recognition accuracy in title
        try:
            self_idx = AUTHORS.index(judge)
            self_n = M[self_idx, self_idx]
            self_total = M[self_idx].sum()
            acc = self_n / self_total if self_total else float("nan")
            ax.set_title(f"Judge: {judge}  (self-recognition {self_n}/{self_total} = {acc:.0%})",
                         fontsize=10)
        except ValueError:
            ax.set_title(f"Judge: {judge}", fontsize=10)
    fig.suptitle("C4 confusion matrices: who does each judge think wrote what?\n"
                 "(row-normalized; cell text = raw count out of 30; diagonal = correct)",
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = OUT_DIR / "c4_confusion_matrices.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def plot_per_judge_prediction_bias(df: pd.DataFrame) -> Path:
    """How often does each judge predict each author, as a fraction of all 120?"""
    judges = sorted(df["judge"].unique())
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    x = np.arange(len(judges))
    width = 0.18
    colors = {"claude-opus-4.7": "#c46a4f",
              "gemini-3.1-pro": "#4f7bd6",
              "gpt-5.5": "#3da06b",
              "kimi-k2.6": "#a163d6"}
    for k, author in enumerate(AUTHORS):
        heights = []
        for j in judges:
            sub = df[df["judge"] == j]
            pred_count = (sub["predicted_author"] == author).sum()
            heights.append(pred_count / max(len(sub), 1))
        bars = ax.bar(x + (k - 1.5) * width, heights, width=width,
                      label=author, color=colors[author])
        # If the author == judge, mark with hatching
        for j_idx, j in enumerate(judges):
            if j == author:
                bars[j_idx].set_hatch("//")
                bars[j_idx].set_edgecolor("black")
    ax.axhline(0.25, color="grey", linestyle="--", linewidth=1, label="uniform (25%)")
    ax.set_xticks(x)
    ax.set_xticklabels(judges, rotation=0, fontsize=9)
    ax.set_ylabel("share of 120 predictions")
    ax.set_title("Per-judge prediction-share by candidate author\n"
                 "(hatched bar = the judge predicting itself; dashed line = uniform 25%)")
    ax.set_ylim(0, 1.0)
    ax.legend(fontsize=8, loc="upper right", ncol=2)
    fig.tight_layout()
    out = OUT_DIR / "c4_per_judge_prediction_bias.png"
    fig.savefig(out, dpi=140)
    plt.close(fig)
    return out


def main() -> None:
    df = load_recognition()
    print(f"Loaded {len(df)} recognition rows from {df['judge'].nunique()} judge(s).")
    print(f"Judges: {sorted(df['judge'].unique())}")
    p1 = plot_grid(df)
    p2 = plot_per_judge_prediction_bias(df)
    print(f"Wrote {p1.relative_to(ROOT)}")
    print(f"Wrote {p2.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
