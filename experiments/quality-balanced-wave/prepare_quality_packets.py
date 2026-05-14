#!/usr/bin/env python3
"""Build blind C1 scoring packets and optional C4 recognition packets.

Run only after all four authors have responses:

  python3 experiments/quality-balanced-wave/validate_quality_wave.py --require-complete
  python3 experiments/quality-balanced-wave/prepare_quality_packets.py --conditions C1 C4

Generated `evaluation_packets/` and `score_sheets/` are intentionally gitignored.
The key files reveal true authors and should not be inspected until after native
scoring is complete.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
MODELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
SUBSCALES = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


def blind_id(salt: str, judge: str, condition: str, prompt_id: str, author: str) -> str:
    seed = f"{salt}|{judge}|{condition}|{prompt_id}|{author}".encode()
    return "qb_" + hashlib.sha256(seed).hexdigest()[:12]


def load_prompts() -> list[dict[str, str]]:
    raw = load_json(ROOT / "prompt_suite.json")
    return [
        {
            "prompt_id": p["id"],
            "category": p.get("category", ""),
            "prompt": p["text"],
        }
        for p in raw.get("prompts", [])
    ]


def load_response(author: str, prompt_id: str) -> str:
    path = ROOT / "responses" / author / f"{prompt_id}.json"
    if not path.exists():
        raise SystemExit(f"Missing response: {path}")
    obj = load_json(path)
    resp = obj.get("response")
    if not isinstance(resp, str) or not resp.strip():
        raise SystemExit(f"Empty response: {path}")
    return resp


def build_packet(judge: str, condition: str, prompts: list[dict[str, str]], salt: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rng = random.Random(f"{salt}|{judge}|{condition}")
    packets: list[dict[str, Any]] = []
    keys: list[dict[str, Any]] = []
    for p in prompts:
        entries = []
        for author in MODELS:
            bid = blind_id(salt, judge, condition, p["prompt_id"], author)
            entries.append({"blind_id": bid, "author": author, "text": load_response(author, p["prompt_id"])})
        rng.shuffle(entries)
        packets.append({
            "judge_model": judge,
            "condition": condition,
            "prompt_id": p["prompt_id"],
            "category": p["category"],
            "prompt": p["prompt"],
            "responses": [{"blind_id": e["blind_id"], "text": e["text"]} for e in entries],
        })
        for e in entries:
            keys.append({
                "judge_model": judge,
                "condition": condition,
                "prompt_id": p["prompt_id"],
                "blind_id": e["blind_id"],
                "author": e["author"],
                "dataset": "quality_balanced_original",
            })
    return packets, keys


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
            if condition == "C1":
                for subscale in SUBSCALES:
                    row[subscale] = ""
            elif condition == "C4":
                row["predicted_author"] = ""
                row["confidence"] = ""
            else:
                raise ValueError(condition)
            entries.append(row)
    instructions = (
        "Native in-context judging only. Do not use codex/eval wrappers. "
        "Do not inspect evaluation_packets/keys until after all scoring/recognition is done. "
        "For C1, fill each rubric dimension with an integer 1-10. "
        "For C4, predict one of: " + ", ".join(MODELS) + "; confidence is 1-5."
    )
    write_json(out_path, {
        "judge": judge,
        "condition": condition,
        "study": "quality-balanced-wave",
        "schema_version": 1,
        "instructions": instructions,
        "entries": entries,
    })
    return len(entries)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--salt", default="quality-balanced-d408-v1")
    ap.add_argument("--conditions", nargs="+", choices=["C1", "C4"], default=["C1", "C4"])
    args = ap.parse_args()

    prompts = load_prompts()
    manifest: dict[str, Any] = {
        "salt_version": args.salt,
        "models": MODELS,
        "conditions": args.conditions,
        "n_prompts_total": len(prompts),
        "outputs": [],
    }
    for judge in MODELS:
        for condition in args.conditions:
            packets, keys = build_packet(judge, condition, prompts, args.salt)
            packet_path = ROOT / "evaluation_packets" / "packets" / judge / f"{condition}.json"
            key_path = ROOT / "evaluation_packets" / "keys" / judge / f"{condition}_key.json"
            sheet_path = ROOT / "score_sheets" / judge / f"{condition}.json"
            write_json(packet_path, packets)
            write_json(key_path, keys)
            n_entries = export_score_sheet(packet_path, sheet_path, judge, condition)
            manifest["outputs"].append({
                "judge": judge,
                "condition": condition,
                "packet": str(packet_path.relative_to(ROOT)),
                "key": str(key_path.relative_to(ROOT)),
                "score_sheet": str(sheet_path.relative_to(ROOT)),
                "n_prompts": len(packets),
                "n_responses": sum(len(p["responses"]) for p in packets),
                "n_sheet_entries": n_entries,
            })
    write_json(ROOT / "evaluation_packets" / "manifest.json", manifest)
    print(f"Wrote quality-balanced packets and score sheets under {ROOT}")
    for row in manifest["outputs"]:
        print(f"{row['judge']:18s} {row['condition']} prompts={row['n_prompts']:2d} responses={row['n_responses']:3d} sheet_entries={row['n_sheet_entries']:3d}")


if __name__ == "__main__":
    main()
