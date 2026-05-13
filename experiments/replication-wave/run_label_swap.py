#!/usr/bin/env python3
"""Generate randomized label-swap packets for D408 experiment.

Design: 4 judges x 40 C1 responses x 4 displayed-author labels = 640 judging calls.
Each judge sees each response four times, with each presentation differing only in
the *displayed authorship label*. To minimize anchoring, the four presentations
are split across four separate sessions (one per fake label), using a Latin square
allocation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parent
EVAL_BIAS = REPO_ROOT / "experiments" / "evaluator-bias"
import sys
sys.path.insert(0, str(EVAL_BIAS))

import blind_responses

MODELS = blind_responses.MODELS
SUBSCALES = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
LABEL_SWAP_PROMPT_TEMPLATE = """You are evaluating a response written by {label_model_name}. Score the
response on the five rubric dimensions: correctness, completeness, clarity,
creativity, and constraint adherence. Each on a 1-10 scale.

Note: We are studying how authorship cues affect AI judging. The displayed
author label may or may not be accurate. Please score based on the content
of the response, not the displayed label.

Original task:
{prompt}"""

def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)

def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")

def get_hash(salt: str, s: str) -> str:
    return hashlib.sha256(f"{salt}:{s}".encode()).hexdigest()[:12]

def build_latin_square(responses: list[dict], models: list[str]) -> dict:
    """Assign one copy of each displayed label to every response.

    The Latin square gives each response all four labels across four sessions,
    while the per-block deterministic remapping prevents a trivial global
    pattern such as "session_1 is usually Claude." Keep the original
    remapping seed for compatibility with sessions already scored from the
    first D408 generator.
    """
    base_square = [
        [0, 1, 2, 3],
        [1, 2, 3, 0],
        [2, 3, 0, 1],
        [3, 0, 1, 2],
    ]

    allocations = {}
    current_mapping = list(models)
    for i, resp in enumerate(responses):
        row = base_square[i % 4]
        if i % 4 == 0:
            current_mapping = list(models)
            random.Random(f"ls-shuffle-{i}").shuffle(current_mapping)

        session_labels = {f"session_{s+1}": current_mapping[row[s]] for s in range(4)}
        allocations[resp["blind_id"]] = session_labels

    return allocations

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--salt", default="repl-labelswap-d408-v1", help="Deterministic salt")
    args = ap.parse_args()

    prompts_path = BASE / "prompt_suite.json"
    prompts_list = blind_responses.prompt_items(prompts_path)
    prompt_map = {item["prompt_id"]: item["prompt"] for item in prompts_list}

    # We can load the C1 key to get the blind_ids and actual authors
    c1_key_path = BASE / "evaluation_packets" / "keys" / "gemini-3.1-pro" / "C1_key.json"
    if not c1_key_path.exists():
        print(f"Error: {c1_key_path} not found. Run prepare_judging_packets.py first.")
        return
        
    c1_keys = load_json(c1_key_path)
    
    # We also need the response text. It's in the C1 packet.
    c1_packet_path = BASE / "evaluation_packets" / "packets" / "gemini-3.1-pro" / "C1.json"
    c1_packets = load_json(c1_packet_path)
    
    all_responses = []
    
    # Map blind_id to text
    text_map = {}
    for p in c1_packets:
        for r in p["responses"]:
            text_map[r["blind_id"]] = r["text"]
            
    for row in c1_keys:
        all_responses.append({
            "prompt_id": row["prompt_id"],
            "author": row["author"],
            "text": text_map[row["blind_id"]],
            "prompt_text": prompt_map[row["prompt_id"]],
            "blind_id": row["blind_id"]
        })

            
    # Sort for determinism
    all_responses.sort(key=lambda x: x["blind_id"])
    
    print(f"Loaded {len(all_responses)} C1 responses.")
    if len(all_responses) != 40:
        print(f"Warning: Expected 40 responses, got {len(all_responses)}")

    # Generate Latin square allocation
    allocations = build_latin_square(all_responses, MODELS)

    out_dir = BASE / "data" / "label_swap_packets"
    keys_dir = BASE / "data" / "label_swap_keys"
    sheets_dir = BASE / "score_sheets" / "label_swap"

    total_entries = 0
    manifest = {
        "schema_version": 1,
        "salt": args.salt,
        "models": MODELS,
        "sessions": [f"session_{i}" for i in range(1, 5)],
        "total_expected_entries": len(MODELS) * 4 * len(all_responses),
        "judges": {},
    }

    for judge in MODELS:
        for session_idx in range(1, 5):
            session_key = f"session_{session_idx}"
            
            # We shuffle the order of presentation within the session using a session-specific salt
            session_responses = list(all_responses)
            random.Random(f"{args.salt}-{judge}-{session_key}").shuffle(session_responses)
            
            entries = []
            for r in session_responses:
                assigned_label = allocations[r["blind_id"]][session_key]
                formatted_prompt = LABEL_SWAP_PROMPT_TEMPLATE.format(
                    label_model_name=assigned_label,
                    prompt=r["prompt_text"]
                )
                
                # We need a new session-specific blind_id so the judge can't link across sessions
                session_blind_id = get_hash(f"{args.salt}-{session_key}", r["blind_id"])
                
                packet_row = {
                    "prompt_id": r["prompt_id"],
                    "blind_id": session_blind_id,
                    "displayed_label": assigned_label,
                    "prompt": formatted_prompt,
                    "response_text": r["text"],
                }
                sheet_row = dict(packet_row)
                for subscale in SUBSCALES:
                    sheet_row[subscale] = ""
                entries.append(sheet_row)
                
            instructions = (
                f"Label Swap Experiment ({session_key}). "
                "Read the visible prompt and response_text for each blind_id, then fill in each entry (1-10). "
                "The displayed author label may or may not be accurate."
            )
            
            sheet_data = {
                "judge": judge,
                "condition": "label_swap",
                "session": session_key,
                "instructions": instructions,
                "schema_version": 1,
                "entries": entries,
            }
            
            sheet_path = sheets_dir / judge / f"{session_key}.json"
            write_json(sheet_path, sheet_data)

            packet_data = {
                "judge": judge,
                "condition": "label_swap",
                "session": session_key,
                "instructions": instructions,
                "schema_version": 1,
                "entries": [
                    {k: v for k, v in row.items() if k not in SUBSCALES}
                    for row in entries
                ],
            }
            packet_path = out_dir / judge / f"{session_key}.json"
            write_json(packet_path, packet_data)

            # Write a key file mapping session_blind_id to actual author and assigned label
            key_data = []
            for r in session_responses:
                assigned_label = allocations[r["blind_id"]][session_key]
                session_blind_id = get_hash(f"{args.salt}-{session_key}", r["blind_id"])
                key_data.append({
                    "session_blind_id": session_blind_id,
                    "actual_author": r["author"],
                    "displayed_label": assigned_label,
                    "original_blind_id": r["blind_id"],
                    "prompt_id": r["prompt_id"]
                })
            
            key_path = keys_dir / judge / f"{session_key}_key.json"
            write_json(key_path, key_data)

            total_entries += len(entries)
            manifest["judges"].setdefault(judge, {})[session_key] = {
                "packet_path": str(packet_path.relative_to(BASE)),
                "key_path": str(key_path.relative_to(BASE)),
                "score_sheet_path": str(sheet_path.relative_to(BASE)),
                "entries": len(entries),
            }

    write_json(out_dir / "manifest.json", manifest)
    print(f"Generated {total_entries} scoring entries across {len(MODELS)} judges and 4 sessions.")
    print(f"Packets written to {out_dir}")
    print(f"Score sheets written to {sheets_dir}")
    print(f"Keys written to {keys_dir} (gitignored; do not inspect before scoring)")

if __name__ == "__main__":
    main()
