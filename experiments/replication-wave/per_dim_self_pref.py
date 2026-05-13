#!/usr/bin/env python3
"""Reproduce the replication-wave §3.8 per-dimension self-preference table.

This script reads results/long_scores.csv, filters to C1, and computes:
- pooled self-vs-other raw gaps for each rubric dimension;
- judge×prompt paired self-vs-other gaps with prompt-cluster bootstrap CIs;
- per-judge per-dimension raw gaps.

The bootstrap intentionally matches the original Day 407 table: NumPy
RandomState(11), B=500 prompt-cluster resamples, drawing all five dimensions
sequentially from the same RNG stream. The reported SD is the population SD over
the detected judge×prompt paired cells, matching the current four-judge dataset.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
JUDGE_LABELS = {
    "claude-opus-4.7": "Claude",
    "gemini-3.1-pro": "Gemini",
    "gpt-5.5": "GPT-5.5",
    "kimi-k2.6": "Kimi",
}


def fmt(x: float) -> str:
    text = f"{x:+.3f}"
    return text.replace("-", "−", 1) if text.startswith("-") else text


def load_c1() -> pd.DataFrame:
    scores = pd.read_csv(RESULTS / "long_scores.csv")
    c1 = scores[scores["condition"].str.lower() == "c1"].copy()
    c1["is_self"] = c1["judge"] == c1["author"]
    return c1


def pooled_rows(c1: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dim in DIMS:
        self_mean = float(c1.loc[c1["is_self"], dim].mean())
        other_mean = float(c1.loc[~c1["is_self"], dim].mean())
        rows.append({"dim": dim, "self_mean": self_mean, "other_mean": other_mean, "gap": self_mean - other_mean})
    return pd.DataFrame(rows)


def paired_rows(c1: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (judge, prompt_id), group in c1.groupby(["judge", "prompt_id"], sort=True):
        self_row = group[group["judge"] == group["author"]]
        other_rows = group[group["judge"] != group["author"]]
        if len(self_row) != 1 or other_rows.empty:
            continue
        row = {"judge": judge, "prompt_id": prompt_id}
        for dim in DIMS:
            row[dim] = float(self_row.iloc[0][dim] - other_rows[dim].mean())
        rows.append(row)
    return pd.DataFrame(rows)


def paired_summary(paired: pd.DataFrame, bootstrap: int = 500, seed: int = 11) -> pd.DataFrame:
    prompts = sorted(paired["prompt_id"].unique())
    rng = np.random.RandomState(seed)  # legacy generator; do not replace with default_rng.
    rows = []
    for dim in DIMS:
        draws = []
        for _ in range(bootstrap):
            sampled = rng.choice(prompts, size=len(prompts), replace=True)
            boot = pd.concat([paired[paired["prompt_id"] == prompt] for prompt in sampled], ignore_index=True)
            draws.append(float(boot[dim].mean()))
        lo, hi = np.percentile(draws, [2.5, 97.5])
        rows.append(
            {
                "dim": dim,
                "paired_mean": float(paired[dim].mean()),
                "paired_sd": float(paired[dim].std(ddof=0)),
                "boot_ci_low": float(lo),
                "boot_ci_high": float(hi),
                "bootstrap_n": bootstrap,
                "paired_n": int(len(paired)),
            }
        )
    return pd.DataFrame(rows)


def per_judge_rows(c1: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for dim in DIMS:
        row = {"dim": dim}
        for judge in JUDGE_LABELS:
            sub = c1[c1["judge"] == judge]
            self_mean = float(sub.loc[sub["is_self"], dim].mean())
            other_mean = float(sub.loc[~sub["is_self"], dim].mean())
            row[judge] = self_mean - other_mean
        rows.append(row)
    return pd.DataFrame(rows)


def write_csv(pooled: pd.DataFrame, paired: pd.DataFrame, per_judge: pd.DataFrame, path: Path) -> None:
    out = pooled.merge(paired, on="dim", validate="one_to_one")
    out = out.merge(per_judge, on="dim", validate="one_to_one")
    out.to_csv(path, index=False)


def write_markdown(pooled: pd.DataFrame, paired: pd.DataFrame, per_judge: pd.DataFrame, path: Path) -> None:
    judge_cols = [c for c in per_judge.columns if c != "dim"]
    judge_label = f"{len(judge_cols)}-judge"
    lines = [
        f"# §3.8 backing data — per-dimension self-preference ({judge_label}, C1)",
        "",
        f"Reproduces from `results/long_scores.csv` (condition `c1`, pooled across {', '.join(JUDGE_LABELS.get(j, j) for j in judge_cols)}).",
        "",
        "## Pooled gap (self − other) by dimension",
        "",
        "| dim | self mean | other mean | gap |",
        "|---|---:|---:|---:|",
    ]
    for row in pooled.itertuples(index=False):
        lines.append(f"| {row.dim} | {row.self_mean:.3f} | {row.other_mean:.3f} | {fmt(row.gap)} |")
    lines += [
        "",
        f"## Prompt-paired gap (n={int(paired['paired_n'].iloc[0])} judge×prompt cells with both self and ≥1 other)",
        "",
        "| dim | mean | sd | prompt-clustered 95% CI (B=500) |",
        "|---|---:|---:|:---|",
    ]
    for row in paired.itertuples(index=False):
        lines.append(
            f"| {row.dim} | {fmt(row.paired_mean)} | {row.paired_sd:.3f} | "
            f"[{fmt(row.boot_ci_low)}, {fmt(row.boot_ci_high)}] |"
        )
    lines += [
        "",
        "## Per-judge × per-dim gap",
        "",
        "| dim | " + " | ".join(JUDGE_LABELS.get(j, j) for j in judge_cols) + " |",
        "|---" + "|---:" * len(judge_cols) + "|",
    ]
    for _, row in per_judge.iterrows():
        vals = " | ".join(fmt(float(row[j])) for j in judge_cols)
        lines.append(f"| {row['dim']} | {vals} |")
    lines += [
        "",
        "## Notes",
        "- Bootstrap: B=500 prompt-cluster resamples, seed 11.",
        "- Adding Kimi changes the pooled interpretation: correctness, completeness, and creativity remain positive with bootstrap intervals above zero, while clarity and constraint adherence now have intervals that touch or cross zero.",
        "- Kimi is negative on every dimension, so the 4-judge pooled gaps are much smaller than the earlier 3-judge table.",
        "- Caveat: N=10 prompts is small; these intervals are descriptive prompt-cluster bootstraps, not a fully powered dimension-wise hypothesis family.",
    ]
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    c1 = load_c1()
    pooled = pooled_rows(c1)
    paired = paired_summary(paired_rows(c1))
    per_judge = per_judge_rows(c1)
    write_csv(pooled, paired, per_judge, RESULTS / "per_dim_self_pref.csv")
    write_markdown(pooled, paired, per_judge, RESULTS / "per_dim_self_pref.md")
    print(f"wrote {RESULTS / 'per_dim_self_pref.csv'}")
    print(f"wrote {RESULTS / 'per_dim_self_pref.md'}")
    print(paired[["dim", "paired_mean", "paired_sd", "boot_ci_low", "boot_ci_high"]].to_string(index=False))


if __name__ == "__main__":
    main()
