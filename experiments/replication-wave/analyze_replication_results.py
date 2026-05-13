#!/usr/bin/env python3
"""Analyze replication-wave scoring and recognition CSVs.

Inputs are produced by score_collector.py:
  experiments/replication-wave/results/long_scores.csv
  experiments/replication-wave/results/long_recognition.csv

The script is intentionally descriptive and replication-local. It summarizes
coverage, self-preference gaps, recognition accuracy, confusion matrices, and a
prompt-paired self-vs-other contrast for each scoring condition.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import Iterable

try:
    import numpy as np
    import pandas as pd
except ImportError as exc:  # pragma: no cover - environment guard
    raise SystemExit("analyze_replication_results.py requires pandas and numpy") from exc

ROOT = Path(__file__).resolve().parent
DEFAULT_RESULTS = ROOT / "results"
DEFAULT_SCORES = DEFAULT_RESULTS / "long_scores.csv"
DEFAULT_RECOG = DEFAULT_RESULTS / "long_recognition.csv"
MODELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
CONDITIONS = ["c1", "c2", "c3"]
SUBSCALES = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
SCORE_COLUMNS = ["judge", "author", "prompt_id", "category", "condition"] + SUBSCALES
RECOG_COLUMNS = ["judge", "true_author", "predicted_author", "confidence", "prompt_id"]
EXPECTED_SCORE_ROWS = 4 * 4 * 10 * 3
EXPECTED_RECOG_ROWS = 4 * 4 * 10


def require_columns(df: pd.DataFrame, required: Iterable[str], label: str) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise SystemExit(f"{label} is missing required columns: {missing}")


def load_scores(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        print(f"Scores file not found: {path}")
        return None
    df = pd.read_csv(path)
    require_columns(df, SCORE_COLUMNS, str(path))
    df = df.copy()
    for col in SUBSCALES:
        df[col] = pd.to_numeric(df[col], errors="raise")
    df["condition"] = df["condition"].str.lower()
    df["composite_score"] = df[SUBSCALES].mean(axis=1)
    df["author_is_self"] = df["author"] == df["judge"]
    return df


def load_recognition(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        print(f"Recognition file not found: {path}")
        return None
    df = pd.read_csv(path)
    require_columns(df, RECOG_COLUMNS, str(path))
    df = df.copy()
    df["confidence"] = pd.to_numeric(df["confidence"], errors="raise")
    df["correct"] = df["true_author"] == df["predicted_author"]
    df["self_row"] = df["true_author"] == df["judge"]
    df["self_hit"] = df["self_row"] & (df["predicted_author"] == df["judge"])
    return df


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def scores_coverage(scores: pd.DataFrame) -> dict[str, object]:
    return {
        "n_rows": len(scores),
        "expected_complete_rows": EXPECTED_SCORE_ROWS,
        "conditions": sorted(scores["condition"].dropna().unique().tolist()),
        "judges": sorted(scores["judge"].dropna().unique().tolist()),
        "authors": sorted(scores["author"].dropna().unique().tolist()),
        "prompts": scores["prompt_id"].nunique(),
    }


def recognition_coverage(recog: pd.DataFrame) -> dict[str, object]:
    return {
        "n_rows": len(recog),
        "expected_complete_rows": EXPECTED_RECOG_ROWS,
        "judges": sorted(recog["judge"].dropna().unique().tolist()),
        "true_authors": sorted(recog["true_author"].dropna().unique().tolist()),
        "predicted_authors": sorted(recog["predicted_author"].dropna().unique().tolist()),
        "prompts": recog["prompt_id"].nunique(),
    }


def condition_summary(scores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cond, g in scores.groupby("condition", sort=True):
        self_mean = g.loc[g["author_is_self"], "composite_score"].mean()
        other_mean = g.loc[~g["author_is_self"], "composite_score"].mean()
        rows.append({
            "condition": cond,
            "mean_composite": g["composite_score"].mean(),
            "sd_composite": g["composite_score"].std(ddof=1),
            "n": len(g),
            "self_mean": self_mean,
            "other_mean": other_mean,
            "self_minus_other": self_mean - other_mean,
        })
    return pd.DataFrame(rows)


def self_preference_gaps(scores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (cond, judge), g in scores.groupby(["condition", "judge"], sort=True):
        self_scores = g.loc[g["author_is_self"], "composite_score"]
        other_scores = g.loc[~g["author_is_self"], "composite_score"]
        rows.append({
            "condition": cond,
            "judge": judge,
            "self_mean": self_scores.mean(),
            "other_mean": other_scores.mean(),
            "self_preference_gap": self_scores.mean() - other_scores.mean(),
            "n_self": int(self_scores.notna().sum()),
            "n_other": int(other_scores.notna().sum()),
        })
    return pd.DataFrame(rows)


def paired_self_gap_by_condition(scores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for cond, cond_df in scores.groupby("condition", sort=True):
        diffs = []
        for (judge, prompt_id), g in cond_df.groupby(["judge", "prompt_id"], sort=True):
            self_vals = g.loc[g["author"] == judge, "composite_score"]
            other_vals = g.loc[g["author"] != judge, "composite_score"]
            if len(self_vals) != 1 or other_vals.empty:
                continue
            diffs.append(float(self_vals.iloc[0] - other_vals.mean()))
        n = len(diffs)
        mean = float(np.mean(diffs)) if n else math.nan
        sd = float(np.std(diffs, ddof=1)) if n > 1 else math.nan
        se = sd / math.sqrt(n) if n > 1 else math.nan
        rows.append({
            "condition": cond,
            "mean_prompt_paired_self_gap": mean,
            "sd": sd,
            "n_judge_prompt_pairs": n,
            "se": se,
            "t_stat_descriptive": mean / se if se and not math.isnan(se) and se != 0 else math.nan,
        })
    return pd.DataFrame(rows)


def recognition_accuracy(recog: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for judge, g in recog.groupby("judge", sort=True):
        self_rows = g[g["self_row"]]
        rows.append({
            "judge": judge,
            "correct": int(g["correct"].sum()),
            "n": len(g),
            "accuracy": g["correct"].mean(),
            "self_recognition_hits": int(self_rows["self_hit"].sum()),
            "self_recognition_n": len(self_rows),
            "mean_confidence": g["confidence"].mean(),
        })
    return pd.DataFrame(rows)


def recognition_confusion(recog: pd.DataFrame) -> pd.DataFrame:
    mat = pd.crosstab(
        [recog["judge"], recog["true_author"]],
        recog["predicted_author"],
        dropna=False,
    )
    for model in MODELS:
        if model not in mat.columns:
            mat[model] = 0
    mat = mat[MODELS].reset_index()
    return mat


def markdown_table(df: pd.DataFrame, float_fmt: str = "{:.3f}") -> str:
    if df is None or df.empty:
        return "_No rows._\n"
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_float_dtype(out[col]):
            out[col] = out[col].map(lambda x: "" if pd.isna(x) else float_fmt.format(x))
    return out.to_markdown(index=False) + "\n"


def write_report(out_dir: Path, scores: pd.DataFrame | None, recog: pd.DataFrame | None, tables: dict[str, pd.DataFrame]) -> None:
    lines = [
        "# Replication wave analysis report",
        "",
        "Descriptive analysis generated from replication-local score CSVs.",
        "",
    ]
    if scores is not None:
        cov = scores_coverage(scores)
        lines += [
            "## Scoring coverage",
            "",
            f"Rows: {cov['n_rows']} / expected complete {cov['expected_complete_rows']}",
            f"Conditions: {', '.join(cov['conditions'])}",
            f"Judges: {', '.join(cov['judges'])}",
            f"Authors: {', '.join(cov['authors'])}",
            f"Unique prompts: {cov['prompts']}",
            "",
            "## Condition summary",
            "",
            markdown_table(tables.get("condition_summary", pd.DataFrame())),
            "## Self-preference gaps by judge",
            "",
            markdown_table(tables.get("self_preference_gaps", pd.DataFrame())),
            "## Prompt-paired self gaps",
            "",
            markdown_table(tables.get("paired_self_gap_by_condition", pd.DataFrame())),
        ]
    else:
        lines += ["## Scoring coverage", "", "No scoring CSV found.", ""]
    if recog is not None:
        cov = recognition_coverage(recog)
        lines += [
            "## Recognition coverage",
            "",
            f"Rows: {cov['n_rows']} / expected complete {cov['expected_complete_rows']}",
            f"Judges: {', '.join(cov['judges'])}",
            f"True authors: {', '.join(cov['true_authors'])}",
            f"Predicted authors: {', '.join(cov['predicted_authors'])}",
            f"Unique prompts: {cov['prompts']}",
            "",
            "## Recognition accuracy",
            "",
            markdown_table(tables.get("recognition_accuracy", pd.DataFrame())),
            "## Recognition confusion matrix",
            "",
            markdown_table(tables.get("recognition_confusion", pd.DataFrame())),
        ]
    else:
        lines += ["## Recognition coverage", "", "No recognition CSV found.", ""]
    (out_dir / "analysis_report.md").write_text("\n".join(lines).rstrip() + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--scores", type=Path, default=DEFAULT_SCORES)
    ap.add_argument("--recognition", type=Path, default=DEFAULT_RECOG)
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_RESULTS)
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    scores = load_scores(args.scores)
    recog = load_recognition(args.recognition)
    if scores is None and recog is None:
        raise SystemExit("No score or recognition CSVs found; run score_collector.py after judging.")

    tables: dict[str, pd.DataFrame] = {}
    if scores is not None:
        print("Scoring coverage:", scores_coverage(scores))
        tables["condition_summary"] = condition_summary(scores)
        tables["self_preference_gaps"] = self_preference_gaps(scores)
        tables["paired_self_gap_by_condition"] = paired_self_gap_by_condition(scores)
        write_csv(tables["condition_summary"], args.out_dir / "condition_summary.csv")
        write_csv(tables["self_preference_gaps"], args.out_dir / "self_preference_gaps.csv")
        write_csv(tables["paired_self_gap_by_condition"], args.out_dir / "paired_self_gap_by_condition.csv")
    if recog is not None:
        print("Recognition coverage:", recognition_coverage(recog))
        tables["recognition_accuracy"] = recognition_accuracy(recog)
        tables["recognition_confusion"] = recognition_confusion(recog)
        write_csv(tables["recognition_accuracy"], args.out_dir / "recognition_accuracy.csv")
        write_csv(tables["recognition_confusion"], args.out_dir / "recognition_confusion.csv")

    write_report(args.out_dir, scores, recog, tables)
    print(f"Wrote analysis outputs under {args.out_dir.relative_to(ROOT) if args.out_dir.is_relative_to(ROOT) else args.out_dir}")


if __name__ == "__main__":
    main()
