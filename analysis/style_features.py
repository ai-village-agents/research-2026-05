#!/usr/bin/env python3
"""
Compute simple stylometric features for each response (original and paraphrased).

Features:
  - word_count
  - char_count
  - mean_sentence_length (words)
  - mean_word_length (chars)
  - type_token_ratio (lexical diversity)
  - markdown_header_rate (# of lines starting with '#')
  - bullet_rate (# of lines starting with '- ', '* ', or '\\d+\\.')
  - emdash_rate (em-dashes per 1000 chars)
  - first_person_rate (we/I/our/my tokens per 100 words)
  - code_block_count (number of ``` fences)
  - bold_count (occurrences of **)
  - colon_rate (colons per 100 words)
  - semicolon_rate (semicolons per 100 words)

Usage:
  python analysis/style_features.py                                  # original responses
  python analysis/style_features.py --paraphrased                    # paraphrases
  python analysis/style_features.py --out data/style_features.csv    # write CSV
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import Counter

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EB = os.path.join(REPO_ROOT, "experiments", "evaluator-bias")

BULLET_RE = re.compile(r"^\s*(?:[-*+]\s|\d+\.\s)")
HEADER_RE = re.compile(r"^\s*#+\s")
FIRST_PERSON = {"i", "we", "my", "our", "us", "me", "ours", "mine"}


def features_for_text(text: str) -> dict:
    n_chars = len(text)
    words = re.findall(r"\b\w+\b", text)
    n_words = len(words)
    if n_words == 0:
        return {"word_count": 0}
    sentences = [s for s in re.split(r"[.!?]+\s", text) if s.strip()]
    n_sent = max(1, len(sentences))
    lower_words = [w.lower() for w in words]
    types = set(lower_words)
    lines = text.splitlines()

    n_headers = sum(1 for ln in lines if HEADER_RE.match(ln))
    n_bullets = sum(1 for ln in lines if BULLET_RE.match(ln))
    n_emdash = text.count("—") + text.count("--")
    n_fp = sum(1 for w in lower_words if w in FIRST_PERSON)
    n_code = text.count("```")
    n_bold = text.count("**") // 2
    n_colon = text.count(":")
    n_semi = text.count(";")

    return {
        "word_count": n_words,
        "char_count": n_chars,
        "mean_sentence_length": round(n_words / n_sent, 2),
        "mean_word_length": round(sum(len(w) for w in words) / n_words, 2),
        "type_token_ratio": round(len(types) / n_words, 4),
        "markdown_header_rate": round(n_headers / max(1, len(lines)), 4),
        "bullet_rate": round(n_bullets / max(1, len(lines)), 4),
        "emdash_per_1k": round(n_emdash / max(1, n_chars) * 1000, 3),
        "first_person_per_100w": round(n_fp / n_words * 100, 3),
        "code_block_pairs": n_code // 2,
        "bold_count": n_bold,
        "colons_per_100w": round(n_colon / n_words * 100, 3),
        "semicolons_per_100w": round(n_semi / n_words * 100, 3),
    }


def iter_originals():
    base = os.path.join(EB, "responses")
    for author in sorted(os.listdir(base)):
        adir = os.path.join(base, author)
        if not os.path.isdir(adir):
            continue
        for fn in sorted(os.listdir(adir)):
            if not fn.endswith(".json"):
                continue
            prompt_id = fn[len("prompt-"):-len(".json")]
            with open(os.path.join(adir, fn)) as f:
                obj = json.load(f)
            yield {"kind": "original", "author": author, "paraphraser": "", "prompt_id": prompt_id,
                   "text": obj.get("response", "")}


def iter_paraphrased():
    base = os.path.join(EB, "paraphrased_responses")
    if not os.path.isdir(base):
        return
    for paraphraser in sorted(os.listdir(base)):
        pdir = os.path.join(base, paraphraser)
        if not os.path.isdir(pdir):
            continue
        for fn in sorted(os.listdir(pdir)):
            if not fn.endswith(".json"):
                continue
            with open(os.path.join(pdir, fn)) as f:
                obj = json.load(f)
            yield {
                "kind": "paraphrased",
                "author": obj.get("original_author", ""),
                "paraphraser": obj.get("paraphraser", paraphraser),
                "prompt_id": obj.get("prompt_id", ""),
                "text": obj.get("paraphrased_response", ""),
            }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--paraphrased", action="store_true",
                    help="Compute features for paraphrased corpus instead of originals.")
    ap.add_argument("--both", action="store_true",
                    help="Compute features for both originals and paraphrases (stacked).")
    ap.add_argument("--out", default=None, help="Optional output CSV path.")
    args = ap.parse_args()

    sources = []
    if args.both:
        sources = [iter_originals(), iter_paraphrased()]
    elif args.paraphrased:
        sources = [iter_paraphrased()]
    else:
        sources = [iter_originals()]

    rows = []
    for src in sources:
        for item in src:
            f = features_for_text(item["text"])
            row = {"kind": item["kind"], "author": item["author"],
                   "paraphraser": item["paraphraser"], "prompt_id": item["prompt_id"]}
            row.update(f)
            rows.append(row)

    if not rows:
        print("No responses found.", file=sys.stderr)
        return 1

    headers = list(rows[0].keys())
    out = args.out or "-"
    if out == "-":
        w = csv.DictWriter(sys.stdout, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    else:
        os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
        with open(out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=headers)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"Wrote {len(rows)} rows to {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
