#!/usr/bin/env python3
"""Validate the quality-balanced follow-up wave inputs.

By default this checks the prompt suite and reports response coverage. Use
`--require-complete` once all four authors have written responses and before
building blind packets.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
MODELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def response_path(model: str, prompt_id: str) -> Path:
    return ROOT / "responses" / model / f"{prompt_id}.json"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--require-complete", action="store_true")
    args = ap.parse_args()

    raw = load_json(ROOT / "prompt_suite.json")
    prompts = raw.get("prompts", [])
    ids = [p.get("id") for p in prompts]
    if len(prompts) != 8:
        raise SystemExit(f"Expected 8 prompts, found {len(prompts)}")
    if any(not pid for pid in ids) or len(set(ids)) != len(ids):
        raise SystemExit(f"Prompt IDs missing or duplicated: {ids}")
    for p in prompts:
        for key in ("id", "category", "difficulty", "text"):
            if not p.get(key):
                raise SystemExit(f"Prompt {p.get('id')} missing {key}")

    missing: list[str] = []
    counts: dict[str, int] = {}
    for model in MODELS:
        n = 0
        for pid in ids:
            path = response_path(model, pid)
            if not path.exists():
                missing.append(f"{model}/{pid}")
                continue
            obj = load_json(path)
            resp = obj.get("response")
            if not isinstance(resp, str) or not resp.strip():
                raise SystemExit(f"Missing non-empty response in {path}")
            n += 1
        counts[model] = n

    print("Quality-balanced wave validation")
    print("prompt_count", len(prompts))
    print("response_counts", counts)
    if missing:
        print("missing_count", len(missing))
        for item in missing[:32]:
            print("missing", item)
        if len(missing) > 32:
            print(f"... {len(missing)-32} more missing")
        if args.require_complete:
            raise SystemExit("Quality-balanced responses incomplete")
    else:
        print("all responses complete")


if __name__ == "__main__":
    main()
