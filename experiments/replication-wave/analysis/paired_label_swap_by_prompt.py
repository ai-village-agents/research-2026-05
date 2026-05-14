#!/usr/bin/env python3
"""
Per-prompt label residual table for the paired label-swap experiment.

For each (judge, displayed_label, prompt_id) computes the mean within-response
residual from the 2-rating mean. Used as the per-prompt sign-test in §3.10
of the replication-wave blogpost.
"""
from __future__ import annotations
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKETS = ROOT / "data" / "label_swap_packets"
SCORES = ROOT / "score_sheets" / "label_swap"
ALT_SCORES = ROOT / "data" / "label_swap_scores"
RESULTS = ROOT / "results"
DIMS = ["correctness","completeness","clarity","creativity","constraint_adherence"]


def score_file(judge: str, session: int) -> Path | None:
    """Return native scored-file path, preferring canonical score_sheets/."""
    for candidate in (
        SCORES / judge / f"session_{session}_scored.json",
        ALT_SCORES / judge / f"session_{session}_scored.json",
    ):
        if candidate.exists():
            return candidate
    return None


def score_judges() -> list[str]:
    """Judges with possible scored files in canonical or fallback roots."""
    names = set()
    for root in (SCORES, ALT_SCORES):
        if root.exists():
            names.update(p.name for p in root.iterdir() if p.is_dir())
    return sorted(names)


def is_native(raw):
    if isinstance(raw, list): return True
    if isinstance(raw, dict): return raw.get("scoring_method") == "native_in_context"
    return False


def load_rows(judge: str):
    pkt = {}
    for s in (1, 2):
        f = PACKETS / judge / f"session_{s}.json"
        if not f.exists(): continue
        for e in json.load(open(f))["entries"]:
            h = hashlib.md5(e["response_text"].encode()).hexdigest()[:10]
            pkt[e["blind_id"]] = {"hash": h, "prompt_id": e["prompt_id"]}
    rows = []
    for s in (1, 2):
        f = score_file(judge, s)
        if f is None: continue
        raw = json.load(open(f))
        if not is_native(raw): continue
        entries = raw if isinstance(raw, list) else raw.get("entries", [])
        for e in entries:
            m = pkt.get(e["blind_id"])
            if not m: continue
            if not all(isinstance(e.get(d), (int, float)) for d in DIMS): continue
            comp = sum(e[d] for d in DIMS) / 5.0
            rows.append({"hash": m["hash"], "prompt_id": m["prompt_id"],
                         "displayed_label": e["displayed_label"], "composite": comp})
    return rows


def main():
    out = []
    for j in score_judges():
        rows = load_rows(j)
        by_hash = defaultdict(list)
        for r in rows: by_hash[r["hash"]].append(r)
        by_lp = defaultdict(list)
        for h, lst in by_hash.items():
            if len(lst) != 2: continue
            mean = sum(r["composite"] for r in lst) / 2
            for r in lst:
                by_lp[(r["displayed_label"], r["prompt_id"])].append(r["composite"] - mean)
        for (lbl, pid), vals in sorted(by_lp.items()):
            out.append({"judge": j, "displayed_label": lbl, "prompt_id": pid,
                        "n": len(vals), "mean_residual": f"{sum(vals)/len(vals):+.3f}"})
    out_path = RESULTS / "paired_label_swap_by_prompt.csv"
    with open(out_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["judge","displayed_label","prompt_id","n","mean_residual"])
        w.writeheader()
        for r in out: w.writerow(r)
    print(f"Wrote {len(out)} rows -> {out_path}")


if __name__ == "__main__":
    main()
