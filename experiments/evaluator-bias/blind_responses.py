#!/usr/bin/env python3
"""Create blinded evaluation packets for C1-C4.

Outputs are written under `evaluation_packets/`:
  - packets/<judge>/<condition>.json: what the judge may see.
  - keys/<judge>/<condition>_key.json: answer key for analysis only.

The visible packets never include true author names. C1/C3/C4 use original
responses. C2 uses the round-robin paraphrased responses, preserving the original
author in the hidden key. Blind IDs are deterministic for reproducibility but are
salted by judge, condition, prompt, and author so they cannot be linked across
conditions or judges.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any

MODELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
CONDITIONS = ["C1", "C2", "C3", "C4"]
CONDITION_DATASET = {"C1": "original", "C2": "paraphrased", "C3": "original", "C4": "original"}


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def prompt_items(prompt_suite_path: Path) -> list[dict[str, str]]:
    raw = load_json(prompt_suite_path)
    items = raw if isinstance(raw, list) else raw.get("prompts", [])
    out = []
    for item in items:
        pid = item.get("prompt_id") or item.get("id")
        if not pid:
            raise ValueError(f"Prompt item missing id/prompt_id: {item}")
        out.append({
            "prompt_id": pid,
            "category": item.get("category", ""),
            "prompt": item.get("prompt") or item.get("text") or "",
        })
    return out


def blind_id(judge: str, condition: str, prompt_id: str, author: str, salt: str) -> str:
    seed = f"{salt}|{judge}|{condition}|{prompt_id}|{author}".encode()
    return "r_" + hashlib.sha256(seed).hexdigest()[:12]


def original_response(base: Path, author: str, prompt_id: str) -> str | None:
    path = base / "responses" / author / f"prompt-{prompt_id}.json"
    if not path.exists():
        return None
    return load_json(path).get("response")


def paraphrased_response(base: Path, author: str, prompt_id: str) -> tuple[str, str] | None:
    """Return (paraphrased text, paraphraser) for a given original author/prompt."""
    root = base / "paraphrased_responses"
    matches = sorted(root.glob(f"*/{author}__prompt-{prompt_id}.json"))
    if not matches:
        return None
    if len(matches) > 1:
        raise RuntimeError(f"Multiple paraphrases found for {author} {prompt_id}: {matches}")
    obj = load_json(matches[0])
    return obj.get("paraphrased_response", ""), obj.get("paraphraser", matches[0].parent.name)


def load_response(base: Path, dataset: str, author: str, prompt_id: str) -> dict[str, Any] | None:
    if dataset == "original":
        text = original_response(base, author, prompt_id)
        if text is None:
            return None
        return {"text": text, "paraphraser": None}
    got = paraphrased_response(base, author, prompt_id)
    if got is None:
        return None
    text, paraphraser = got
    return {"text": text, "paraphraser": paraphraser}


def complete_prompt_ids(base: Path, prompts: list[dict[str, str]], condition: str, allow_partial: bool) -> list[str]:
    dataset = CONDITION_DATASET[condition]
    complete = []
    missing: list[str] = []
    for p in prompts:
        pid = p["prompt_id"]
        absent = [m for m in MODELS if load_response(base, dataset, m, pid) is None]
        if absent:
            missing.append(f"{condition} {pid}: {', '.join(absent)}")
        else:
            complete.append(pid)
    if missing and not allow_partial:
        preview = "\n  ".join(missing[:25])
        more = "" if len(missing) <= 25 else f"\n  ... {len(missing)-25} more"
        raise SystemExit(f"Missing source texts; rerun with --allow-partial to packetize complete prompts only:\n  {preview}{more}")
    return complete


def build_condition_for_judge(base: Path, prompts: list[dict[str, str]], judge: str, condition: str, salt: str, allow_partial: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    by_id = {p["prompt_id"]: p for p in prompts}
    usable = complete_prompt_ids(base, prompts, condition, allow_partial)
    rng = random.Random(f"{salt}|{judge}|{condition}")
    packets: list[dict[str, Any]] = []
    key_rows: list[dict[str, Any]] = []
    dataset = CONDITION_DATASET[condition]

    for pid in usable:
        entries = []
        for author in MODELS:
            loaded = load_response(base, dataset, author, pid)
            assert loaded is not None
            bid = blind_id(judge, condition, pid, author, salt)
            entries.append({
                "blind_id": bid,
                "text": loaded["text"],
                "author": author,
                "paraphraser": loaded["paraphraser"],
            })
        rng.shuffle(entries)
        packet_responses = [{"blind_id": e["blind_id"], "text": e["text"]} for e in entries]
        packets.append({
            "judge_model": judge,
            "condition": condition,
            "prompt_id": pid,
            "category": by_id[pid].get("category", ""),
            "prompt": by_id[pid]["prompt"],
            "responses": packet_responses,
        })
        for e in entries:
            key_rows.append({
                "judge_model": judge,
                "condition": condition,
                "prompt_id": pid,
                "blind_id": e["blind_id"],
                "author": e["author"],
                "dataset": dataset,
                "paraphraser": e["paraphraser"],
            })
    return packets, key_rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=Path(__file__).parent, type=Path)
    ap.add_argument("--out", default=None, help="Output directory; default <base>/evaluation_packets")
    ap.add_argument("--salt", default="day405-v1", help="Deterministic blinding salt/version")
    ap.add_argument(
        "--conditions",
        nargs="+",
        choices=CONDITIONS,
        default=CONDITIONS,
        help="Conditions to packetize; e.g. --conditions C1 C3 C4 allows original/recognition packets before C2 paraphrases are complete",
    )
    ap.add_argument("--allow-partial", action="store_true", help="Emit packets for prompts with all required texts, even if corpus is incomplete")
    args = ap.parse_args()

    base = args.base
    out = Path(args.out) if args.out else base / "evaluation_packets"
    packets_dir = out / "packets"
    keys_dir = out / "keys"
    packets_dir.mkdir(parents=True, exist_ok=True)
    keys_dir.mkdir(parents=True, exist_ok=True)

    prompts = prompt_items(base / "prompt_suite.json")
    manifest = {
        "salt_version": args.salt,
        "models": MODELS,
        "conditions": args.conditions,
        "n_prompts_total": len(prompts),
        "allow_partial": args.allow_partial,
        "outputs": [],
    }

    for judge in MODELS:
        (packets_dir / judge).mkdir(parents=True, exist_ok=True)
        (keys_dir / judge).mkdir(parents=True, exist_ok=True)
        for condition in args.conditions:
            packets, key_rows = build_condition_for_judge(base, prompts, judge, condition, args.salt, args.allow_partial)
            packet_path = packets_dir / judge / f"{condition}.json"
            key_path = keys_dir / judge / f"{condition}_key.json"
            packet_path.write_text(json.dumps(packets, ensure_ascii=False, indent=2) + "\n")
            key_path.write_text(json.dumps(key_rows, ensure_ascii=False, indent=2) + "\n")
            manifest["outputs"].append({
                "judge": judge,
                "condition": condition,
                "packet": str(packet_path.relative_to(out)),
                "key": str(key_path.relative_to(out)),
                "n_prompts": len(packets),
                "n_responses": sum(len(p["responses"]) for p in packets),
            })
    (out / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Wrote blinded evaluation packets to {out}")
    for row in manifest["outputs"]:
        print(f"{row['judge']:18s} {row['condition']} prompts={row['n_prompts']:2d} responses={row['n_responses']:3d}")


if __name__ == "__main__":
    main()
