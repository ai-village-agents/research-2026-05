#!/usr/bin/env python3
"""smoke_test_pipeline.py — verify the full evaluator-bias pipeline end-to-end
on synthetic but realistic mock scores.

Pipeline tested:
  blind_responses.py --allow-partial
    --> evaluation_packets/
  score_collector.py export   (4 judges x 4 conditions)
    --> score_sheets/
  fill score sheets with synthetic data injecting H1/H2/H3/H4 signals
  score_collector.py ingest
    --> results/long_scores.csv + long_recognition.csv
  run_analysis.py
    --> results/analysis_report.md (printed to stdout)

The script writes everything to a temporary subdirectory it cleans up
afterward; the repo's own results/ and score_sheets/ are NOT touched.

Usage:
  python3 analysis/smoke_test_pipeline.py
"""
from __future__ import annotations

import json
import os
import random
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EVB = REPO_ROOT / "experiments" / "evaluator-bias"

JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
CONDS = ["C1", "C2", "C3", "C4"]
SUBSCALES = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]

# Synthetic ground truth — what we inject and expect the analysis to recover.
SELF_BIAS = {"claude-opus-4.7": 1.0, "gemini-3.1-pro": 0.5, "gpt-5.5": 0.7, "kimi-k2.6": 0.2}
ATTENUATION = {"C1": 1.0, "C2": 0.5, "C3": 0.8}
RECOG_RATE = 0.6  # judges recognize self 60% of the time


def run(cmd: list[str]) -> None:
    print(f"  $ {' '.join(cmd)}")
    subprocess.run(cmd, check=True, capture_output=True)


def fill_sheet(sheet_path: Path, key_path: Path, judge: str, condition: str, rng: random.Random) -> None:
    sheet = json.loads(sheet_path.read_text())
    key = {r["blind_id"]: r for r in json.loads(key_path.read_text())}
    for e in sheet["entries"]:
        k = key[e["blind_id"]]
        is_self = (k["author"] == judge)
        if condition in ("C1", "C2", "C3"):
            base = 7.0
            bias = SELF_BIAS[judge] * ATTENUATION[condition] if is_self else 0.0
            for s in SUBSCALES:
                v = round(base + bias + rng.gauss(0, 0.6))
                e[s] = max(1, min(10, v))
        else:
            if is_self and rng.random() < RECOG_RATE:
                e["predicted_author"] = judge
            else:
                e["predicted_author"] = rng.choice(JUDGES)
            e["confidence"] = rng.randint(1, 5)
    sheet_path.write_text(json.dumps(sheet, indent=2))


def main() -> int:
    rng = random.Random(42)

    # Snapshot anything we might overwrite, so we can restore at the end.
    pre_existing = {p: p.exists() for p in [
        EVB / "evaluation_packets",
        EVB / "score_sheets",
        REPO_ROOT / "results",
    ]}
    backup_dir = REPO_ROOT / ".smoke_test_backup"
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    backup_dir.mkdir()
    for p, exists in pre_existing.items():
        if exists:
            shutil.move(str(p), str(backup_dir / p.name))

    rc = 1
    try:
        print("[1/4] Generating blinded packets (--allow-partial)...")
        run(["python3", str(EVB / "blind_responses.py"), "--allow-partial"])

        print("[2/4] Exporting and filling score sheets with synthetic signals...")
        for j in JUDGES:
            for c in CONDS:
                run(["python3", str(EVB / "score_collector.py"), "export", "--judge", j, "--condition", c])
                fill_sheet(EVB / "score_sheets" / j / f"{c}.json",
                           EVB / "evaluation_packets" / "keys" / j / f"{c}_key.json",
                           j, c, rng)
                run(["python3", str(EVB / "score_collector.py"), "ingest", "--judge", j, "--condition", c])

        print("[3/4] Running analysis...")
        out = subprocess.run(["python3", str(REPO_ROOT / "analysis" / "run_analysis.py")],
                             capture_output=True, text=True, check=True)
        # Quick sanity checks on the printed report.
        text = out.stdout
        assert "H1 verdict:** SUPPORTED" in text, "H1 should be supported under synthetic signal"
        assert "H2 verdict:** SUPPORTED" in text, "H2 should be supported under synthetic signal"
        assert "H3 verdict:** SUPPORTED" in text, "H3 should be supported under synthetic signal"
        assert "H4 verdict:** SUPPORTED" in text, "H4 should be supported under synthetic signal"
        print("  All four hypotheses recovered from synthetic signal: OK")

        print("[4/4] Cleanup")
        rc = 0
    finally:
        # Always restore.
        for p, exists in pre_existing.items():
            if p.exists():
                if p.is_dir():
                    shutil.rmtree(p)
                else:
                    p.unlink()
            if exists:
                shutil.move(str(backup_dir / p.name), str(p))
        if backup_dir.exists():
            shutil.rmtree(backup_dir)

    if rc == 0:
        print("\nSmoke test PASSED.")
    else:
        print("\nSmoke test FAILED.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
