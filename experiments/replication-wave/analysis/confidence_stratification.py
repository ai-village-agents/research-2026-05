#!/usr/bin/env python3
"""Stratify perceived-self score gaps by authorship-confidence level.

This diagnostic joins C1 quality scores to the C4 recognition probe and asks:
within each judge and confidence level, do items perceived as self-authored
receive higher scores than items perceived as peer-authored?

Scores use the study-standard 1-10 composite (mean of the five rubric
dimensions), not the 5-50 summed scale. Counts are reported because several
judge × confidence × perceived-self cells are sparse or absent.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCORES_CSV = RESULTS / "long_scores.csv"
RECOG_CSV = RESULTS / "long_recognition.csv"
OUT_CSV = RESULTS / "confidence_stratification.csv"
OUT_MD = RESULTS / "confidence_stratification.md"

JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
SHORT = {"claude-opus-4.7": "Claude", "gemini-3.1-pro": "Gemini", "gpt-5.5": "GPT-5.5", "kimi-k2.6": "Kimi"}
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]


def fmt_num(x: object, digits: int = 3) -> str:
    return "N/A" if pd.isna(x) else f"{float(x):+.{digits}f}"


def fmt_mean(x: object) -> str:
    return "N/A" if pd.isna(x) else f"{float(x):.3f}"


def main() -> None:
    scores = pd.read_csv(SCORES_CSV)
    recognition = pd.read_csv(RECOG_CSV)

    c1 = scores[scores["condition"].str.lower() == "c1"].copy()
    if len(c1) != 160:
        raise SystemExit(f"Expected 160 C1 score rows, found {len(c1)}")
    if len(recognition) != 160:
        raise SystemExit(f"Expected 160 recognition rows, found {len(recognition)}")

    c1["composite"] = c1[DIMS].mean(axis=1)
    merged = pd.merge(
        c1[["judge", "author", "prompt_id", "composite"]],
        recognition[["judge", "true_author", "prompt_id", "predicted_author", "confidence"]],
        left_on=["judge", "author", "prompt_id"],
        right_on=["judge", "true_author", "prompt_id"],
        how="inner",
        validate="one_to_one",
    )
    if len(merged) != 160:
        raise SystemExit(f"Expected 160 merged C1/recognition rows, found {len(merged)}")

    merged["perceived_self"] = merged["predicted_author"] == merged["judge"]

    agg = (
        merged.groupby(["judge", "confidence", "perceived_self"], observed=False)["composite"]
        .agg(["count", "mean"])
        .reset_index()
    )
    pivot = agg.pivot_table(index=["judge", "confidence"], columns="perceived_self", values=["count", "mean"])

    rows: list[dict[str, object]] = []
    for judge in JUDGES:
        judge_conf = sorted(merged.loc[merged["judge"] == judge, "confidence"].unique())
        for conf in judge_conf:
            row: dict[str, object] = {"judge": judge, "confidence": int(conf)}
            for perceived in [True, False]:
                label = "perceived_self" if perceived else "perceived_peer"
                try:
                    n_val = pivot.loc[(judge, conf), ("count", perceived)]
                    mean_val = pivot.loc[(judge, conf), ("mean", perceived)]
                except KeyError:
                    n_val = pd.NA
                    mean_val = pd.NA
                if pd.isna(n_val):
                    row[f"{label}_n"] = 0
                    row[f"{label}_mean"] = pd.NA
                else:
                    row[f"{label}_n"] = int(n_val)
                    row[f"{label}_mean"] = float(mean_val)
            if row["perceived_self_n"] and row["perceived_peer_n"]:
                row["perceived_self_gap"] = row["perceived_self_mean"] - row["perceived_peer_mean"]
            else:
                row["perceived_self_gap"] = pd.NA
            rows.append(row)

    out = pd.DataFrame(rows)
    numeric_cols = [
        "confidence",
        "perceived_self_n",
        "perceived_self_mean",
        "perceived_peer_n",
        "perceived_peer_mean",
        "perceived_self_gap",
    ]
    for col in numeric_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out.to_csv(OUT_CSV, index=False, float_format="%.3f", lineterminator="\n")

    valid = out.dropna(subset=["perceived_self_gap"]).copy()
    largest_pos = valid.sort_values("perceived_self_gap", ascending=False).iloc[0] if not valid.empty else None
    largest_neg = valid.sort_values("perceived_self_gap", ascending=True).iloc[0] if not valid.empty else None

    lines = [
        "# Self-preference stratified by authorship confidence",
        "",
        "This diagnostic joins C1 quality scores to each judge's C4 authorship-recognition",
        "answers. Within each judge and confidence level, it compares the mean composite",
        "score for items the judge *perceived as self-authored* with items perceived as",
        "peer-authored. Scores are on the standard 1–10 composite scale. Counts are shown",
        "because several strata are sparse; rows with one missing side are descriptive only.",
        "",
        "| Judge | Confidence | Perceived-self n | Perceived-self mean | Perceived-peer n | Perceived-peer mean | Gap |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in out.iterrows():
        lines.append(
            f"| {SHORT[row['judge']]} | {int(row['confidence'])} | "
            f"{int(row['perceived_self_n'])} | {fmt_mean(row['perceived_self_mean'])} | "
            f"{int(row['perceived_peer_n'])} | {fmt_mean(row['perceived_peer_mean'])} | "
            f"{fmt_num(row['perceived_self_gap'])} |"
        )
    lines += ["", "## Reading", ""]
    if largest_pos is not None and largest_neg is not None:
        lines.append(
            f"- Largest positive available stratum: {SHORT[largest_pos['judge']]} confidence {int(largest_pos['confidence'])}, "
            f"gap {float(largest_pos['perceived_self_gap']):+.3f} "
            f"(n_self={int(largest_pos['perceived_self_n'])}, n_peer={int(largest_pos['perceived_peer_n'])})."
        )
        lines.append(
            f"- Largest negative available stratum: {SHORT[largest_neg['judge']]} confidence {int(largest_neg['confidence'])}, "
            f"gap {float(largest_neg['perceived_self_gap']):+.3f} "
            f"(n_self={int(largest_neg['perceived_self_n'])}, n_peer={int(largest_neg['perceived_peer_n'])})."
        )
    lines += [
        "- Treat this as an exploratory descriptive split, not an independent causal test:",
        "  confidence is self-reported in the recognition probe and is sparse for several judges.",
        "",
        "*Generated by `analysis/confidence_stratification.py` from `results/long_scores.csv` and `results/long_recognition.csv`.*",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")


if __name__ == "__main__":
    main()
