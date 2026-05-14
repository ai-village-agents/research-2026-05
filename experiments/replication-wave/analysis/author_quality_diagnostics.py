#!/usr/bin/env python3
"""Author-quality diagnostics for the D407 replication wave.

This supplement quantifies the content-quality confound behind the observed
C1 self-preference/self-penalty pattern by summarizing how each author's
original responses were scored by *other* judges. Excluding self-judgments is
important: it estimates response quality from independent judges rather than
reusing the potentially biased self rows whose interpretation is at issue.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
LONG_SCORES = RESULTS / "long_scores.csv"

DIMS = [
    "correctness",
    "completeness",
    "clarity",
    "creativity",
    "constraint_adherence",
]
MODELS = [
    "claude-opus-4.7",
    "gemini-3.1-pro",
    "gpt-5.5",
    "kimi-k2.6",
]


def _fmt(x: float) -> str:
    return f"{x:.3f}"


def main() -> None:
    df = pd.read_csv(LONG_SCORES)
    missing = [col for col in ["judge", "author", "condition", *DIMS] if col not in df.columns]
    if missing:
        raise SystemExit(f"Missing required columns: {missing}")

    df["composite"] = df[DIMS].mean(axis=1)
    c1 = df[df["condition"].astype(str).str.lower() == "c1"].copy()
    if len(c1) != 160:
        raise SystemExit(f"Expected 160 C1 rows, found {len(c1)}")

    nonself = c1[c1["judge"] != c1["author"]].copy()
    if len(nonself) != 120:
        raise SystemExit(f"Expected 120 non-self C1 rows, found {len(nonself)}")

    author_quality = (
        nonself.groupby("author")["composite"]
        .agg(mean="mean", sd="std", n="count")
        .reindex(MODELS)
        .reset_index()
    )
    author_quality["mean_minus_kimi"] = (
        author_quality["mean"] - float(author_quality.loc[author_quality["author"] == "kimi-k2.6", "mean"].iloc[0])
    )

    by_judge_author = (
        c1.pivot_table(index="judge", columns="author", values="composite", aggfunc="mean")
        .reindex(index=MODELS, columns=MODELS)
        .round(3)
    )

    by_dim = (
        nonself.groupby("author")[DIMS]
        .mean()
        .reindex(MODELS)
        .reset_index()
    )

    author_quality.to_csv(RESULTS / "author_quality_nonself_c1.csv", index=False, float_format="%.6f")
    by_judge_author.to_csv(RESULTS / "author_quality_by_judge_c1.csv", float_format="%.6f")
    by_dim.to_csv(RESULTS / "author_quality_nonself_c1_by_dimension.csv", index=False, float_format="%.6f")

    kimi_mean = float(author_quality.loc[author_quality["author"] == "kimi-k2.6", "mean"].iloc[0])
    non_kimi_mean = float(nonself[nonself["author"] != "kimi-k2.6"]["composite"].mean())
    kimi_deficit = kimi_mean - non_kimi_mean
    claude_mean = float(author_quality.loc[author_quality["author"] == "claude-opus-4.7", "mean"].iloc[0])

    md = []
    md.append("# Author-quality diagnostic for C1 originals\n")
    md.append(
        "This supplement estimates underlying response quality in the D407 replication wave "
        "using only **non-self C1 judgments**: for each author, it averages the scores assigned "
        "by the other three judges to that author's original responses. This keeps the diagnostic "
        "separate from the self-judgment rows whose bias is under study.\n"
    )
    md.append("## Non-self author quality\n")
    md.append("| Author | Mean composite | SD | Rows | Mean minus Kimi |")
    md.append("|---|---:|---:|---:|---:|")
    for row in author_quality.itertuples(index=False):
        md.append(f"| `{row.author}` | {_fmt(row.mean)} | {_fmt(row.sd)} | {int(row.n)} | {_fmt(row.mean_minus_kimi)} |")
    md.append("")
    md.append(
        f"Across independent judges, Kimi-authored originals average **{kimi_mean:.3f}**, versus "
        f"**{non_kimi_mean:.3f}** for the three non-Kimi authors combined (Kimi minus non-Kimi: "
        f"**{kimi_deficit:.3f}**). Claude-authored originals average **{claude_mean:.3f}**, "
        f"which is **{claude_mean - kimi_mean:.3f}** points above Kimi on the same 1–10 composite scale.\n"
    )
    md.append("## C1 judge × author means (including the self cell on the diagonal)\n")
    md.append("| Judge | Claude | Gemini | GPT-5.5 | Kimi |")
    md.append("|---|---:|---:|---:|---:|")
    for judge, row in by_judge_author.iterrows():
        md.append(
            f"| `{judge}` | {_fmt(row['claude-opus-4.7'])} | {_fmt(row['gemini-3.1-pro'])} | "
            f"{_fmt(row['gpt-5.5'])} | {_fmt(row['kimi-k2.6'])} |"
        )
    md.append("")
    md.append("## Non-self author quality by dimension\n")
    md.append("| Author | Correctness | Completeness | Clarity | Creativity | Constraint adherence |")
    md.append("|---|---:|---:|---:|---:|---:|")
    for row in by_dim.itertuples(index=False):
        md.append(
            f"| `{row.author}` | {_fmt(row.correctness)} | {_fmt(row.completeness)} | {_fmt(row.clarity)} | "
            f"{_fmt(row.creativity)} | {_fmt(row.constraint_adherence)} |"
        )
    md.append("")
    md.append("## Interpretation\n")
    md.append(
        "These diagnostics strengthen the quality-confound explanation for the observed Kimi self-penalty: "
        "Kimi-the-judge is not uniquely harsh toward Kimi-authored C1 responses; the other three judges also "
        "score Kimi-authored originals far below the other authors. The planned quality-balanced wave therefore "
        "has a sharp target: test whether Kimi still self-penalizes when the prompt set is designed to remove this "
        "large independent quality gap.\n"
    )
    md.append(
        "Generated by `experiments/replication-wave/analysis/author_quality_diagnostics.py` from "
        "`experiments/replication-wave/results/long_scores.csv`.\n"
    )

    (RESULTS / "author_quality_diagnostics.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {RESULTS / 'author_quality_nonself_c1.csv'}")
    print(f"Wrote {RESULTS / 'author_quality_by_judge_c1.csv'}")
    print(f"Wrote {RESULTS / 'author_quality_nonself_c1_by_dimension.csv'}")
    print(f"Wrote {RESULTS / 'author_quality_diagnostics.md'}")
    print(f"Kimi non-self mean {kimi_mean:.3f}; non-Kimi mean {non_kimi_mean:.3f}; gap {kimi_deficit:.3f}")


if __name__ == "__main__":
    main()
