#!/usr/bin/env python3
"""Validate per-judge evaluator-bias judgment CSVs.

This is a lightweight preflight check for result PRs. It verifies that each
`data/judgments/<judge>/` directory has the expected long-format files, schemas,
row counts, condition counts, score ranges, confidence ranges, and model slugs.
It intentionally does not judge scientific conclusions; it only catches common
file-shape mistakes before rerunning the analysis suite.
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

MODELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
SCORE_HEADER = [
    "judge", "author", "prompt_id", "category", "condition",
    "correctness", "completeness", "clarity", "creativity", "constraint_adherence",
]
RECOG_HEADER = ["judge", "true_author", "predicted_author", "confidence", "prompt_id"]
SUBSCALES = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
EXPECTED_SCORE_ROWS_PER_JUDGE = 360
EXPECTED_RECOG_ROWS_PER_JUDGE = 120
EXPECTED_CONDITION_ROWS = {"c1": 120, "c2": 120, "c3": 120}
EXPECTED_SELF_RECOG_ROWS = 30


def read_csv(path: Path, expected_header: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        raise ValueError(f"missing file: {path}")
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != expected_header:
            raise ValueError(
                f"{path} has unexpected columns: got {reader.fieldnames}, expected {expected_header}"
            )
        return list(reader)


def require_int_range(path: Path, row_num: int, name: str, value: str, lo: int, hi: int) -> None:
    try:
        v = int(value)
    except ValueError as exc:
        raise ValueError(f"{path} row {row_num}: {name}={value!r} is not an integer") from exc
    if not lo <= v <= hi:
        raise ValueError(f"{path} row {row_num}: {name}={v} outside {lo}..{hi}")


def validate_judge_dir(judge_dir: Path, strict: bool) -> list[str]:
    judge = judge_dir.name
    messages: list[str] = []
    if judge not in MODELS:
        messages.append(f"WARNING: unexpected judge directory slug {judge!r}")

    score_path = judge_dir / "long_scores.csv"
    recog_path = judge_dir / "long_recognition.csv"
    scores = read_csv(score_path, SCORE_HEADER)
    recog = read_csv(recog_path, RECOG_HEADER)

    if len(scores) != EXPECTED_SCORE_ROWS_PER_JUDGE:
        raise ValueError(f"{score_path}: expected 360 rows, found {len(scores)}")
    if len(recog) != EXPECTED_RECOG_ROWS_PER_JUDGE:
        raise ValueError(f"{recog_path}: expected 120 rows, found {len(recog)}")

    score_judges = Counter(r["judge"] for r in scores)
    recog_judges = Counter(r["judge"] for r in recog)
    if score_judges != Counter({judge: len(scores)}):
        raise ValueError(f"{score_path}: judge column mismatch: {dict(score_judges)}")
    if recog_judges != Counter({judge: len(recog)}):
        raise ValueError(f"{recog_path}: judge column mismatch: {dict(recog_judges)}")

    conds = Counter(r["condition"] for r in scores)
    if conds != Counter(EXPECTED_CONDITION_ROWS):
        raise ValueError(f"{score_path}: condition counts mismatch: {dict(conds)}")

    for i, r in enumerate(scores, start=2):
        if r["author"] not in MODELS:
            raise ValueError(f"{score_path} row {i}: unknown author {r['author']!r}")
        if not r["prompt_id"]:
            raise ValueError(f"{score_path} row {i}: empty prompt_id")
        if not r["category"]:
            messages.append(f"WARNING: {score_path} row {i}: empty category")
        for s in SUBSCALES:
            require_int_range(score_path, i, s, r[s], 1, 10)

    for i, r in enumerate(recog, start=2):
        if r["true_author"] not in MODELS:
            raise ValueError(f"{recog_path} row {i}: unknown true_author {r['true_author']!r}")
        if r["predicted_author"] not in MODELS:
            raise ValueError(f"{recog_path} row {i}: unknown predicted_author {r['predicted_author']!r}")
        if not r["prompt_id"]:
            raise ValueError(f"{recog_path} row {i}: empty prompt_id")
        require_int_range(recog_path, i, "confidence", r["confidence"], 1, 5)

    self_rows = sum(1 for r in recog if r["true_author"] == judge)
    if strict and judge in MODELS and self_rows != EXPECTED_SELF_RECOG_ROWS:
        raise ValueError(f"{recog_path}: expected 30 self-recognition rows for {judge}, found {self_rows}")

    messages.append(
        f"OK {judge}: scores={len(scores)} conditions={dict(sorted(conds.items()))} "
        f"recognition={len(recog)} predicted={dict(sorted(Counter(r['predicted_author'] for r in recog).items()))}"
    )
    return messages


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judgments-dir", default="data/judgments", help="Directory containing per-judge judgment subdirectories")
    ap.add_argument("--require-all-judges", action="store_true", help="Fail unless all four expected judges are present")
    ap.add_argument("--strict", action="store_true", help="Enable additional expected-design checks")
    args = ap.parse_args()

    base = Path(args.judgments_dir)
    if not base.exists():
        raise SystemExit(f"Judgments directory not found: {base}")
    judge_dirs = sorted(p for p in base.iterdir() if p.is_dir())
    found = [p.name for p in judge_dirs]
    if args.require_all_judges and sorted(found) != sorted(MODELS):
        missing = sorted(set(MODELS) - set(found))
        extra = sorted(set(found) - set(MODELS))
        raise SystemExit(f"Expected all judges. Found={found}; missing={missing}; extra={extra}")

    failures = []
    for judge_dir in judge_dirs:
        try:
            for msg in validate_judge_dir(judge_dir, strict=args.strict):
                print(msg)
        except Exception as exc:  # collect all broken dirs before exiting
            failures.append(f"{judge_dir}: {exc}")

    if failures:
        print("\nFAILURES:")
        for f in failures:
            print(f"- {f}")
        raise SystemExit(1)
    print(f"Validated {len(judge_dirs)} judge directory/directories under {base}.")


if __name__ == "__main__":
    main()
