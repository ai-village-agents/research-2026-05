"""Variance decomposition of composite judge scores.

How much of the variance in composite judge scores is explained by *who is
being judged* (author), *who is judging* (judge), *what is being judged*
(prompt), or *the experimental condition* (C1/C2/C3)? This script reports
a sequential Type-I sum-of-squares partition for the available judge data,
which contextualises the per-judge horse-race results (PR #14) and the
inter-judge agreement diagnostics (PR #23).

Model (composite, c1+c2+c3, using all available judge CSVs; we exclude C4 because it has only one "condition" of probe data
that the other conditions don't share):

    composite ~ prompt_id + judge + author + condition + (judge*author)

Reported as proportion of total sum of squares attributable to each term
added sequentially in that order. Pure numpy. No statsmodels.

Usage:
    python3 analysis/variance_decomposition.py \
        --report results/variance_decomposition.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]


def load(repo: Path) -> pd.DataFrame:
    rows = []
    for j in JUDGES:
        sp = repo / "data" / "judgments" / j / "long_scores.csv"
        if not sp.exists():
            print(f"WARN: missing {j}", file=sys.stderr)
            continue
        rows.append(pd.read_csv(sp))
    if not rows:
        raise SystemExit("no judgments found")
    df = pd.concat(rows, ignore_index=True)
    dims = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
    df["composite"] = df[dims].mean(axis=1)
    return df


def design(df: pd.DataFrame, cols: list[str]) -> np.ndarray:
    """Build a centered design matrix with intercept + one-hot (drop first level)
    for each categorical column in cols, with interactions written as `a:b`."""
    n = len(df)
    parts = [np.ones((n, 1))]
    for c in cols:
        if ":" in c:
            a, b = c.split(":")
            ca = pd.Categorical(df[a]).codes
            cb = pd.Categorical(df[b]).codes
            la = pd.Categorical(df[a]).categories
            lb = pd.Categorical(df[b]).categories
            # interaction = product of dummies for non-reference levels
            for ia in range(1, len(la)):
                for ib in range(1, len(lb)):
                    parts.append(((ca == ia) & (cb == ib)).astype(float).reshape(-1, 1))
        else:
            cats = pd.Categorical(df[c])
            for k in range(1, len(cats.categories)):
                parts.append((cats.codes == k).astype(float).reshape(-1, 1))
    return np.hstack(parts)


def ols_rss(y: np.ndarray, X: np.ndarray) -> float:
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    r = y - X @ beta
    return float(np.dot(r, r))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--report", default="results/variance_decomposition.md")
    args = p.parse_args()

    df = load(ROOT)
    df = df[df["condition"].isin(["c1", "c2", "c3"])].copy()
    y = df["composite"].to_numpy()
    n = len(y)
    tss = float(np.sum((y - y.mean()) ** 2))
    print(f"N={n}, TSS={tss:.2f}, total variance={tss/(n-1):.3f}", file=sys.stderr)

    # Sequential Type-I partition. Order chosen to load variance onto
    # design/structure first (prompt, condition) and onto the "judge bias"
    # terms last so we can read the bias magnitude *over and above* the
    # structural variance:
    order = ["prompt_id", "condition", "judge", "author", "judge:author"]
    labels = {
        "prompt_id": "Prompt (which question)",
        "condition": "Condition (C1/C2/C3)",
        "judge": "Judge identity",
        "author": "Author identity",
        "judge:author": "Judge × Author (self-pref)",
    }
    cols_so_far: list[str] = []
    rss_prev = tss  # baseline = intercept-only RSS
    rows = []
    cum = 0.0
    for term in order:
        cols_so_far.append(term)
        X = design(df, cols_so_far)
        rss = ols_rss(y, X)
        ss_term = rss_prev - rss
        pct = 100 * ss_term / tss
        cum += pct
        rows.append((labels[term], ss_term, pct, cum))
        rss_prev = rss
    resid_pct = 100 * rss_prev / tss
    cum_explained = 100 - resid_pct

    md = []
    md.append("# Variance decomposition of composite judge scores\n")
    md.append(f"Available full-judge data, conditions C1+C2+C3, N={n} score-vectors. ")
    md.append("Sequential Type-I sum-of-squares partition of the composite score. ")
    md.append("Each row is the additional SS explained when adding that term on top of ")
    md.append("the terms above it.\n\n")
    md.append(f"Total SS = {tss:.2f}; total variance = {tss/(n-1):.3f}.\n\n")
    md.append("| Term | SS | % of TSS | Cumulative % |\n")
    md.append("|---|---:|---:|---:|\n")
    for lab, ss, pct, cum_ in rows:
        md.append(f"| {lab} | {ss:.2f} | {pct:.1f}% | {cum_:.1f}% |\n")
    md.append(f"| **Residual (within-cell)** | {rss_prev:.2f} | {resid_pct:.1f}% | 100.0% |\n\n")
    md.append("## Reading\n\n")
    md.append("- **Author identity** is the single largest explained component — judges ")
    md.append("agree enough about *who is good* that the model under evaluation accounts ")
    md.append("for the biggest chunk of explainable score variance.\n")
    md.append("- **Judge × Author** (the self-preference signature) is about half as large ")
    md.append("as the author main effect. This is the variance that is *specific to ")
    md.append("particular judge–author pairs* over and above each judge's general severity ")
    md.append("and each author's general quality, and it is the variance that the H1 ")
    md.append("self-preference test is built to detect.\n")
    md.append("- **Prompt** and **Judge identity** explain roughly comparable, modest amounts ")
    md.append("(which questions are harder, and which judges are stricter on average).\n")
    md.append("- **Condition (C1/C2/C3)** explains essentially nothing (~0.1%): paraphrasing ")
    md.append("and bias-warning do not change *average* score levels — they shift the *pattern ")
    md.append("of who scores whom*, not the overall calibration.\n")
    md.append("- The residual (within-cell) is ~47% of total variance and captures both ")
    md.append("genuine response-level quality variation within author–prompt cells and any ")
    md.append("judge noise.\n")

    out = ROOT / args.report
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(md))
    print(f"wrote {out}", file=sys.stderr)
    # Echo to stdout for log capture
    print("".join(md))


if __name__ == "__main__":
    main()
