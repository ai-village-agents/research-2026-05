#!/usr/bin/env python3
"""Reproduce replication-wave perceived-vs-actual authorship analyses.

The script joins C1 quality scores to C4 authorship predictions, computes the
core 2x2 cell summaries, and fits dependency-light fixed-effect OLS models using
NumPy rather than statsmodels. It is designed to rerun unchanged when Kimi's rows
are ingested.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
MODELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
DEFAULT_ROOT = Path(__file__).resolve().parent


def load_merged(root: Path) -> pd.DataFrame:
    scores = pd.read_csv(root / "results" / "long_scores.csv")
    recog = pd.read_csv(root / "results" / "long_recognition.csv").rename(columns={"true_author": "author"})
    c1 = scores[scores["condition"].str.lower() == "c1"].copy()
    c1["mean5"] = c1[DIMS].mean(axis=1)
    merged = c1.merge(recog, on=["judge", "author", "prompt_id"], how="inner", validate="one_to_one")
    merged["actual_self"] = (merged["judge"] == merged["author"]).astype(int)
    merged["predicted_self"] = (merged["judge"] == merged["predicted_author"]).astype(int)
    return merged


def fit_ols(df: pd.DataFrame, continuous_terms: list[str], categorical_terms: list[str]) -> dict[str, float]:
    parts = [pd.Series(1.0, index=df.index, name="Intercept")]
    parts.extend(df[term].astype(float).rename(term) for term in continuous_terms)
    for term in categorical_terms:
        dummies = pd.get_dummies(df[term], prefix=f"C({term})", drop_first=True, dtype=float)
        parts.append(dummies)
    x = pd.concat(parts, axis=1)
    y = df["mean5"].astype(float).to_numpy()
    beta, *_ = np.linalg.lstsq(x.to_numpy(dtype=float), y, rcond=None)
    return dict(zip(x.columns, beta))


def bootstrap_coefficients(
    df: pd.DataFrame,
    continuous_terms: list[str],
    categorical_terms: list[str],
    keep_terms: list[str],
    b: int,
    seed: int,
) -> pd.DataFrame:
    prompts = sorted(df["prompt_id"].unique())
    rng = np.random.default_rng(seed)
    draws: dict[str, list[float]] = {term: [] for term in keep_terms}
    for _ in range(b):
        sampled = rng.choice(prompts, size=len(prompts), replace=True)
        boot = pd.concat([df[df["prompt_id"] == prompt] for prompt in sampled], ignore_index=True)
        try:
            coefs = fit_ols(boot, continuous_terms, categorical_terms)
        except np.linalg.LinAlgError:
            continue
        for term in keep_terms:
            draws[term].append(float(coefs.get(term, np.nan)))
    rows = []
    for term in keep_terms:
        arr = np.array(draws[term], dtype=float)
        arr = arr[np.isfinite(arr)]
        rows.append(
            {
                "term": term,
                "bootstrap_n": int(len(arr)),
                "boot_ci_low": float(np.percentile(arr, 2.5)) if len(arr) else np.nan,
                "boot_ci_high": float(np.percentile(arr, 97.5)) if len(arr) else np.nan,
            }
        )
    return pd.DataFrame(rows)


def summarize(root: Path, b: int, seed: int) -> dict[str, pd.DataFrame]:
    merged = load_merged(root)

    two_by_two = (
        merged.groupby(["judge", "actual_self", "predicted_self"])["mean5"]
        .agg(mean="mean", n="size", std="std")
        .reset_index()
        .sort_values(["judge", "actual_self", "predicted_self"])
    )

    raw_gap_rows = []
    for judge, group in merged.groupby("judge"):
        actual_gap = group.loc[group["actual_self"] == 1, "mean5"].mean() - group.loc[group["actual_self"] == 0, "mean5"].mean()
        pred_gap = group.loc[group["predicted_self"] == 1, "mean5"].mean() - group.loc[group["predicted_self"] == 0, "mean5"].mean()
        raw_gap_rows.append(
            {
                "judge": judge,
                "n": len(group),
                "actual_self_gap": actual_gap,
                "predicted_self_gap": pred_gap,
                "recognition_accuracy": (group["author"] == group["predicted_author"]).mean(),
                "self_hits": int(((group["judge"] == group["author"]) & (group["judge"] == group["predicted_author"])).sum()),
            }
        )
    raw_gaps = pd.DataFrame(raw_gap_rows).sort_values("judge")

    label_means = (
        merged.groupby("predicted_author")["mean5"]
        .agg(mean="mean", n="size", std="std")
        .reset_index()
        .sort_values("mean", ascending=False)
    )

    main_coefs = fit_ols(merged, ["actual_self", "predicted_self"], ["judge", "prompt_id"])
    main_df = pd.DataFrame(
        [{"term": term, "beta": main_coefs[term]} for term in ["actual_self", "predicted_self"]]
    )
    main_ci = bootstrap_coefficients(
        merged,
        ["actual_self", "predicted_self"],
        ["judge", "prompt_id"],
        ["actual_self", "predicted_self"],
        b,
        seed,
    )
    main_df = main_df.merge(main_ci, on="term")

    # Label-effect model with Kimi as explicit reference for actual and predicted labels.
    label_df = merged.copy()
    for model in MODELS:
        if model == "kimi-k2.6":
            continue
        label_df[f"predicted_author={model}"] = (label_df["predicted_author"] == model).astype(int)
        label_df[f"actual_author={model}"] = (label_df["author"] == model).astype(int)
    label_terms = [f"predicted_author={m}" for m in MODELS if m != "kimi-k2.6"] + [
        f"actual_author={m}" for m in MODELS if m != "kimi-k2.6"
    ]
    label_coefs = fit_ols(label_df, label_terms, ["judge", "prompt_id"])
    label_effects = pd.DataFrame([{"term": term, "beta": label_coefs[term]} for term in label_terms])
    label_ci = bootstrap_coefficients(label_df, label_terms, ["judge", "prompt_id"], label_terms, b, seed + 1)
    label_effects = label_effects.merge(label_ci, on="term")

    return {
        "merged": merged,
        "two_by_two": two_by_two,
        "raw_gaps": raw_gaps,
        "label_means": label_means,
        "main_coefficients": main_df,
        "label_effects": label_effects,
    }


def fmt(x: float) -> str:
    if pd.isna(x):
        return "NA"
    return f"{0.0 if abs(float(x)) < 5e-13 else float(x):+.3f}"


def write_markdown(outputs: dict[str, pd.DataFrame], path: Path, b: int) -> None:
    merged = outputs["merged"]
    main = outputs["main_coefficients"]
    label = outputs["label_effects"]
    raw = outputs["raw_gaps"]
    means = outputs["label_means"]
    two = outputs["two_by_two"]
    judges = ", ".join(sorted(merged["judge"].unique()))
    lines = [
        "# Perceived-vs-actual authorship reproducible summary",
        "",
        "Generated by `experiments/replication-wave/analyze_perceived_self_replication.py`.",
        "",
        f"Data: C1 quality scores joined to C4 recognition rows, N={len(merged)}, judges: {judges}.",
        "",
        "## Fixed-effect OLS: `mean5 ~ actual_self + predicted_self + C(judge) + C(prompt_id)`",
        "",
        f"Prompt bootstrap uses B={b} resamples of prompt clusters.",
        "",
        "| term | beta | boot CI low | boot CI high |",
        "|---|---:|---:|---:|",
    ]
    for _, r in main.iterrows():
        lines.append(f"| {r['term']} | {fmt(r['beta'])} | {fmt(r['boot_ci_low'])} | {fmt(r['boot_ci_high'])} |")
    lines.extend(["", "## Per-judge raw gaps", "", "| judge | n | recognition accuracy | self hits | actual-self gap | predicted-self gap |", "|---|---:|---:|---:|---:|---:|"])
    for _, r in raw.iterrows():
        lines.append(
            f"| {r['judge']} | {int(r['n'])} | {r['recognition_accuracy']:.3f} | {int(r['self_hits'])} | {fmt(r['actual_self_gap'])} | {fmt(r['predicted_self_gap'])} |"
        )
    lines.extend(["", "## Predicted-author label means", "", "| predicted_author | mean5 | n | std |", "|---|---:|---:|---:|"])
    for _, r in means.iterrows():
        lines.append(f"| {r['predicted_author']} | {r['mean']:.3f} | {int(r['n'])} | {r['std']:.3f} |")
    lines.extend(["", "## Label-effect model coefficients", "", "Reference label for actual and predicted authors is `kimi-k2.6`; model also includes judge and prompt fixed effects.", "", "| term | beta | boot CI low | boot CI high |", "|---|---:|---:|---:|"])
    for _, r in label.iterrows():
        lines.append(f"| {r['term']} | {fmt(r['beta'])} | {fmt(r['boot_ci_low'])} | {fmt(r['boot_ci_high'])} |")
    lines.extend(["", "## 2x2 cells", "", "| judge | actual_self | predicted_self | mean5 | n | std |", "|---|---:|---:|---:|---:|---:|"])
    for _, r in two.iterrows():
        std = "NA" if pd.isna(r["std"]) else f"{r['std']:.3f}"
        lines.append(f"| {r['judge']} | {int(r['actual_self'])} | {int(r['predicted_self'])} | {r['mean']:.3f} | {int(r['n'])} | {std} |")
    lines.append("")
    path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--bootstrap", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20260513)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_ROOT / "results")
    args = parser.parse_args()

    outputs = summarize(args.root, args.bootstrap, args.seed)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, df in outputs.items():
        if name == "merged":
            continue
        df.to_csv(args.output_dir / f"perceived_self_{name}.csv", index=False)
    write_markdown(outputs, args.output_dir / "perceived_self_reproducible_summary.md", args.bootstrap)
    print(f"wrote outputs to {args.output_dir}")
    print(outputs["main_coefficients"].to_string(index=False))


if __name__ == "__main__":
    main()
