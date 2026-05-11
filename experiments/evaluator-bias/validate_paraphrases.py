#!/usr/bin/env python3
"""
Validate the paraphrase corpus for the evaluator-bias study.

Checks:
  1. Every paraphrase file is parseable JSON with the expected schema.
  2. For each paraphrase, the original response exists.
  3. Word count is within +/-15% of the original (per PARAPHRASE_INSTRUCTIONS.md).
  4. Coverage: the round-robin assignment matrix is satisfied.
  5. No model has paraphrased its own response (diagonal must be empty).

Usage:
  python experiments/evaluator-bias/validate_paraphrases.py
"""
import csv
import json
import os
import sys
from collections import defaultdict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EB = os.path.join(REPO_ROOT, "experiments", "evaluator-bias")
RESPONSES_DIR = os.path.join(EB, "responses")
PARAPHRASES_DIR = os.path.join(EB, "paraphrased_responses")
ASSIGNMENT_CSV = os.path.join(EB, "paraphrase_assignment.csv")

MODELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
LENGTH_TOLERANCE = 0.15  # +/-15%


def word_count(text: str) -> int:
    return len(text.split())


def load_assignment():
    """Return list of (paraphraser, original_author, prompt_id) tuples."""
    if not os.path.exists(ASSIGNMENT_CSV):
        return []
    out = []
    with open(ASSIGNMENT_CSV) as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append((row["paraphraser_model"], row["author_model"], row["prompt_id"]))
    return out


def check_one_paraphrase(path, paraphraser, original_author, prompt_id, problems):
    try:
        with open(path) as f:
            obj = json.load(f)
    except Exception as e:
        problems.append(f"[{paraphraser}] {os.path.basename(path)}: invalid JSON ({e})")
        return

    for key in ("prompt_id", "original_author", "paraphraser", "paraphrased_response"):
        if key not in obj:
            problems.append(f"[{paraphraser}] {os.path.basename(path)}: missing field '{key}'")
            return

    if obj["prompt_id"] != prompt_id:
        problems.append(
            f"[{paraphraser}] {os.path.basename(path)}: prompt_id mismatch "
            f"(file says {obj['prompt_id']!r}, expected {prompt_id!r})"
        )
    if obj["original_author"] != original_author:
        problems.append(
            f"[{paraphraser}] {os.path.basename(path)}: original_author mismatch "
            f"(file says {obj['original_author']!r}, expected {original_author!r})"
        )
    if obj["paraphraser"] != paraphraser:
        problems.append(
            f"[{paraphraser}] {os.path.basename(path)}: paraphraser mismatch "
            f"(file says {obj['paraphraser']!r}, expected {paraphraser!r})"
        )

    # Length check
    orig_path = os.path.join(RESPONSES_DIR, original_author, f"prompt-{prompt_id}.json")
    if not os.path.exists(orig_path):
        problems.append(
            f"[{paraphraser}] {os.path.basename(path)}: original response not found at {orig_path}"
        )
        return

    with open(orig_path) as f:
        orig = json.load(f)
    orig_text = orig.get("response", "")
    orig_wc = word_count(orig_text)
    para_wc = word_count(obj["paraphrased_response"])
    if orig_wc == 0:
        return
    ratio = para_wc / orig_wc
    if abs(ratio - 1.0) > LENGTH_TOLERANCE:
        problems.append(
            f"[{paraphraser}] prompt-{prompt_id} (orig {original_author}): "
            f"length {para_wc}w vs original {orig_wc}w (ratio {ratio:.2f}, out of +/-15%)"
        )


def main():
    assignment = load_assignment()
    if not assignment:
        print("No paraphrase_assignment.csv found.")
        return 1

    problems = []
    found = defaultdict(set)  # paraphraser -> set of (original_author, prompt_id)
    expected = defaultdict(set)

    for paraphraser, original_author, prompt_id in assignment:
        expected[paraphraser].add((original_author, prompt_id))
        if paraphraser == original_author:
            problems.append(
                f"[ASSIGNMENT] {paraphraser} is assigned to paraphrase its own prompt-{prompt_id}"
            )

        path = os.path.join(
            PARAPHRASES_DIR, paraphraser, f"{original_author}__prompt-{prompt_id}.json"
        )
        if os.path.exists(path):
            check_one_paraphrase(path, paraphraser, original_author, prompt_id, problems)
            found[paraphraser].add((original_author, prompt_id))

    print("== Paraphrase corpus status ==")
    for m in MODELS:
        f = len(found.get(m, set()))
        e = len(expected.get(m, set()))
        status = "OK" if f == e else "pending"
        print(f"  {m:20s}  {f}/{e}  {status}")

    if problems:
        print("\n== Issues ==")
        for p in problems:
            print(f"  - {p}")
        print(f"\nTotal issues: {len(problems)}")
        return 1
    print("\nNo issues.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
