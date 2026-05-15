#!/usr/bin/env python3
"""Judge calibration and disagreement profile for the replication wave.

This is a post-v1.3.0 exploratory supplement. It does not alter any headline
estimand; it summarizes how judges used the 1--10 composite scale and how far
each judge sat from the contemporaneous cross-judge consensus for the same
(condition, prompt, author) cell.
"""
from __future__ import annotations

from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCORES = RESULTS / "long_scores.csv"
DIMENSIONS = [
    "correctness",
    "completeness",
    "clarity",
    "creativity",
    "constraint_adherence",
]
CELL = ["condition", "prompt_id", "author"]


def _fmt(x: float | int | None, digits: int = 3) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "NA"
    return f"{x:.{digits}f}"




def _spearman_no_scipy(x: pd.Series, y: pd.Series) -> float:
    paired = pd.concat([x, y], axis=1).dropna()
    if len(paired) < 2:
        return float("nan")
    rx = paired.iloc[:, 0].rank(method="average")
    ry = paired.iloc[:, 1].rank(method="average")
    if rx.nunique() < 2 or ry.nunique() < 2:
        return float("nan")
    return float(rx.corr(ry, method="pearson"))

def _rank_order(df: pd.DataFrame, metric: str, ascending: bool = False) -> str:
    ordered = df.sort_values(metric, ascending=ascending)
    return " > ".join(f"{r.judge} ({_fmt(getattr(r, metric))})" for r in ordered.itertuples())


def main() -> None:
    df = pd.read_csv(SCORES)
    df["composite"] = df[DIMENSIONS].mean(axis=1)

    cell_mean = df.groupby(CELL)["composite"].transform("mean")
    peer_sum = df.groupby(CELL)["composite"].transform("sum")
    peer_n = df.groupby(CELL)["composite"].transform("count") - 1
    df["cell_consensus"] = cell_mean
    df["peer_consensus"] = (peer_sum - df["composite"]) / peer_n
    df["signed_vs_cell_consensus"] = df["composite"] - df["cell_consensus"]
    df["signed_vs_peer_consensus"] = df["composite"] - df["peer_consensus"]
    df["abs_vs_peer_consensus"] = df["signed_vs_peer_consensus"].abs()

    judge_rows = []
    for judge, g in df.groupby("judge", sort=True):
        judge_rows.append({
            "judge": judge,
            "n_scores": len(g),
            "mean_composite": g["composite"].mean(),
            "sd_composite": g["composite"].std(ddof=1),
            "min_composite": g["composite"].min(),
            "max_composite": g["composite"].max(),
            "mean_signed_vs_peer_consensus": g["signed_vs_peer_consensus"].mean(),
            "mean_abs_vs_peer_consensus": g["abs_vs_peer_consensus"].mean(),
            "median_abs_vs_peer_consensus": g["abs_vs_peer_consensus"].median(),
            "pct_within_0_5_of_peer_consensus": (g["abs_vs_peer_consensus"] <= 0.5).mean(),
            "pct_within_1_0_of_peer_consensus": (g["abs_vs_peer_consensus"] <= 1.0).mean(),
        })
    judge_summary = pd.DataFrame(judge_rows)

    condition_summary = (
        df.groupby(["condition", "judge"])
        .agg(
            n_scores=("composite", "size"),
            mean_composite=("composite", "mean"),
            sd_composite=("composite", "std"),
            mean_signed_vs_peer_consensus=("signed_vs_peer_consensus", "mean"),
            mean_abs_vs_peer_consensus=("abs_vs_peer_consensus", "mean"),
        )
        .reset_index()
    )

    author_summary = (
        df.groupby(["author", "judge"])
        .agg(
            n_scores=("composite", "size"),
            mean_composite=("composite", "mean"),
            mean_signed_vs_peer_consensus=("signed_vs_peer_consensus", "mean"),
            mean_abs_vs_peer_consensus=("abs_vs_peer_consensus", "mean"),
        )
        .reset_index()
    )

    # Pairwise disagreement is computed on matched condition/prompt/author cells.
    pair_rows = []
    wide = df.pivot_table(index=CELL, columns="judge", values="composite", aggfunc="first")
    judges = sorted(df["judge"].unique())
    for a, b in combinations(judges, 2):
        x = wide[a]
        y = wide[b]
        d = x - y
        pair_rows.append({
            "judge_a": a,
            "judge_b": b,
            "n_cells": int(d.notna().sum()),
            "mean_signed_a_minus_b": d.mean(),
            "mean_abs_difference": d.abs().mean(),
            "median_abs_difference": d.abs().median(),
            "spearman_rho": _spearman_no_scipy(x, y),
            "pearson_r": x.corr(y, method="pearson"),
        })
    pairwise = pd.DataFrame(pair_rows)

    # Which cells create the biggest absolute disagreement from peer consensus?
    outlier_cols = [
        "condition", "prompt_id", "category", "author", "judge", "composite",
        "peer_consensus", "signed_vs_peer_consensus", "abs_vs_peer_consensus",
    ]
    outliers = df.sort_values("abs_vs_peer_consensus", ascending=False)[outlier_cols].head(20)

    judge_summary.to_csv(RESULTS / "judge_calibration_profile.csv", index=False)
    condition_summary.to_csv(RESULTS / "judge_calibration_by_condition.csv", index=False)
    author_summary.to_csv(RESULTS / "judge_calibration_by_author.csv", index=False)
    pairwise.to_csv(RESULTS / "judge_pairwise_disagreement.csv", index=False)
    outliers.to_csv(RESULTS / "judge_calibration_outliers.csv", index=False)

    md = []
    md.append("# Judge calibration and disagreement profile (post-v1.3.0 exploratory supplement)\n")
    md.append("This supplement does **not** change the headline v1.3.0 results. It describes how each judge used the composite 1–10 scale in the completed replication wave, and how far each judge's score sat from the peer consensus for the same `(condition, prompt, author)` response cell.\n")
    md.append("Definitions:\n")
    md.append("- `composite` = mean of correctness, completeness, clarity, creativity, and constraint adherence.\n")
    md.append("- `peer_consensus` = mean composite from the other three judges on the same condition/prompt/author cell.\n")
    md.append("- `signed_vs_peer_consensus` = judge composite minus peer consensus; positive means more lenient than peers on matched cells.\n")
    md.append("- `abs_vs_peer_consensus` = absolute distance from peer consensus; lower means closer calibration to peers.\n\n")

    md.append("## Overall judge profiles\n\n")
    md.append("| Judge | n | Mean composite | SD | Mean signed vs peers | Mean abs vs peers | Median abs vs peers | % within 0.5 | % within 1.0 |\n")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|\n")
    for r in judge_summary.sort_values("judge").itertuples():
        md.append(
            f"| {r.judge} | {r.n_scores} | {_fmt(r.mean_composite)} | {_fmt(r.sd_composite)} | "
            f"{_fmt(r.mean_signed_vs_peer_consensus)} | {_fmt(r.mean_abs_vs_peer_consensus)} | "
            f"{_fmt(r.median_abs_vs_peer_consensus)} | {_fmt(100*r.pct_within_0_5_of_peer_consensus,1)}% | "
            f"{_fmt(100*r.pct_within_1_0_of_peer_consensus,1)}% |\n"
        )
    md.append("\n")
    md.append("Scale-use rank, highest to lowest mean composite: " + _rank_order(judge_summary, "mean_composite") + ".\n\n")
    md.append("Peer-calibration rank, closest to farthest by mean absolute peer deviation: " + _rank_order(judge_summary, "mean_abs_vs_peer_consensus", ascending=True) + ".\n\n")

    md.append("## By condition\n\n")
    md.append("| Condition | Judge | Mean composite | SD | Mean signed vs peers | Mean abs vs peers |\n")
    md.append("|---|---|---:|---:|---:|---:|\n")
    for r in condition_summary.sort_values(["condition", "judge"]).itertuples():
        md.append(f"| {r.condition.upper()} | {r.judge} | {_fmt(r.mean_composite)} | {_fmt(r.sd_composite)} | {_fmt(r.mean_signed_vs_peer_consensus)} | {_fmt(r.mean_abs_vs_peer_consensus)} |\n")
    md.append("\n")

    md.append("## Pairwise matched-cell disagreement\n\n")
    md.append("| Judge A | Judge B | n cells | Mean A−B | Mean absolute difference | Median absolute difference | Spearman ρ | Pearson r |\n")
    md.append("|---|---|---:|---:|---:|---:|---:|---:|\n")
    for r in pairwise.sort_values("mean_abs_difference").itertuples():
        md.append(f"| {r.judge_a} | {r.judge_b} | {r.n_cells} | {_fmt(r.mean_signed_a_minus_b)} | {_fmt(r.mean_abs_difference)} | {_fmt(r.median_abs_difference)} | {_fmt(r.spearman_rho)} | {_fmt(r.pearson_r)} |\n")
    md.append("\n")

    md.append("## Largest individual deviations from peer consensus\n\n")
    md.append("These rows are useful for diagnosing where disagreement concentrates; they are not evidence of error by themselves.\n\n")
    md.append("| Condition | Prompt | Author | Judge | Composite | Peer consensus | Signed gap | Abs gap |\n")
    md.append("|---|---|---|---|---:|---:|---:|---:|\n")
    for r in outliers.itertuples():
        md.append(f"| {r.condition.upper()} | {r.prompt_id} | {r.author} | {r.judge} | {_fmt(r.composite)} | {_fmt(r.peer_consensus)} | {_fmt(r.signed_vs_peer_consensus)} | {_fmt(r.abs_vs_peer_consensus)} |\n")
    md.append("\n")

    md.append("## Interpretation\n\n")
    closest = judge_summary.sort_values("mean_abs_vs_peer_consensus").iloc[0]
    farthest = judge_summary.sort_values("mean_abs_vs_peer_consensus").iloc[-1]
    lenient = judge_summary.sort_values("mean_signed_vs_peer_consensus").iloc[-1]
    harsh = judge_summary.sort_values("mean_signed_vs_peer_consensus").iloc[0]
    md.append(f"- The closest judge to peer consensus is **{closest.judge}** (mean absolute peer deviation {_fmt(closest.mean_abs_vs_peer_consensus)}); the farthest is **{farthest.judge}** ({_fmt(farthest.mean_abs_vs_peer_consensus)}).\n")
    md.append(f"- The most lenient matched-cell calibration is **{lenient.judge}** (signed vs peers {_fmt(lenient.mean_signed_vs_peer_consensus)}); the harshest is **{harsh.judge}** ({_fmt(harsh.mean_signed_vs_peer_consensus)}).\n")
    md.append("- These calibration profiles complement, but do not replace, the self-preference and label-swap estimands. A judge can be globally lenient or harsh while still showing little causal sensitivity to displayed self-labels.\n")

    (RESULTS / "judge_calibration_profile.md").write_text("".join(md))
    print("wrote judge calibration supplement")


if __name__ == "__main__":
    main()
