#!/usr/bin/env python3
"""Prepare blinded packets and blank score sheets for the replication wave.

This is a thin wrapper around the main study's blinding logic. It writes all
replication outputs under experiments/replication-wave/ so the OOD replication
can be judged and ingested separately from the original D405/D406 dataset.

Typical full run, after validate_replication_wave.py --require-complete passes:

  python3 experiments/replication-wave/prepare_judging_packets.py \
    --salt repl-day407-v1 \
    --conditions C1 C2 C3 C4

Before C2 is complete, use --conditions C1 C3 C4 to dry-run original/recognition
packetization without creating partial C2 sheets.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
EVAL_BIAS = REPO_ROOT / "experiments" / "evaluator-bias"
sys.path.insert(0, str(EVAL_BIAS))

import blind_responses  # noqa: E402

MODELS = blind_responses.MODELS
SCORING_CONDS = {"C1", "C2", "C3"}
SUBSCALES = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
C3_WARNING = (
    "Bias-warning condition: before scoring, make an active effort not to favor "
    "responses you suspect were written by yourself or by any familiar model family. "
    "Score only the response quality relative to the prompt."
)


def prompt_for_condition(prompt: str, condition: str) -> str:
    """Return the judge-visible prompt for a condition."""
    if condition == "C3":
        return f"{C3_WARNING}\n\nOriginal task:\n{prompt}"
    return prompt


def apply_condition_overlays(packets: list[dict[str, Any]], condition: str) -> list[dict[str, Any]]:
    """Apply replication-specific visible instructions after shared blinding."""
    if condition != "C3":
        return packets
    overlaid: list[dict[str, Any]] = []
    for item in packets:
        updated = dict(item)
        updated["prompt"] = prompt_for_condition(str(item.get("prompt", "")), condition)
        overlaid.append(updated)
    return overlaid


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def export_score_sheet(packet_path: Path, out_path: Path, judge: str, condition: str) -> int:
    packet = load_json(packet_path)
    entries: list[dict[str, Any]] = []
    for item in packet:
        for resp in item["responses"]:
            row: dict[str, Any] = {
                "prompt_id": item["prompt_id"],
                "category": item.get("category", ""),
                "prompt": item.get("prompt", ""),
                "blind_id": resp["blind_id"],
                "response_text": resp.get("text", ""),
            }
            if condition in SCORING_CONDS:
                for subscale in SUBSCALES:
                    row[subscale] = ""
            elif condition == "C4":
                row["predicted_author"] = ""
                row["confidence"] = ""
            else:
                raise ValueError(f"Unknown condition: {condition}")
            entries.append(row)

    instructions = (
        "Read the visible prompt and response_text for each blind_id, then fill in each entry. "
        "Do not inspect evaluation_packets/keys until after submitting scores. "
        "For C1/C2/C3: subscales are integers 1-10. "
        "For C3 specifically, the visible prompt begins with a bias-warning instruction; apply it while scoring. "
        "For C4: predicted_author must be one of " + ", ".join(MODELS)
        + " and confidence is an integer 1-5. Run C4 last if included."
    )
    write_json(out_path, {
        "judge": judge,
        "condition": condition,
        "instructions": instructions,
        "schema_version": 1,
        "entries": entries,
    })
    return len(entries)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--salt", default="repl-day407-v1", help="Deterministic blinding salt/version")
    ap.add_argument("--conditions", nargs="+", choices=blind_responses.CONDITIONS, default=blind_responses.CONDITIONS)
    ap.add_argument("--allow-partial", action="store_true", help="Allow incomplete C2 packetization for dry runs only")
    args = ap.parse_args()

    out = BASE / "evaluation_packets"
    prompts = blind_responses.prompt_items(BASE / "prompt_suite.json")
    manifest = {
        "salt_version": args.salt,
        "models": MODELS,
        "conditions": args.conditions,
        "n_prompts_total": len(prompts),
        "allow_partial": args.allow_partial,
        "outputs": [],
    }

    for judge in MODELS:
        for condition in args.conditions:
            packets, key_rows = blind_responses.build_condition_for_judge(
                BASE, prompts, judge, condition, args.salt, args.allow_partial
            )
            packets = apply_condition_overlays(packets, condition)
            packet_path = out / "packets" / judge / f"{condition}.json"
            key_path = out / "keys" / judge / f"{condition}_key.json"
            write_json(packet_path, packets)
            write_json(key_path, key_rows)
            sheet_path = BASE / "score_sheets" / judge / f"{condition}.json"
            n_entries = export_score_sheet(packet_path, sheet_path, judge, condition)
            manifest["outputs"].append({
                "judge": judge,
                "condition": condition,
                "packet": str(packet_path.relative_to(BASE)),
                "key": str(key_path.relative_to(BASE)),
                "score_sheet": str(sheet_path.relative_to(BASE)),
                "n_prompts": len(packets),
                "n_responses": sum(len(p["responses"]) for p in packets),
                "n_sheet_entries": n_entries,
            })

    write_json(out / "manifest.json", manifest)
    print(f"Wrote replication packets and score sheets under {BASE}")
    for row in manifest["outputs"]:
        print(
            f"{row['judge']:18s} {row['condition']} "
            f"prompts={row['n_prompts']:2d} responses={row['n_responses']:3d} "
            f"sheet_entries={row['n_sheet_entries']:3d}"
        )


if __name__ == "__main__":
    main()
