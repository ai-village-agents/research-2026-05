#!/usr/bin/env python3
"""Validate current replication-wave artifacts.

Checks prompt coverage, C1 response schema, paraphrase assignment balance, C2 schema,
and the ±15% source-word-count rule for paraphrases whose source file exists.
By default this is a progress validator: missing Kimi files are reported but do not
fail unless --require-complete is passed.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

MODELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
BASE = Path(__file__).resolve().parent


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - progress diagnostics
        raise AssertionError(f"invalid JSON {path}: {exc}") from exc


def word_count(text: str) -> int:
    return len(text.split())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--require-complete", action="store_true",
                    help="fail if any expected response/paraphrase is missing")
    args = ap.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    prompts = load_json(BASE / "prompt_suite.json")
    if isinstance(prompts, dict) and "prompts" in prompts:
        prompt_rows = prompts["prompts"]
    else:
        prompt_rows = prompts
    prompt_ids = [p.get("prompt_id") or p.get("id") for p in prompt_rows]
    if any(pid is None for pid in prompt_ids) or len(prompt_ids) != 10 or len(set(prompt_ids)) != 10:
        errors.append(f"expected 10 unique prompt ids, found {len(prompt_ids)} / {len(set(prompt_ids))}")

    # C1 responses.
    response_counts = {}
    for model in MODELS:
        present = []
        for pid in prompt_ids:
            path = BASE / "responses" / model / f"prompt-{pid}.json"
            if not path.exists():
                warnings.append(f"missing C1 response: {path.relative_to(BASE)}")
                continue
            data = load_json(path)
            if set(data) != {"response"}:
                errors.append(f"C1 schema should be exactly {{'response'}}: {path.relative_to(BASE)} has {sorted(data)}")
            elif not isinstance(data["response"], str) or not data["response"].strip():
                errors.append(f"empty C1 response: {path.relative_to(BASE)}")
            else:
                present.append(pid)
        response_counts[model] = len(present)

    # Assignment balance.
    assignment_path = BASE / "paraphrase_assignment.csv"
    rows = list(csv.DictReader(assignment_path.open(newline="")))
    required_cols = {"prompt_id", "author_model", "paraphraser_model"}
    if set(rows[0]) != required_cols:
        errors.append(f"assignment columns should be {sorted(required_cols)}, found {sorted(rows[0])}")
    if len(rows) != 40:
        errors.append(f"expected 40 assignment rows, found {len(rows)}")
    if any(r["author_model"] == r["paraphraser_model"] for r in rows):
        errors.append("assignment contains self-paraphrase rows")
    author_counts = Counter(r["author_model"] for r in rows)
    paraphraser_counts = Counter(r["paraphraser_model"] for r in rows)
    if any(author_counts[m] != 10 for m in MODELS):
        errors.append(f"author assignment counts not all 10: {dict(author_counts)}")
    if any(paraphraser_counts[m] != 10 for m in MODELS):
        errors.append(f"paraphraser assignment counts not all 10: {dict(paraphraser_counts)}")

    # C2 paraphrases for assigned rows.
    expected_c2_paths = set()
    paraphrase_counts = Counter()
    available_validated = 0
    missing_paraphrases = []
    by_paraphraser_missing = defaultdict(list)
    for r in rows:
        pid = r["prompt_id"]
        author = r["author_model"]
        paraphraser = r["paraphraser_model"]
        src = BASE / "responses" / author / f"prompt-{pid}.json"
        dst = BASE / "paraphrased_responses" / paraphraser / f"{author}__prompt-{pid}.json"
        expected_c2_paths.add(dst)
        if not dst.exists():
            missing_paraphrases.append(dst.relative_to(BASE))
            by_paraphraser_missing[paraphraser].append(f"{author}/{pid}")
            continue
        paraphrase_counts[paraphraser] += 1
        data = load_json(dst)
        expected_keys = {"prompt_id", "original_author", "paraphraser", "paraphrased_response", "word_count"}
        if set(data) != expected_keys:
            errors.append(f"C2 schema mismatch: {dst.relative_to(BASE)} has {sorted(data)}")
            continue
        if data["prompt_id"] != pid or data["original_author"] != author or data["paraphraser"] != paraphraser:
            errors.append(f"C2 metadata mismatch: {dst.relative_to(BASE)}")
        text = data.get("paraphrased_response")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"empty C2 paraphrase: {dst.relative_to(BASE)}")
            continue
        wc = word_count(text)
        if data.get("word_count") != wc:
            errors.append(f"C2 word_count mismatch: {dst.relative_to(BASE)} stored={data.get('word_count')} computed={wc}")
        if src.exists():
            source_text = load_json(src).get("response", "")
            sw = word_count(source_text)
            ratio = wc / sw if sw else 0.0
            if not (0.85 <= ratio <= 1.15):
                errors.append(f"C2 length ratio outside ±15%: {dst.relative_to(BASE)} source={sw} paraphrase={wc} ratio={ratio:.3f}")
            else:
                available_validated += 1
        else:
            warnings.append(f"C2 exists but source missing for length validation: {dst.relative_to(BASE)}")

    # Extra paraphrase files not matching the current assignment are usually stale or
    # generated against an earlier assignment. Report them explicitly.
    extra_c2 = []
    c2_root = BASE / "paraphrased_responses"
    if c2_root.exists():
        for path in sorted(c2_root.glob("*/*.json")):
            if path not in expected_c2_paths:
                extra_c2.append(path.relative_to(BASE))
                warnings.append(f"unassigned C2 paraphrase file: {path.relative_to(BASE)}")

    print("Replication wave validation")
    print("prompt_count", len(prompt_ids))
    print("C1 response counts", dict(response_counts))
    print("assignment author counts", dict(author_counts))
    print("assignment paraphraser counts", dict(paraphraser_counts))
    print("C2 paraphrase counts", dict(paraphrase_counts))
    print("C2 available validated", available_validated)
    print("unassigned C2 files", len(extra_c2))
    if missing_paraphrases:
        print("missing paraphrases", len(missing_paraphrases))
        for model in MODELS:
            if by_paraphraser_missing[model]:
                print(f"  {model}:", ", ".join(by_paraphraser_missing[model]))
    if warnings:
        print("warnings", len(warnings))
        for w in warnings:
            print("  WARN", w)
    if errors:
        print("errors", len(errors))
        for e in errors:
            print("  ERROR", e)
    if errors or (args.require_complete and (warnings or missing_paraphrases)):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
