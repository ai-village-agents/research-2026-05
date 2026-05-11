"""Forest-plot of per-rubric-dimension self-preference effects.

Mirrors `analysis/subscale_analysis.py` — for each of the five 1-10 rubric
dimensions, plots the C1 horse-race coefficients (β with 95% CI HC0 SEs)
for `author_is_self` and `predicted_self`. Saves to
`analysis/plots/subscale_horse_race.png`.

Run:
    python3 analysis/plot_subscale.py
"""

from __future__ import annotations

import glob
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUBRIC = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
PRETTY = {
    "correctness": "Correctness",
    "completeness": "Completeness",
    "clarity": "Clarity",
    "creativity": "Creativity",
    "constraint_adherence": "Constraint Adherence",
}


def load() -> pd.DataFrame:
    sp = sorted(glob.glob(str(ROOT / "data" / "judgments" / "*" / "long_scores.csv")))
    rp = sorted(glob.glob(str(ROOT / "data" / "judgments" / "*" / "long_recognition.csv")))
    s = pd.concat([pd.read_csv(p) for p in sp], ignore_index=True)
    r = pd.concat([pd.read_csv(p) for p in rp], ignore_index=True).rename(
        columns={"true_author": "author"})
    s["condition"] = s["condition"].str.lower()
    s["author_is_self"] = (s["judge"] == s["author"]).astype(int)
    r["predicted_self"] = (r["predicted_author"] == r["judge"]).astype(int)
    df = s.merge(r[["judge", "author", "prompt_id", "predicted_self"]],
                 on=["judge", "author", "prompt_id"], how="left")
    return df.dropna(subset=["predicted_self"])


def ols(df, regs, fe, dep):
    cols = ["Intercept"]
    X = [np.ones((len(df), 1))]
    for r in regs:
        X.append(df[r].to_numpy()[:, None].astype(float))
        cols.append(r)
    for f in fe:
        d = pd.get_dummies(df[f], prefix=f, drop_first=True, dtype=float).to_numpy()
        X.append(d)
        cols.extend([f"{f}_{i}" for i in range(d.shape[1])])
    X = np.hstack(X)
    y = df[dep].to_numpy().astype(float)
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    resid = y - X @ beta
    Omega = X.T @ (X * (resid ** 2)[:, None])
    cov = XtX_inv @ Omega @ XtX_inv
    se = np.sqrt(np.diag(cov))
    return cols, beta, se


def get_coef(cols, beta, se, name):
    i = cols.index(name)
    return float(beta[i]), float(se[i])


def main():
    df = load()
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.6), sharey=True)
    for ax, cond in zip(axes, ["c1", "c2", "c3"]):
        sub = df[df["condition"] == cond]
        ys = np.arange(len(RUBRIC))[::-1]
        for i, dim in enumerate(RUBRIC):
            cols, b, s = ols(sub, ["author_is_self", "predicted_self"],
                              ["author", "judge", "category"], dim)
            ba, sa = get_coef(cols, b, s, "author_is_self")
            bp, sp = get_coef(cols, b, s, "predicted_self")
            y = ys[i]
            ax.errorbar(ba, y - 0.18, xerr=1.96 * sa, fmt="o",
                         color="#1f77b4", capsize=3, label="author_is_self" if i == 0 else None)
            ax.errorbar(bp, y + 0.18, xerr=1.96 * sp, fmt="s",
                         color="#d62728", capsize=3, label="predicted_self" if i == 0 else None)
        ax.axvline(0, color="grey", linewidth=0.8)
        ax.set_yticks(ys)
        ax.set_yticklabels([PRETTY[d] for d in RUBRIC])
        ax.set_xlabel("β (1–10 points)")
        ax.set_title({"c1": "C1 — Baseline blind",
                       "c2": "C2 — Style-neutralized",
                       "c3": "C3 — Bias-warned"}[cond])
        ax.set_xlim(-1.0, 1.6)
        ax.grid(axis="x", linewidth=0.3, alpha=0.6)
    axes[0].legend(loc="lower right", fontsize=9, frameon=True)
    fig.suptitle("Per-rubric-dimension self-preference: belief vs raw authorship",
                  fontsize=13, y=1.02)
    plt.tight_layout()
    out = ROOT / "analysis" / "plots" / "subscale_horse_race.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
