#!/usr/bin/env python3
"""Analyze evaluator-bias experiment results.

This script is intentionally conservative: it accepts either a real results JSONL/JSON
file or the existing mock data file, normalizes common field names, and prints the
pre-registered descriptive quantities needed for H1-H4.

Expected scoring rows, one row per judged response per condition, should contain at
least:
  prompt_id, author/generator, judge/evaluator, condition, and either composite_score
  or the five rubric dimensions (correctness, completeness, clarity, creativity,
  constraint_adherence).

Expected recognition rows should contain:
  prompt_id, author/generator, judge/evaluator, predicted_author/recognized_as,
  confidence (optional), condition=C4 (or be supplied in a separate recognition file).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, Any

import numpy as np
import pandas as pd

RUBRIC_COLUMNS = [
    "correctness",
    "completeness",
    "clarity",
    "creativity",
    "constraint_adherence",
]
MODEL_ORDER = ["gpt-5.5", "claude-opus-4.7", "gemini-3.1-pro", "kimi-k2.6"]
MODEL_ALIASES = {
    "GPT-5.5": "gpt-5.5",
    "Claude Opus 4.7": "claude-opus-4.7",
    "Gemini 3.1 Pro": "gemini-3.1-pro",
    "Kimi K2.6": "kimi-k2.6",
}


def read_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".jsonl":
        records = []
        with path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
        return records
    data = json.load(path.open())
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("rows", "records", "data", "results"):
            if isinstance(data.get(key), list):
                return data[key]
    raise ValueError(f"Could not find a list of records in {path}")


def norm_model(x: Any) -> str:
    if pd.isna(x):
        return ""
    s = str(x)
    return MODEL_ALIASES.get(s, s)


def normalize_condition(x: Any) -> str:
    s = str(x).strip()
    mapping = {"baseline": "C1", "style_neutralized": "C2", "bias_warned": "C3", "recognition": "C4"}
    return mapping.get(s, s)


def flatten_scores_record(row: dict[str, Any]) -> Iterable[dict[str, Any]]:
    """Expand a nested judge-output object into row records when needed."""
    if isinstance(row.get("scores"), dict):
        for blind_id, score_obj in row["scores"].items():
            out = {k: v for k, v in row.items() if k != "scores"}
            out["blind_id"] = blind_id
            if isinstance(score_obj, dict):
                out.update(score_obj)
            yield out
    else:
        yield row


def load_frame(path: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for rec in read_records(path):
        rows.extend(flatten_scores_record(rec))
    df = pd.DataFrame(rows)
    rename = {
        "generator": "author",
        "evaluator": "judge",
        "judge_model": "judge",
        "model": "author",
        "prompt": "prompt_id",
        "recognized_as": "predicted_author",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    for col in ("author", "judge", "predicted_author"):
        if col in df.columns:
            df[col] = df[col].map(norm_model)
    if "condition" in df.columns:
        df["condition"] = df["condition"].map(normalize_condition)
    if "composite_score" not in df.columns:
        present = [c for c in RUBRIC_COLUMNS if c in df.columns]
        if present:
            df["composite_score"] = df[present].apply(pd.to_numeric, errors="coerce").mean(axis=1)
        elif "score" in df.columns:
            df["composite_score"] = pd.to_numeric(df["score"], errors="coerce")
    if "author" in df.columns and "judge" in df.columns:
        df["author_is_self"] = df["author"] == df["judge"]
    return df


def summarize_coverage(df: pd.DataFrame) -> None:
    print("\n== Coverage ==")
    print(f"Rows: {len(df):,}")
    for col in ("condition", "judge", "author"):
        if col in df.columns:
            print(f"\n{col} counts:")
            print(df[col].value_counts(dropna=False).sort_index())
    if {"condition", "judge", "author"}.issubset(df.columns):
        print("\nRows by condition × judge × author:")
        print(pd.crosstab([df["condition"], df["judge"]], df["author"]))


def self_preference_table(df: pd.DataFrame) -> pd.DataFrame:
    scoring = df[df["condition"].isin(["C1", "C2", "C3"])].copy()
    scoring = scoring.dropna(subset=["composite_score"])
    if scoring.empty:
        return pd.DataFrame()
    grouped = scoring.groupby(["condition", "judge", "author_is_self"])["composite_score"].mean().unstack()
    grouped = grouped.rename(columns={False: "score_for_others", True: "score_for_self"})
    for col in ("score_for_others", "score_for_self"):
        if col not in grouped:
            grouped[col] = np.nan
    grouped["self_preference_gap"] = grouped["score_for_self"] - grouped["score_for_others"]
    return grouped.reset_index().sort_values(["condition", "judge"])


def attenuation_table(gaps: pd.DataFrame) -> pd.DataFrame:
    if gaps.empty:
        return gaps
    wide = gaps.pivot(index="judge", columns="condition", values="self_preference_gap")
    if "C1" not in wide:
        return wide.reset_index()
    for cond in ("C2", "C3"):
        if cond in wide:
            wide[f"{cond}_minus_C1"] = wide[cond] - wide["C1"]
            wide[f"{cond}_attenuation_pct"] = np.where(
                wide["C1"].abs() > 1e-9,
                100 * (wide["C1"] - wide[cond]) / wide["C1"].abs(),
                np.nan,
            )
    return wide.reset_index()


def recognition_summary(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    recog = df[(df.get("condition", pd.Series(index=df.index, dtype=object)) == "C4") | df.get("predicted_author", pd.Series(index=df.index, dtype=object)).notna()].copy()
    if recog.empty or not {"judge", "author", "predicted_author"}.issubset(recog.columns):
        return pd.DataFrame(), pd.DataFrame()
    recog["correct_recognition"] = recog["predicted_author"] == recog["author"]
    acc = recog.groupby("judge")["correct_recognition"].agg(["mean", "sum", "count"]).reset_index()
    acc = acc.rename(columns={"mean": "accuracy", "sum": "correct", "count": "n"})
    matrix = pd.crosstab([recog["judge"], recog["author"]], recog["predicted_author"], dropna=False)
    return acc, matrix


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="data/results.jsonl", help="Real scoring/recognition rows (.jsonl or .json).")
    ap.add_argument("--mock", default="data/mock_results.json", help="Fallback mock results file.")
    args = ap.parse_args()

    result_path = Path(args.results)
    if result_path.exists():
        print(f"Loading real results from {result_path}")
        df = load_frame(result_path)
    else:
        print(f"Real results not found at {result_path}; loading mock data from {args.mock}")
        df = load_frame(Path(args.mock))

    summarize_coverage(df)

    print("\n== Self-preference gaps: mean composite(self) - mean composite(others) ==")
    gaps = self_preference_table(df)
    if gaps.empty:
        print("No scoring rows found.")
    else:
        print(gaps.to_string(index=False, float_format=lambda x: f"{x:0.3f}"))

    print("\n== C2/C3 attenuation relative to C1 ==")
    att = attenuation_table(gaps)
    if att.empty:
        print("No C1-C3 gaps available.")
    else:
        print(att.to_string(index=False, float_format=lambda x: f"{x:0.3f}"))

    print("\n== Self-recognition accuracy ==")
    acc, matrix = recognition_summary(df)
    if acc.empty:
        print("No C4/predicted_author rows found.")
    else:
        print(acc.to_string(index=False, float_format=lambda x: f"{x:0.3f}"))
        print("\nConfusion matrix (judge, true author) × predicted author:")
        print(matrix)


if __name__ == "__main__":
    main()
