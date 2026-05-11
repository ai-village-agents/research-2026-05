#!/usr/bin/env python3
"""score_collector.py — convert filled-in judge score sheets into the long-format
CSVs consumed by analysis/run_analysis.py.

Two-step workflow per judge × condition:

  1. EXPORT TEMPLATES: starting from the blinded packets written by
     `blind_responses.py`, this script writes a per-(judge, condition)
     scoring template (a JSON file) where the judge fills in one entry
     per blind_id.

       For C1, C2, C3 (scoring conditions) the template asks for the five
       subscale scores (1-10): correctness, completeness, clarity, creativity,
       constraint_adherence.

       For C4 (recognition probe) the template asks for predicted_author and
       confidence (1-5).

  2. INGEST FILLED TEMPLATES: this script reads the filled template along
     with the matching answer-key file written by blind_responses.py, joins
     them on blind_id, and appends rows to:

       results/long_scores.csv      (C1, C2, C3)
       results/long_recognition.csv (C4)

The CSV columns match the format expected by analysis/run_analysis.py.

This script is idempotent on a per-(judge, condition) basis. Re-ingesting
overwrites prior rows for the same (judge, condition) so judges can fix
mistakes and rerun without polluting the corpus.

USAGE
-----
Export template:
  python score_collector.py export --judge claude-opus-4.7 --condition C1
  python score_collector.py export --judge claude-opus-4.7 --condition C4

Ingest filled template:
  python score_collector.py ingest --judge claude-opus-4.7 --condition C1

By default templates live under:
  experiments/evaluator-bias/score_sheets/<judge>/<condition>.json

And the answer keys live under (created by blind_responses.py):
  experiments/evaluator-bias/evaluation_packets/keys/<judge>/<condition>_key.json
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REPO_ROOT = ROOT.parent.parent
PACKETS_DIR = ROOT / "evaluation_packets" / "packets"
KEYS_DIR = ROOT / "evaluation_packets" / "keys"
SHEETS_DIR = ROOT / "score_sheets"
RESULTS_DIR = REPO_ROOT / "results"
SCORES_CSV = RESULTS_DIR / "long_scores.csv"
RECOG_CSV = RESULTS_DIR / "long_recognition.csv"

MODELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
SCORING_CONDS = ("C1", "C2", "C3")
SUBSCALES = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
SCORES_HEADER = ["judge", "author", "prompt_id", "category", "condition"] + SUBSCALES
RECOG_HEADER = ["judge", "true_author", "predicted_author", "confidence", "prompt_id"]


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


# ----------------------------------------------------------------------
# EXPORT
# ----------------------------------------------------------------------

def export_template(judge: str, condition: str) -> Path:
    packet_path = PACKETS_DIR / judge / f"{condition}.json"
    if not packet_path.exists():
        raise SystemExit(
            f"Packet not found: {packet_path}\n"
            f"Run blind_responses.py first to generate evaluation packets."
        )
    packet = load_json(packet_path)

    entries: list[dict[str, Any]] = []
    for item in packet:
        for resp in item["responses"]:
            row: dict[str, Any] = {
                "prompt_id": item["prompt_id"],
                "blind_id": resp["blind_id"],
            }
            if condition == "C4":
                row["predicted_author"] = ""  # one of MODELS
                row["confidence"] = ""        # 1..5
            else:
                for s in SUBSCALES:
                    row[s] = ""  # 1..10
            entries.append(row)

    template = {
        "judge": judge,
        "condition": condition,
        "instructions": (
            "Fill in each entry. For C1/C2/C3: subscales are integers 1-10. "
            "For C4: predicted_author must be one of " + ", ".join(MODELS)
            + " and confidence is an integer 1-5."
        ),
        "schema_version": 1,
        "entries": entries,
    }
    out = SHEETS_DIR / judge / f"{condition}.json"
    write_json(out, template)
    return out


# ----------------------------------------------------------------------
# INGEST
# ----------------------------------------------------------------------

def _validate_score(name: str, value: Any) -> int:
    try:
        v = int(value)
    except (TypeError, ValueError) as e:
        raise SystemExit(f"Invalid {name}={value!r}; expected integer 1-10") from e
    if not 1 <= v <= 10:
        raise SystemExit(f"{name}={v} out of range 1-10")
    return v


def _validate_confidence(value: Any) -> int:
    try:
        v = int(value)
    except (TypeError, ValueError) as e:
        raise SystemExit(f"Invalid confidence={value!r}; expected integer 1-5") from e
    if not 1 <= v <= 5:
        raise SystemExit(f"confidence={v} out of range 1-5")
    return v


def _read_existing(path: Path, header: list[str]) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open() as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != header:
            raise SystemExit(
                f"{path} has unexpected columns:\n  got      {reader.fieldnames}\n  expected {header}"
            )
        return list(reader)


def _write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in header})


def ingest_filled(judge: str, condition: str) -> tuple[int, Path]:
    sheet_path = SHEETS_DIR / judge / f"{condition}.json"
    if not sheet_path.exists():
        raise SystemExit(f"Filled template not found: {sheet_path}")
    sheet = load_json(sheet_path)
    if sheet.get("judge") != judge or sheet.get("condition") != condition:
        raise SystemExit(
            f"Sheet judge/condition mismatch: header={sheet.get('judge')}/{sheet.get('condition')}"
            f" expected={judge}/{condition}"
        )

    key_path = KEYS_DIR / judge / f"{condition}_key.json"
    if not key_path.exists():
        raise SystemExit(f"Answer key not found: {key_path}")
    key_rows = load_json(key_path)
    key_by_id = {r["blind_id"]: r for r in key_rows}

    # Build a category map from prompt suite (so analysis has category column).
    prompts_path = ROOT / "prompt_suite.json"
    raw = load_json(prompts_path)
    items = raw if isinstance(raw, list) else raw.get("prompts", [])
    cat_by_pid = {p["id"]: p.get("category", "") for p in items}

    if condition in SCORING_CONDS:
        new_rows: list[dict[str, str]] = []
        for e in sheet["entries"]:
            bid = e["blind_id"]
            if bid not in key_by_id:
                raise SystemExit(f"Unknown blind_id in sheet: {bid}")
            k = key_by_id[bid]
            pid = e["prompt_id"]
            assert k["prompt_id"] == pid
            row = {
                "judge": judge,
                "author": k["author"],
                "prompt_id": pid,
                "category": cat_by_pid.get(pid, ""),
                "condition": condition.lower(),
            }
            for s in SUBSCALES:
                row[s] = str(_validate_score(s, e.get(s)))
            new_rows.append(row)

        existing = _read_existing(SCORES_CSV, SCORES_HEADER)
        # Drop prior rows for this (judge, condition).
        kept = [r for r in existing if not (r["judge"] == judge and r["condition"] == condition.lower())]
        combined = kept + new_rows
        _write_csv(SCORES_CSV, SCORES_HEADER, combined)
        return len(new_rows), SCORES_CSV

    if condition == "C4":
        new_rows: list[dict[str, str]] = []
        for e in sheet["entries"]:
            bid = e["blind_id"]
            if bid not in key_by_id:
                raise SystemExit(f"Unknown blind_id in sheet: {bid}")
            k = key_by_id[bid]
            pred = e.get("predicted_author")
            if pred not in MODELS:
                raise SystemExit(f"predicted_author={pred!r} not one of {MODELS} (blind_id={bid})")
            conf = _validate_confidence(e.get("confidence"))
            new_rows.append({
                "judge": judge,
                "true_author": k["author"],
                "predicted_author": pred,
                "confidence": str(conf),
                "prompt_id": k["prompt_id"],
            })
        existing = _read_existing(RECOG_CSV, RECOG_HEADER)
        kept = [r for r in existing if r["judge"] != judge]
        combined = kept + new_rows
        _write_csv(RECOG_CSV, RECOG_HEADER, combined)
        return len(new_rows), RECOG_CSV

    raise SystemExit(f"Unknown condition: {condition}")


# ----------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_exp = sub.add_parser("export", help="Write a blank score-sheet template.")
    p_exp.add_argument("--judge", required=True, choices=MODELS)
    p_exp.add_argument("--condition", required=True, choices=["C1", "C2", "C3", "C4"])

    p_ing = sub.add_parser("ingest", help="Read a filled template and append to results CSVs.")
    p_ing.add_argument("--judge", required=True, choices=MODELS)
    p_ing.add_argument("--condition", required=True, choices=["C1", "C2", "C3", "C4"])

    p_all = sub.add_parser("export-all", help="Export every (judge, condition) template.")

    args = ap.parse_args()

    if args.cmd == "export":
        out = export_template(args.judge, args.condition)
        print(f"Wrote template -> {out}")
    elif args.cmd == "ingest":
        n, out = ingest_filled(args.judge, args.condition)
        print(f"Ingested {n} rows -> {out}")
    elif args.cmd == "export-all":
        for j in MODELS:
            for c in ["C1", "C2", "C3", "C4"]:
                try:
                    out = export_template(j, c)
                    print(f"  {j:18s} {c}: {out.relative_to(REPO_ROOT)}")
                except SystemExit as e:
                    print(f"  {j:18s} {c}: SKIP ({e})")


if __name__ == "__main__":
    main()
