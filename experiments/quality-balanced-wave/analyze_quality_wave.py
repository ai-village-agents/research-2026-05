#!/usr/bin/env python3
"""Analyze quality-balanced wave C1 self-preference and optional C4 recognition."""
from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
SCORES = RESULTS / "long_scores.csv"
RECOG = RESULTS / "long_recognition.csv"
SUBSCALES = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
MODELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs) if xs else float("nan")


def fmt(x: float) -> str:
    if math.isnan(x):
        return "NA"
    return f"{x:+.3f}"


def read_scores() -> list[dict[str, str]]:
    if not SCORES.exists():
        raise SystemExit(f"No scored data yet: {SCORES}")
    with SCORES.open(newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row["composite"] = str(mean([float(row[s]) for s in SUBSCALES]))
    return rows


def write_csv(path: Path, header: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def analyze_scores(rows: list[dict[str, str]]) -> tuple[list[dict[str, object]], list[dict[str, object]], list[float]]:
    by_judge = sorted({r["judge"] for r in rows})
    gaps: list[dict[str, object]] = []
    paired_gaps: list[float] = []
    for judge in by_judge:
        judge_rows = [r for r in rows if r["judge"] == judge]
        self_scores = [float(r["composite"]) for r in judge_rows if r["author"] == judge]
        other_scores = [float(r["composite"]) for r in judge_rows if r["author"] != judge]
        gaps.append({
            "judge": judge,
            "self_mean": round(mean(self_scores), 6),
            "other_mean": round(mean(other_scores), 6),
            "self_minus_other": round(mean(self_scores) - mean(other_scores), 6),
            "n_self": len(self_scores),
            "n_other": len(other_scores),
        })
        by_prompt = sorted({r["prompt_id"] for r in judge_rows})
        for pid in by_prompt:
            cell = [r for r in judge_rows if r["prompt_id"] == pid]
            s = [float(r["composite"]) for r in cell if r["author"] == judge]
            o = [float(r["composite"]) for r in cell if r["author"] != judge]
            if s and o:
                paired_gaps.append(mean(s) - mean(o))
    summary = [{
        "condition": "c1",
        "judges_completed": len(by_judge),
        "score_rows": len(rows),
        "pooled_prompt_paired_self_gap": round(mean(paired_gaps), 6),
        "n_judge_prompt_pairs": len(paired_gaps),
    }]
    return gaps, summary, paired_gaps


def analyze_recognition() -> list[dict[str, object]]:
    if not RECOG.exists():
        return []
    with RECOG.open(newline="") as f:
        rows = list(csv.DictReader(f))
    out = []
    for judge in sorted({r["judge"] for r in rows}):
        jr = [r for r in rows if r["judge"] == judge]
        correct = sum(r["true_author"] == r["predicted_author"] for r in jr)
        self_rows = [r for r in jr if r["true_author"] == judge]
        self_correct = sum(r["predicted_author"] == judge for r in self_rows)
        out.append({
            "judge": judge,
            "accuracy": round(correct / len(jr), 6) if jr else "",
            "correct": correct,
            "n": len(jr),
            "self_correct": self_correct,
            "self_n": len(self_rows),
            "mean_confidence": round(mean([float(r["confidence"]) for r in jr]), 6) if jr else "",
        })
    return out


def write_report(gaps: list[dict[str, object]], summary: list[dict[str, object]], recog: list[dict[str, object]]) -> None:
    lines = [
        "# Quality-balanced wave results",
        "",
        "This report is generated from `results/long_scores.csv` and optional `results/long_recognition.csv`.",
        "The primary diagnostic is whether Kimi K2.6 still self-penalizes on moderate prompts designed to reduce genuine quality confounds.",
        "",
        "## C1 self-preference gaps",
        "",
        "| judge | self mean | other mean | self − other | n self | n other |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in gaps:
        lines.append(f"| {r['judge']} | {float(r['self_mean']):.2f} | {float(r['other_mean']):.2f} | **{fmt(float(r['self_minus_other']))}** | {r['n_self']} | {r['n_other']} |")
    lines += [
        "",
        "## Pooled prompt-paired gap",
        "",
        "| condition | completed judges | score rows | pooled self gap | n judge-prompt pairs |",
        "|---|---:|---:|---:|---:|",
    ]
    for r in summary:
        lines.append(f"| {r['condition']} | {r['judges_completed']} | {r['score_rows']} | **{fmt(float(r['pooled_prompt_paired_self_gap']))}** | {r['n_judge_prompt_pairs']} |")
    if recog:
        lines += ["", "## C4 recognition", "", "| judge | accuracy | correct / n | self correct / n | mean confidence |", "|---|---:|---:|---:|---:|"]
        for r in recog:
            lines.append(f"| {r['judge']} | {float(r['accuracy']):.1%} | {r['correct']} / {r['n']} | {r['self_correct']} / {r['self_n']} | {float(r['mean_confidence']):.2f} |")
    else:
        lines += ["", "## C4 recognition", "", "No recognition rows ingested yet."]
    (RESULTS / "quality_wave_report.md").write_text("\n".join(lines) + "\n")


def main() -> None:
    rows = read_scores()
    gaps, summary, _ = analyze_scores(rows)
    recog = analyze_recognition()
    write_csv(RESULTS / "self_preference_gaps.csv", ["judge", "self_mean", "other_mean", "self_minus_other", "n_self", "n_other"], gaps)
    write_csv(RESULTS / "condition_summary.csv", ["condition", "judges_completed", "score_rows", "pooled_prompt_paired_self_gap", "n_judge_prompt_pairs"], summary)
    if recog:
        write_csv(RESULTS / "recognition_accuracy.csv", ["judge", "accuracy", "correct", "n", "self_correct", "self_n", "mean_confidence"], recog)
    write_report(gaps, summary, recog)
    print("Wrote quality-balanced analysis outputs under", RESULTS)


if __name__ == "__main__":
    main()
