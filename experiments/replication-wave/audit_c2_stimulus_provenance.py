#!/usr/bin/env python3
"""Audit whether C2 score sheets match the current C2 source files.

The Day 407 replication wave has a known C2 provenance wrinkle: after the
initial C2 packets were generated, the Kimi-as-paraphraser source files were
replaced with Kimi's validated versions. This script compares the text actually present in
committed C2 score sheets against the current canonical paraphrase files and
writes a row-level hash/word-count audit.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

DEFAULT_JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
CSV_COLUMNS = [
    "judge",
    "prompt_id",
    "author",
    "current_source_path",
    "current_paraphraser",
    "sheet_sha256",
    "current_sha256",
    "sheet_word_count",
    "current_word_count",
    "match_status",
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def word_count(text: str) -> int:
    return len(text.split())


def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def key_map_for_judge(base: Path, judge: str) -> dict[str, dict]:
    key_path = base / "evaluation_packets" / "keys" / judge / "C2_key.json"
    key_rows = load_json(key_path)
    if not isinstance(key_rows, list):
        raise ValueError(f"Expected list in {key_path}, got {type(key_rows).__name__}")
    by_blind: dict[str, dict] = {}
    for row in key_rows:
        blind_id = row.get("blind_id")
        if not blind_id:
            raise ValueError(f"Key row without blind_id in {key_path}: {row}")
        if blind_id in by_blind:
            raise ValueError(f"Duplicate blind_id {blind_id!r} in {key_path}")
        by_blind[blind_id] = row
    return by_blind


def audit_judge(base: Path, judge: str) -> list[dict[str, object]]:
    sheet_path = base / "score_sheets" / judge / "C2.json"
    sheet = load_json(sheet_path)
    entries = sheet.get("entries")
    if not isinstance(entries, list):
        raise ValueError(f"Expected entries list in {sheet_path}")
    keys = key_map_for_judge(base, judge)

    rows: list[dict[str, object]] = []
    seen_blind: set[str] = set()
    for entry in entries:
        blind_id = entry.get("blind_id")
        if not blind_id:
            raise ValueError(f"Score-sheet entry without blind_id in {sheet_path}: {entry}")
        if blind_id in seen_blind:
            raise ValueError(f"Duplicate blind_id {blind_id!r} in {sheet_path}")
        seen_blind.add(blind_id)
        if blind_id not in keys:
            raise ValueError(f"Score-sheet blind_id {blind_id!r} missing from {base / 'evaluation_packets' / 'keys' / judge / 'C2_key.json'}")
        if "response_text" not in entry:
            raise ValueError(f"Score-sheet entry {blind_id!r} in {sheet_path} lacks response_text")

        key = keys[blind_id]
        author = key.get("author")
        paraphraser = key.get("paraphraser")
        prompt_id = entry.get("prompt_id")
        if prompt_id != key.get("prompt_id"):
            raise ValueError(
                f"Prompt mismatch for {judge} {blind_id}: sheet={prompt_id!r}, key={key.get('prompt_id')!r}"
            )
        if not author or not paraphraser or not prompt_id:
            raise ValueError(f"Incomplete key/sheet metadata for {judge} {blind_id}: key={key}, entry={entry}")

        rel_source = Path("paraphrased_responses") / paraphraser / f"{author}__prompt-{prompt_id}.json"
        source_path = base / rel_source
        source = load_json(source_path)
        if "paraphrased_response" not in source:
            raise ValueError(f"Source file lacks paraphrased_response: {source_path}")

        sheet_text = entry["response_text"]
        current_text = source["paraphrased_response"]
        if not isinstance(sheet_text, str) or not isinstance(current_text, str):
            raise ValueError(f"Non-string response text for {judge} {blind_id}")

        rows.append(
            {
                "judge": judge,
                "prompt_id": prompt_id,
                "author": author,
                "current_source_path": rel_source.as_posix(),
                "current_paraphraser": paraphraser,
                "sheet_sha256": sha256_text(sheet_text),
                "current_sha256": sha256_text(current_text),
                "sheet_word_count": word_count(sheet_text),
                "current_word_count": word_count(current_text),
                "match_status": "exact" if sheet_text == current_text else "mismatch",
            }
        )
    return rows


def write_csv(rows: list[dict[str, object]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def print_summary(rows: list[dict[str, object]]) -> None:
    status_counts = Counter(row["match_status"] for row in rows)
    by_judge: dict[str, Counter] = defaultdict(Counter)
    mismatch_by_paraphraser = Counter()
    for row in rows:
        by_judge[str(row["judge"])][str(row["match_status"])] += 1
        if row["match_status"] != "exact":
            mismatch_by_paraphraser[str(row["current_paraphraser"])] += 1

    print(f"rows: {len(rows)}")
    print("match_status:")
    for key in sorted(status_counts):
        print(f"  {key}: {status_counts[key]}")
    print("by judge:")
    for judge in sorted(by_judge):
        counts = by_judge[judge]
        print(f"  {judge}: exact={counts.get('exact', 0)} mismatch={counts.get('mismatch', 0)}")
    print("mismatches by current_paraphraser:")
    if mismatch_by_paraphraser:
        for paraphraser in sorted(mismatch_by_paraphraser):
            print(f"  {paraphraser}: {mismatch_by_paraphraser[paraphraser]}")
    else:
        print("  none")


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=script_dir, help="replication-wave directory")
    parser.add_argument("--judges", nargs="+", default=DEFAULT_JUDGES, help="judges whose C2 sheets should be audited")
    parser.add_argument(
        "--output",
        type=Path,
        default=script_dir / "results" / "c2_stimulus_sheet_audit.csv",
        help="CSV output path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base = args.base.resolve()
    rows: list[dict[str, object]] = []
    for judge in args.judges:
        rows.extend(audit_judge(base, judge))
    write_csv(rows, args.output)
    print_summary(rows)
    print(f"wrote: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
