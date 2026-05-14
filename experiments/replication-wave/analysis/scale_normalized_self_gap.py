#!/usr/bin/env python3
"""Scale-normalized self-preference robustness diagnostic.

Raw C1/C2/C3 self-preference gaps are in composite score points on a 1--10
rubric. This diagnostic asks whether the same qualitative judge heterogeneity
survives after removing judge/condition severity and scale differences.

For each (condition, judge) block, compute:
  * z_composite = (composite - block mean) / block sample SD
  * percentile = within-block average-rank percentile in [0, 1]
Then report self-authored minus other-authored gaps in raw points, z units, and
percentile points. The z and percentile gaps are not new causal estimands; they
are robustness views of whether raw self-gaps are just scale/severity artifacts.
"""

from __future__ import annotations

import csv
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, stdev

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "experiments" / "replication-wave" / "results"
IN = RESULTS / "long_scores.csv"
OUT_CSV = RESULTS / "scale_normalized_self_gap.csv"
OUT_MD = RESULTS / "scale_normalized_self_gap.md"
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
CONDS = ["c1", "c2", "c3"]


def read_rows() -> list[dict[str, str]]:
    with IN.open(newline="") as f:
        rows = list(csv.DictReader(f))
    if len(rows) != 480:
        raise SystemExit(f"Expected 480 long_scores rows, found {len(rows)}")
    return rows


def avg_rank_percentiles(vals: list[float]) -> list[float]:
    """Average-rank percentiles in [0,1], preserving original order."""
    n = len(vals)
    order = sorted(range(n), key=lambda i: vals[i])
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i + 1
        while j < n and vals[order[j]] == vals[order[i]]:
            j += 1
        # 1-indexed average rank for tied positions i+1..j
        avg_rank = (i + 1 + j) / 2
        for k in range(i, j):
            ranks[order[k]] = avg_rank
        i = j
    if n == 1:
        return [0.5]
    return [(r - 1) / (n - 1) for r in ranks]


def fmt(x: float, digits: int = 3) -> str:
    return f"{x:+.{digits}f}"


def main() -> None:
    rows = read_rows()
    for r in rows:
        r["composite"] = f"{mean(float(r[d]) for d in DIMS):.10f}"
        if r["condition"] not in CONDS:
            raise SystemExit(f"Unexpected condition {r['condition']}")
        if r["judge"] not in JUDGES or r["author"] not in JUDGES:
            raise SystemExit(f"Unexpected judge/author row: {r}")

    by_block: dict[tuple[str, str], list[int]] = defaultdict(list)
    for i, r in enumerate(rows):
        by_block[(r["condition"], r["judge"])].append(i)

    for block, idxs in sorted(by_block.items()):
        if len(idxs) != 40:
            raise SystemExit(f"Expected 40 rows for {block}, found {len(idxs)}")
        vals = [float(rows[i]["composite"]) for i in idxs]
        mu = mean(vals)
        sd = stdev(vals)
        if sd <= 0 or math.isnan(sd):
            raise SystemExit(f"Non-positive SD for {block}: {sd}")
        pct = avg_rank_percentiles(vals)
        for local_i, row_i in enumerate(idxs):
            rows[row_i]["z_composite"] = f"{(vals[local_i] - mu) / sd:.10f}"
            rows[row_i]["percentile"] = f"{pct[local_i]:.10f}"
            rows[row_i]["block_mean"] = f"{mu:.10f}"
            rows[row_i]["block_sd"] = f"{sd:.10f}"

    summary: list[dict[str, str]] = []
    for cond in CONDS:
        for judge in JUDGES:
            block_rows = [r for r in rows if r["condition"] == cond and r["judge"] == judge]
            self_rows = [r for r in block_rows if r["author"] == judge]
            other_rows = [r for r in block_rows if r["author"] != judge]
            if len(self_rows) != 10 or len(other_rows) != 30:
                raise SystemExit(f"Bad self/other counts for {(cond, judge)}: {len(self_rows)}, {len(other_rows)}")
            rec: dict[str, str] = {"condition": cond, "judge": judge, "self_n": "10", "other_n": "30"}
            for metric in ["composite", "z_composite", "percentile"]:
                self_mean = mean(float(r[metric]) for r in self_rows)
                other_mean = mean(float(r[metric]) for r in other_rows)
                rec[f"self_mean_{metric}"] = f"{self_mean:.6f}"
                rec[f"other_mean_{metric}"] = f"{other_mean:.6f}"
                rec[f"gap_{metric}"] = f"{self_mean - other_mean:.6f}"
            summary.append(rec)

    # Pooled judge-weighted means (each judge contributes one gap per condition).
    for cond in CONDS:
        cond_rows = [r for r in summary if r["condition"] == cond]
        rec = {"condition": cond, "judge": "pooled_judge_mean", "self_n": "40", "other_n": "120"}
        for metric in ["composite", "z_composite", "percentile"]:
            gaps = [float(r[f"gap_{metric}"]) for r in cond_rows]
            rec[f"self_mean_{metric}"] = ""
            rec[f"other_mean_{metric}"] = ""
            rec[f"gap_{metric}"] = f"{mean(gaps):.6f}"
        summary.append(rec)

    fields = [
        "condition", "judge", "self_n", "other_n",
        "self_mean_composite", "other_mean_composite", "gap_composite",
        "self_mean_z_composite", "other_mean_z_composite", "gap_z_composite",
        "self_mean_percentile", "other_mean_percentile", "gap_percentile",
    ]
    with OUT_CSV.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(summary)

    lines: list[str] = []
    lines.append("# Scale-normalized self-preference gaps")
    lines.append("")
    lines.append("Generated by `analysis/scale_normalized_self_gap.py` from canonical `long_scores.csv`.")
    lines.append("")
    lines.append("For each condition × judge block (40 ratings), composite scores are converted to (a) z-scores using that judge/condition's sample SD and (b) within-block average-rank percentiles. This removes judge severity and scale differences before recomputing self-authored minus other-authored gaps. It is a robustness diagnostic, not a causal label-swap estimator.")
    lines.append("")
    lines.append("## Summary by condition and judge")
    lines.append("")
    lines.append("| Condition | Judge | raw gap | z gap | percentile gap |")
    lines.append("|---|---|---:|---:|---:|")
    for cond in CONDS:
        for r in [x for x in summary if x["condition"] == cond and x["judge"] != "pooled_judge_mean"]:
            lines.append(f"| {cond.upper()} | {r['judge']} | {fmt(float(r['gap_composite']))} | {fmt(float(r['gap_z_composite']))} | {fmt(float(r['gap_percentile']))} |")
        pooled = next(x for x in summary if x["condition"] == cond and x["judge"] == "pooled_judge_mean")
        lines.append(f"| {cond.upper()} | **pooled judge mean** | **{fmt(float(pooled['gap_composite']))}** | **{fmt(float(pooled['gap_z_composite']))}** | **{fmt(float(pooled['gap_percentile']))}** |")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    c1 = {r["judge"]: r for r in summary if r["condition"] == "c1"}
    lines.append(f"The C1 directional pattern survives scale normalization: Claude ({fmt(float(c1['claude-opus-4.7']['gap_z_composite']))} z), Gemini ({fmt(float(c1['gemini-3.1-pro']['gap_z_composite']))} z), and GPT-5.5 ({fmt(float(c1['gpt-5.5']['gap_z_composite']))} z) remain positive, while Kimi remains strongly negative ({fmt(float(c1['kimi-k2.6']['gap_z_composite']))} z). The pooled C1 raw gap of {fmt(float(c1['pooled_judge_mean']['gap_composite']))} corresponds to only {fmt(float(c1['pooled_judge_mean']['gap_z_composite']))} within-judge SD units and {fmt(float(c1['pooled_judge_mean']['gap_percentile']))} percentile points, reinforcing that the pooled estimate is a cancellation artifact rather than a stable single benchmark.")
    lines.append("")
    lines.append("C2 remains near zero after normalization, and C3 resembles C1, matching the main analyses. Thus the main heterogeneity/inversion result is not an artifact of one judge using a wider or narrower numerical scale.")
    lines.append("")
    lines.append("Companion CSV: `scale_normalized_self_gap.csv`.")
    OUT_MD.write_text("\n".join(lines) + "\n")
    print(f"wrote {OUT_CSV.relative_to(ROOT)}")
    print(f"wrote {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
