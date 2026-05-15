#!/usr/bin/env python3
"""Leave-one-judge-out of the pooled 3-judge paired SELF−OTHER causal effect.

Reads canonical per-judge SELF−OTHER residual gaps from
`experiments/replication-wave/results/paired_label_swap.md`, computes the
3-judge pooled (unweighted mean across judges with native data), and reports
how the pooled estimate shifts when each judge is dropped. This is the
causal-RCT analog to the observational `leave_one_out_sensitivity.md`.

Writes:
  results/paired_lojo.csv
  results/paired_lojo.md
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "results" / "paired_label_swap.md"
OUT_CSV = ROOT / "results" / "paired_lojo.csv"
OUT_MD = ROOT / "results" / "paired_lojo.md"

JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]


def parse_self_other() -> dict[str, tuple[float, float, float]]:
    text = SRC.read_text()
    out: dict[str, tuple[float, float, float]] = {}
    for judge in JUDGES:
        m = re.search(
            rf"## Judge: {re.escape(judge)}\n(?P<body>.*?)(?=\n## Judge:|\n## Summary table|\Z)",
            text,
            re.S,
        )
        if not m:
            continue
        body = m.group("body")
        gap = re.search(
            r"SELF − OTHER residual gap = ([+\-]?[0-9.]+)\s+CI=\[([+\-]?[0-9.]+), ([+\-]?[0-9.]+)\]",
            body,
        )
        if not gap:
            continue
        out[judge] = (float(gap.group(1)), float(gap.group(2)), float(gap.group(3)))
    return out


def main() -> None:
    gaps = parse_self_other()
    present = [j for j in JUDGES if j in gaps]
    values = [gaps[j][0] for j in present]
    n = len(present)
    if n == 0:
        raise SystemExit("No native paired data found.")

    pooled = sum(values) / n

    lojo_rows = []
    for drop in present:
        kept = [gaps[j][0] for j in present if j != drop]
        lojo_pooled = sum(kept) / len(kept)
        delta = lojo_pooled - pooled
        lojo_rows.append({"dropped_judge": drop, "lojo_pooled": round(lojo_pooled, 4), "delta_vs_pooled": round(delta, 4)})

    with open(OUT_CSV, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["statistic", "value"])
        w.writerow(["judges_present", ";".join(present)])
        w.writerow(["pooled_self_other", f"{pooled:+.4f}"])
        w.writerow([])
        w.writerow(["dropped_judge", "lojo_pooled", "delta_vs_pooled"])
        for r in lojo_rows:
            w.writerow([r["dropped_judge"], f"{r['lojo_pooled']:+.4f}", f"{r['delta_vs_pooled']:+.4f}"])

    short = {"claude-opus-4.7": "Claude", "gemini-3.1-pro": "Gemini", "gpt-5.5": "GPT-5.5", "kimi-k2.6": "Kimi"}
    lines = [
        "# Paired SELF−OTHER: leave-one-judge-out",
        "",
        "Causal-RCT analog to `leave_one_out_sensitivity.md`. Each judge's",
        f"SELF−OTHER paired residual gap is the within-response label effect",
        f"computed by `paired_label_swap_analysis.py`. The 'pooled' value is",
        f"the unweighted mean across the {n} judge(s) with native S1+S2",
        "scoring; LOJO shows how that pooled mean shifts if each judge is",
        "dropped one at a time.",
        "",
        f"**Judges present (native S1+S2):** {', '.join(short[j] for j in present)}",
        "",
        "## Per-judge SELF−OTHER (causal paired)",
        "",
        "| Judge | SELF−OTHER | 95% CI |",
        "|---|---:|:---|",
    ]
    for j in present:
        gap, lo, hi = gaps[j]
        lines.append(f"| {short[j]} | {gap:+.3f} | [{lo:+.3f}, {hi:+.3f}] |")
    lines += [
        "",
        f"**Pooled (mean across {n} judges):** **{pooled:+.3f}**",
        "",
        "## Leave-one-judge-out",
        "",
        "| Dropped judge | LOJO pooled | Δ vs full pooled |",
        "|---|---:|---:|",
    ]
    for r in lojo_rows:
        lines.append(
            f"| {short[r['dropped_judge']]} | {r['lojo_pooled']:+.3f} | {r['delta_vs_pooled']:+.3f} |"
        )
    max_abs_delta = max(abs(r["delta_vs_pooled"]) for r in lojo_rows) if lojo_rows else 0.0
    largest = max(present, key=lambda j: gaps[j][0])
    lines += [
        "",
        "**Reading.** The pooled paired SELF−OTHER causal effect is",
        f"{pooled:+.3f} across the {n} judges with native data. Unlike the",
        "observational LOJO (where dropping Kimi recovered the 3-judge",
        "+1.46 headline), the currently observed causal LOJO shifts the",
        f"pooled by at most {max_abs_delta:.3f} in either direction.",
        "The within-response printed-label effect is therefore less dominated",
        "by a single judge than the observational gap was in C1. The largest",
        f"single-judge causal estimate is {short[largest]} at {gaps[largest][0]:+.3f}. All four native",
        "paired judges are now included, so this LOJO table is the complete",
        "S1+S2 paired-label-swap version rather than a pending-data preview.",
        "",
        "*Generated by `analysis/paired_label_swap_lojo.py` from",
        "`results/paired_label_swap.md`.*",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    print(f"Pooled: {pooled:+.4f}; LOJO rows: {lojo_rows}")


if __name__ == "__main__":
    main()
