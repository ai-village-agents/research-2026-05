#!/usr/bin/env python3
"""Collect filled replication-wave score sheets into CSV results.

This mirrors the original study's score_collector.py, but all inputs and outputs
live under experiments/replication-wave/ so the replication data remain separate.

Workflow after prepare_judging_packets.py has produced packets and blank sheets:

  1. A judge fills experiments/replication-wave/score_sheets/<judge>/<condition>.json.
  2. Ingest one filled sheet:
       python3 experiments/replication-wave/score_collector.py ingest --judge gpt-5.5 --condition C1
  3. Or ingest all currently filled sheets:
       python3 experiments/replication-wave/score_collector.py ingest-all

Outputs:
  experiments/replication-wave/results/long_scores.csv       (C1/C2/C3)
  experiments/replication-wave/results/long_recognition.csv  (C4)
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
PACKETS_DIR = ROOT / "evaluation_packets" / "packets"
KEYS_DIR = ROOT / "evaluation_packets" / "keys"
SHEETS_DIR = ROOT / "score_sheets"
RESULTS_DIR = ROOT / "results"
SCORES_CSV = RESULTS_DIR / "long_scores.csv"
RECOG_CSV = RESULTS_DIR / "long_recognition.csv"

MODELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
SCORING_CONDS = ("C1", "C2", "C3")
ALL_CONDS = SCORING_CONDS + ("C4",)
SUBSCALES = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
SCORES_HEADER = ["judge", "author", "prompt_id", "category", "condition"] + SUBSCALES
RECOG_HEADER = ["judge", "true_author", "predicted_author", "confidence", "prompt_id"]


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def _validate_int(name: str, value: Any, lo: int, hi: int) -> int:
    try:
        v = int(value)
    except (TypeError, ValueError) as e:
        raise SystemExit(f"Invalid {name}={value!r}; expected integer {lo}-{hi}") from e
    if not lo <= v <= hi:
        raise SystemExit(f"{name}={v} out of range {lo}-{hi}")
    return v


def _read_existing(path: Path, header: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != header:
            raise SystemExit(f"{path} has unexpected columns: got {reader.fieldnames}, expected {header}")
        return list(reader)


def _write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in header})


def _category_by_prompt() -> dict[str, str]:
    raw = load_json(ROOT / "prompt_suite.json")
    items = raw if isinstance(raw, list) else raw.get("prompts", [])
    out = {}
    for item in items:
        pid = item.get("prompt_id") or item.get("id")
        if pid:
            out[pid] = item.get("category", "")
    return out


def _load_sheet_and_key(judge: str, condition: str) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    sheet_path = SHEETS_DIR / judge / f"{condition}.json"
    key_path = KEYS_DIR / judge / f"{condition}_key.json"
    packet_path = PACKETS_DIR / judge / f"{condition}.json"
    for path in (sheet_path, key_path, packet_path):
        if not path.exists():
            raise SystemExit(f"Required file not found: {path}")
    sheet = load_json(sheet_path)
    if sheet.get("judge") != judge or sheet.get("condition") != condition:
        raise SystemExit(
            f"Sheet header mismatch for {sheet_path}: got {sheet.get('judge')}/{sheet.get('condition')}, "
            f"expected {judge}/{condition}"
        )
    key_rows = load_json(key_path)
    key_by_id = {row["blind_id"]: row for row in key_rows}
    if len(key_by_id) != len(key_rows):
        raise SystemExit(f"Duplicate blind_id in key: {key_path}")
    return sheet, key_by_id


def ingest_filled(judge: str, condition: str) -> tuple[int, Path]:
    sheet, key_by_id = _load_sheet_and_key(judge, condition)
    entries = sheet.get("entries", [])
    if len(entries) != len(key_by_id):
        raise SystemExit(f"Entry/key count mismatch for {judge} {condition}: entries={len(entries)} keys={len(key_by_id)}")
    cat_by_pid = _category_by_prompt()

    seen_ids: set[str] = set()
    if condition in SCORING_CONDS:
        new_rows: list[dict[str, str]] = []
        for entry in entries:
            bid = entry.get("blind_id")
            if bid in seen_ids:
                raise SystemExit(f"Duplicate blind_id in sheet: {bid}")
            seen_ids.add(bid)
            if bid not in key_by_id:
                raise SystemExit(f"Unknown blind_id in sheet: {bid}")
            key = key_by_id[bid]
            pid = entry.get("prompt_id")
            if key["prompt_id"] != pid:
                raise SystemExit(f"Prompt mismatch for {bid}: sheet {pid}, key {key['prompt_id']}")
            row = {
                "judge": judge,
                "author": key["author"],
                "prompt_id": pid,
                "category": cat_by_pid.get(pid, ""),
                "condition": condition.lower(),
            }
            for subscale in SUBSCALES:
                row[subscale] = str(_validate_int(subscale, entry.get(subscale), 1, 10))
            new_rows.append(row)
        existing = _read_existing(SCORES_CSV, SCORES_HEADER)
        kept = [r for r in existing if not (r["judge"] == judge and r["condition"] == condition.lower())]
        _write_csv(SCORES_CSV, SCORES_HEADER, kept + new_rows)
        return len(new_rows), SCORES_CSV

    if condition == "C4":
        new_rows: list[dict[str, str]] = []
        for entry in entries:
            bid = entry.get("blind_id")
            if bid in seen_ids:
                raise SystemExit(f"Duplicate blind_id in sheet: {bid}")
            seen_ids.add(bid)
            if bid not in key_by_id:
                raise SystemExit(f"Unknown blind_id in sheet: {bid}")
            pred = entry.get("predicted_author")
            if pred not in MODELS:
                raise SystemExit(f"predicted_author={pred!r} not one of {MODELS} (blind_id={bid})")
            conf = _validate_int("confidence", entry.get("confidence"), 1, 5)
            key = key_by_id[bid]
            new_rows.append({
                "judge": judge,
                "true_author": key["author"],
                "predicted_author": pred,
                "confidence": str(conf),
                "prompt_id": key["prompt_id"],
            })
        existing = _read_existing(RECOG_CSV, RECOG_HEADER)
        kept = [r for r in existing if r["judge"] != judge]
        _write_csv(RECOG_CSV, RECOG_HEADER, kept + new_rows)
        return len(new_rows), RECOG_CSV

    raise SystemExit(f"Unknown condition: {condition}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_ing = sub.add_parser("ingest", help="Read one filled template and update replication CSVs.")
    p_ing.add_argument("--judge", required=True, choices=MODELS)
    p_ing.add_argument("--condition", required=True, choices=ALL_CONDS)

    sub.add_parser("ingest-all", help="Ingest all judge × condition sheets that currently exist.")
    args = ap.parse_args()

    if args.cmd == "ingest":
        n, path = ingest_filled(args.judge, args.condition)
        print(f"Ingested {n} rows -> {path.relative_to(ROOT)}")
        return

    if args.cmd == "ingest-all":
        total = 0
        for judge in MODELS:
            for condition in ALL_CONDS:
                sheet = SHEETS_DIR / judge / f"{condition}.json"
                if not sheet.exists():
                    continue
                n, path = ingest_filled(judge, condition)
                total += n
                print(f"{judge:18s} {condition}: {n:3d} rows -> {path.relative_to(ROOT)}")
        print(f"Total rows ingested: {total}")


if __name__ == "__main__":
    main()
