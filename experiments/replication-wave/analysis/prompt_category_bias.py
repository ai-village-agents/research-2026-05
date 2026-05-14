#!/usr/bin/env python3
"""Compute C1 self-preference gaps by prompt category.

Each replication prompt has a category. This diagnostic asks whether C1
self-minus-peer gaps are larger in some prompt categories than others. Scores
use the study-standard 1-10 composite (mean of five rubric dimensions), and
counts are reported because category-level per-judge cells are tiny (one self
row and three peer rows per judge/category).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCORES_CSV = RESULTS / "long_scores.csv"
OUT_CSV = RESULTS / "prompt_category_bias.csv"
OUT_MD = RESULTS / "prompt_category_bias.md"

JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
SHORT = {"claude-opus-4.7": "Claude", "gemini-3.1-pro": "Gemini", "gpt-5.5": "GPT-5.5", "kimi-k2.6": "Kimi"}
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]


def main() -> None:
    scores = pd.read_csv(SCORES_CSV)
    c1 = scores[scores["condition"].str.lower() == "c1"].copy()
    if len(c1) != 160:
        raise SystemExit(f"Expected 160 C1 score rows, found {len(c1)}")
    c1["composite"] = c1[DIMS].mean(axis=1)
    c1["is_self"] = c1["judge"] == c1["author"]

    categories = sorted(c1["category"].unique())

    rows: list[dict[str, object]] = []
    for cat in categories:
        cat_df = c1[c1["category"] == cat]
        pooled_self = cat_df[cat_df["is_self"]]
        pooled_peer = cat_df[~cat_df["is_self"]]
        rows.append(
            {
                "level": "pooled",
                "category": cat,
                "judge": "all",
                "self_n": len(pooled_self),
                "self_mean": pooled_self["composite"].mean(),
                "peer_n": len(pooled_peer),
                "peer_mean": pooled_peer["composite"].mean(),
                "self_pref_gap": pooled_self["composite"].mean() - pooled_peer["composite"].mean(),
            }
        )
        for judge in JUDGES:
            judge_df = cat_df[cat_df["judge"] == judge]
            self_df = judge_df[judge_df["is_self"]]
            peer_df = judge_df[~judge_df["is_self"]]
            if len(self_df) != 1 or len(peer_df) != 3:
                raise SystemExit(f"Unexpected {cat}/{judge} counts: self={len(self_df)} peer={len(peer_df)}")
            rows.append(
                {
                    "level": "judge",
                    "category": cat,
                    "judge": judge,
                    "self_n": len(self_df),
                    "self_mean": self_df["composite"].mean(),
                    "peer_n": len(peer_df),
                    "peer_mean": peer_df["composite"].mean(),
                    "self_pref_gap": self_df["composite"].mean() - peer_df["composite"].mean(),
                }
            )

    out = pd.DataFrame(rows)
    out.to_csv(OUT_CSV, index=False, float_format="%.3f", lineterminator="\n")

    pooled = out[out["level"] == "pooled"].copy()
    per_judge = out[out["level"] == "judge"].copy()
    max_pooled = pooled.sort_values("self_pref_gap", ascending=False).iloc[0]
    min_pooled = pooled.sort_values("self_pref_gap", ascending=True).iloc[0]
    max_judge = per_judge.sort_values("self_pref_gap", ascending=False).iloc[0]
    min_judge = per_judge.sort_values("self_pref_gap", ascending=True).iloc[0]

    lines = [
        "# Self-preference gap by prompt category",
        "",
        "This diagnostic asks whether the nature of the prompt influences the severity",
        "of C1 self-preference. Scores are on the standard 1–10 composite scale.",
        "Because each category corresponds to one replication prompt, pooled rows have",
        "4 self and 12 peer ratings; per-judge rows have 1 self and 3 peer ratings and",
        "should be read as descriptive rather than inferential.",
        "",
        "## Pooled 4-judge gap by category",
        "",
        "| Category | Self n | Mean self | Peer n | Mean peer | Pooled gap |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in pooled.iterrows():
        lines.append(
            f"| {row['category']} | {int(row['self_n'])} | {row['self_mean']:.3f} | "
            f"{int(row['peer_n'])} | {row['peer_mean']:.3f} | {row['self_pref_gap']:+.3f} |"
        )
    lines += [
        "",
        "## Per-judge gap by category",
        "",
        "| Category | Judge | Self n | Mean self | Peer n | Mean peer | Gap |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for _, row in per_judge.iterrows():
        lines.append(
            f"| {row['category']} | {SHORT[row['judge']]} | {int(row['self_n'])} | {row['self_mean']:.3f} | "
            f"{int(row['peer_n'])} | {row['peer_mean']:.3f} | {row['self_pref_gap']:+.3f} |"
        )
    lines += [
        "",
        "## Reading",
        "",
        f"- Largest pooled category gap: {max_pooled['category']} {max_pooled['self_pref_gap']:+.3f}.",
        f"- Smallest pooled category gap: {min_pooled['category']} {min_pooled['self_pref_gap']:+.3f}.",
        f"- Largest per-judge/category positive gap: {SHORT[max_judge['judge']]} on {max_judge['category']} {max_judge['self_pref_gap']:+.3f}.",
        f"- Largest per-judge/category negative gap: {SHORT[min_judge['judge']]} on {min_judge['category']} {min_judge['self_pref_gap']:+.3f}.",
        "- Category patterns are heavily confounded with prompt-specific response quality; use leave-one-prompt/category sensitivity for robustness, not as a causal category test.",
        "",
        "*Generated by `analysis/prompt_category_bias.py` from `results/long_scores.csv`.*",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
