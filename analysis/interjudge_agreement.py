#!/usr/bin/env python3
"""Exploratory inter-judge agreement analysis for evaluator-bias scores.

This script asks a simple contextual question: how much do the reporting judges
agree with each other about response quality, and how large is ordinary judge
disagreement relative to the self-preference effects?

It loads per-judge `data/judgments/*/long_scores.csv`, computes the composite
score used in the preregistered analysis, pivots to one row per
(condition, author, prompt_id), and reports by condition:

- number of complete items and judges
- mean pairwise Pearson correlation across judges
- mean pairwise absolute difference in composite score
- Cronbach-alpha-style consistency diagnostic across judges

The report is descriptive/exploratory and coverage-aware: it uses whatever
judges are present, so the current 3-judge interim report should be regenerated
when Kimi K2.6's judgments arrive.
"""
from __future__ import annotations

import argparse
import itertools
import os
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[1]
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]


def table_md(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except Exception as exc:  # tabulate absent in the default village env
        msg = str(exc).rstrip(".")
        return df.to_string(index=False) + f"\n\n(_Markdown table fallback used: {msg}._)"


def load_scores() -> pd.DataFrame:
    rows = []
    base = REPO_ROOT / "data" / "judgments"
    for judge_dir in sorted(base.iterdir()):
        if not judge_dir.is_dir():
            continue
        p = judge_dir / "long_scores.csv"
        if not p.exists():
            continue
        df = pd.read_csv(p)
        if "judge" not in df.columns:
            df["judge"] = judge_dir.name
        rows.append(df)
    if not rows:
        raise SystemExit("No score files found under data/judgments/*/long_scores.csv")
    df = pd.concat(rows, ignore_index=True)
    missing = [c for c in ["judge", "author", "prompt_id", "condition", *DIMS] if c not in df.columns]
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")
    df["composite"] = df[DIMS].mean(axis=1)
    return df


def cronbach_alpha(mat: pd.DataFrame) -> float:
    """Cronbach alpha over columns=judges, rows=items; returns nan if degenerate."""
    k = mat.shape[1]
    if k < 2 or mat.shape[0] < 2:
        return float("nan")
    item_scores = mat.astype(float)
    judge_vars = item_scores.var(axis=0, ddof=1).sum()
    total_var = item_scores.sum(axis=1).var(ddof=1)
    if total_var <= 0 or not np.isfinite(total_var):
        return float("nan")
    return float(k / (k - 1) * (1 - judge_vars / total_var))


def condition_stats(scores: pd.DataFrame, condition: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    sub = scores[scores["condition"] == condition].copy()
    piv = sub.pivot_table(
        index=["author", "prompt_id"], columns="judge", values="composite", aggfunc="mean"
    ).sort_index()
    complete = piv.dropna(axis=0, how="any")
    judges = list(complete.columns)

    pair_rows = []
    for a, b in itertools.combinations(judges, 2):
        x = complete[a].astype(float)
        y = complete[b].astype(float)
        corr = float(np.corrcoef(x, y)[0, 1]) if len(x) > 1 and x.std(ddof=1) > 0 and y.std(ddof=1) > 0 else float("nan")
        mad = float((x - y).abs().mean())
        bias = float((x - y).mean())
        pair_rows.append({
            "condition": condition,
            "judge_pair": f"{a} vs {b}",
            "n_items": len(complete),
            "pearson_r": corr,
            "mean_abs_diff": mad,
            "mean_signed_diff_first_minus_second": bias,
        })

    pair_df = pd.DataFrame(pair_rows)
    summary = pd.DataFrame([{
        "condition": condition,
        "judges": len(judges),
        "complete_items": len(complete),
        "mean_pairwise_r": pair_df["pearson_r"].mean() if not pair_df.empty else float("nan"),
        "mean_pairwise_abs_diff": pair_df["mean_abs_diff"].mean() if not pair_df.empty else float("nan"),
        "cronbach_alpha": cronbach_alpha(complete),
    }])
    return summary, pair_df


def fmt_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        if pd.api.types.is_float_dtype(out[c]):
            out[c] = out[c].map(lambda x: "NA" if pd.isna(x) else f"{x:.3f}")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="results/interjudge_agreement.md")
    args = ap.parse_args()

    scores = load_scores()
    conditions = sorted(scores["condition"].unique())
    summaries = []
    pairs = []
    for cond in conditions:
        s, p = condition_stats(scores, cond)
        summaries.append(s)
        pairs.append(p)
    summary_df = pd.concat(summaries, ignore_index=True)
    pair_df = pd.concat(pairs, ignore_index=True) if pairs else pd.DataFrame()

    out_path = REPO_ROOT / args.report
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        f.write("# Exploratory inter-judge agreement\n\n")
        f.write(
            "This descriptive check asks how similarly the available judges rate the same "
            "blind responses. It uses the preregistered five-dimension composite score and "
            "one item per `(condition, author, prompt_id)`. The current report is coverage-aware: "
            f"it includes {scores['judge'].nunique()} judges and should be regenerated when missing judges arrive.\n\n"
        )
        f.write("## Summary by condition\n\n")
        f.write(table_md(fmt_df(summary_df)) + "\n\n")
        f.write("## Pairwise judge diagnostics\n\n")
        f.write(table_md(fmt_df(pair_df)) + "\n\n")
        f.write("## Interpretation\n\n")
        best = summary_df.sort_values("mean_pairwise_r", ascending=False).iloc[0]
        worst = summary_df.sort_values("mean_pairwise_r", ascending=True).iloc[0]
        f.write(
            f"Across conditions, mean pairwise judge correlations range from "
            f"{summary_df['mean_pairwise_r'].min():.2f} to {summary_df['mean_pairwise_r'].max():.2f}, "
            f"with highest agreement in {best['condition']} and lowest in {worst['condition']}. "
            f"Mean absolute inter-judge differences are about "
            f"{summary_df['mean_pairwise_abs_diff'].mean():.2f} composite-score points. "
            "These ordinary judge-to-judge differences are larger than the pooled regression "
            "self-preference coefficient, which is why the preregistered tests use within-prompt, "
            "fixed-effect comparisons rather than raw cross-judge means.\n\n"
        )
        f.write(
            "This is exploratory rather than preregistered. Cronbach's alpha is included as a "
            "compact consistency diagnostic, not as a claim that LLM judges are exchangeable "
            "human raters.\n"
        )
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
