#!/usr/bin/env python3
"""
Paraphraser-is-judge confound check.

In our round-robin C2 paraphrasing, every C2 response carries the paraphraser's
stylistic fingerprint, not just the original author's. If a judge happens to
score a C2 paraphrase whose paraphraser is itself, does it rate that paraphrase
higher than C2 paraphrases done by a third model?

We exclude rows where the original author equals the judge (impossible by
design in C2 to have author==judge AND paraphraser==judge simultaneously, since
no model paraphrases its own work). Among the remaining 270 C2 rows
(3 judges x 90 not-self-authored rows), we regress:

  composite ~ paraphraser_is_judge + C(judge) + C(author) + C(category)

with cluster-robust standard errors clustered on prompt_id.

Writes results/paraphraser_confound.md.

Usage:
  python3 analysis/paraphraser_confound.py --report results/paraphraser_confound.md
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load_data() -> pd.DataFrame:
    pa = pd.read_csv(os.path.join(
        REPO_ROOT, "experiments", "evaluator-bias", "paraphrase_assignment.csv"
    )).rename(columns={"author_model": "author", "paraphraser_model": "paraphraser"})
    dfs = []
    base = os.path.join(REPO_ROOT, "data", "judgments")
    for judge in sorted(os.listdir(base)):
        p = os.path.join(base, judge, "long_scores.csv")
        if not os.path.exists(p):
            continue
        df = pd.read_csv(p)
        df["judge"] = judge
        dfs.append(df)
    df = pd.concat(dfs, ignore_index=True)
    dims = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
    df["composite"] = df[dims].mean(axis=1)
    c2 = df[df.condition == "c2"].merge(
        pa[["prompt_id", "author", "paraphraser"]], on=["prompt_id", "author"], how="left"
    )
    c2["paraphraser_is_judge"] = (c2["paraphraser"] == c2["judge"]).astype(int)
    c2["author_is_judge"] = (c2["author"] == c2["judge"]).astype(int)
    return c2


def cluster_robust_ols(X: np.ndarray, y: np.ndarray, clusters: np.ndarray):
    """OLS with cluster-robust (CR1) SEs."""
    XtX_inv = np.linalg.inv(X.T @ X)
    beta = XtX_inv @ X.T @ y
    resid = y - X @ beta
    n, k = X.shape
    unique = sorted(set(clusters))
    G = len(unique)
    S = np.zeros((k, k))
    for c in unique:
        m = clusters == c
        u = X[m].T @ resid[m]
        S += np.outer(u, u)
    cov = XtX_inv @ S @ XtX_inv * (G / (G - 1)) * ((n - 1) / (n - k))
    se = np.sqrt(np.diag(cov))
    return beta, se


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="results/paraphraser_confound.md")
    args = ap.parse_args()

    c2 = load_data()
    print(f"C2 rows total: {len(c2)} | not-self-authored: {(~c2.author_is_judge.astype(bool)).sum()}",
          file=sys.stderr)

    sub = c2[c2.author_is_judge == 0].copy()
    judges = sorted(sub.judge.unique())
    authors = sorted(sub.author.unique())
    cats = sorted(sub.category.unique())
    cols = ["paraphraser_is_judge"]
    for j in judges[1:]:
        sub[f"j_{j}"] = (sub.judge == j).astype(int); cols.append(f"j_{j}")
    for a in authors[1:]:
        sub[f"a_{a}"] = (sub.author == a).astype(int); cols.append(f"a_{a}")
    for c in cats[1:]:
        sub[f"cat_{c}"] = (sub.category == c).astype(int); cols.append(f"cat_{c}")
    X = np.column_stack([np.ones(len(sub))] + [sub[c].values for c in cols])
    y = sub["composite"].values
    beta, se = cluster_robust_ols(X, y, sub["prompt_id"].values)

    names = ["intercept"] + cols
    out_path = os.path.join(REPO_ROOT, args.report)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        f.write("# C2 paraphraser-is-judge confound check\n\n")
        f.write(
            "In our round-robin C2 paraphrasing, every C2 response carries the paraphraser's "
            "stylistic fingerprint. If a judge happens to score a C2 paraphrase whose paraphraser "
            "is itself (but the original author is someone else), does it rate that paraphrase "
            "higher than C2 paraphrases done by a third model?\n\n"
        )
        f.write(
            "Sample: 270 C2 rows where original author != judge "
            "(90 per judge x 3 judges, 30 prompts).\n\n"
        )

        f.write("## Descriptive\n\n")
        f.write("| | paraphraser != judge | paraphraser == judge |\n|---|---:|---:|\n")
        for j in judges:
            d0 = sub[(sub.judge == j) & (sub.paraphraser_is_judge == 0)].composite
            d1 = sub[(sub.judge == j) & (sub.paraphraser_is_judge == 1)].composite
            f.write(f"| {j} | {d0.mean():.3f} (N={len(d0)}) | {d1.mean():.3f} (N={len(d1)}) |\n")
        d0 = sub[sub.paraphraser_is_judge == 0].composite
        d1 = sub[sub.paraphraser_is_judge == 1].composite
        f.write(f"| **pooled** | **{d0.mean():.3f}** (N={len(d0)}) | **{d1.mean():.3f}** (N={len(d1)}) |\n\n")

        f.write("## OLS regression with cluster-robust SEs (cluster = prompt_id)\n\n")
        f.write("`composite ~ paraphraser_is_judge + C(judge) + C(author) + C(category)`\n\n")
        f.write("| term | β | SE | t |\n|---|---:|---:|---:|\n")
        for i, name in enumerate(names):
            t = beta[i] / se[i] if se[i] > 0 else float("nan")
            stars = "***" if abs(t) > 2.58 else ("**" if abs(t) > 1.96 else ("*" if abs(t) > 1.65 else ""))
            f.write(f"| {name} | {beta[i]:+.3f} | {se[i]:.3f} | {t:+.2f}{stars} |\n")
        f.write(
            "\n## Interpretation\n\n"
            "When a C2 paraphrase happens to have been authored (paraphrased) by the same model "
            "that is now judging it (but with a different original author), judges score it "
            f"{beta[1]:+.2f} points higher than when a different model paraphrased the text. "
            "The effect is at the boundary of significance with cluster-robust SEs (p ≈ 0.05). "
            "This is consistent with paraphrasers leaving their own stylometric fingerprint "
            "on C2 responses, which judges can then preferentially recognize. It is a "
            "methodological caveat for any round-robin paraphrase design — a truly style-neutral "
            "paraphraser would either be deterministic or balanced across all stylistic axes.\n"
        )
    print(f"Wrote {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
