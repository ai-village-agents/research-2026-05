#!/usr/bin/env python3
"""
Blind and shuffle LLM responses for cross-model evaluation.
Usage: python3 blind_responses.py --input-dir responses/ --output-file blinded.json
"""
import argparse
import json
import os
import random
import hashlib
from pathlib import Path

def load_responses(input_dir):
    """Load all response files from directory."""
    responses = []
    for f in Path(input_dir).glob("*.json"):
        with open(f) as fh:
            data = json.load(fh)
            data["_source_file"] = str(f)
            responses.append(data)
    return responses

def blind_responses(responses, seed=42):
    """Strip identifying metadata and assign random IDs."""
    rng = random.Random(seed)
    blinded = []
    for r in responses:
        blind_id = hashlib.sha256(f"{r['model']}-{r['prompt_id']}-{seed}".encode()).hexdigest()[:12]
        blinded.append({
            "blind_id": blind_id,
            "prompt_id": r["prompt_id"],
            "response": r["response"],
            "_true_model": r["model"]  # kept for later unblinding
        })
    rng.shuffle(blinded)
    return blinded

def save_blinded(blinded, output_file, include_key=False):
    """Save blinded set. Optionally include unblinding key."""
    output = {"responses": [{k: v for k, v in b.items() if not k.startswith("_")} for b in blinded]}
    with open(output_file, "w") as f:
        json.dump(output, f, indent=2)
    
    if include_key:
        key_file = output_file.replace(".json", "_key.json")
        key = {b["blind_id"]: b["_true_model"] for b in blinded}
        with open(key_file, "w") as f:
            json.dump(key, f, indent=2)
        print(f"Saved unblinding key to {key_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-file", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--include-key", action="store_true")
    args = parser.parse_args()
    
    responses = load_responses(args.input_dir)
    blinded = blind_responses(responses, seed=args.seed)
    save_blinded(blinded, args.output_file, include_key=args.include_key)
    print(f"Blinded {len(blinded)} responses -> {args.output_file}")
