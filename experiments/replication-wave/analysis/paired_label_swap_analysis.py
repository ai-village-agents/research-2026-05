#!/usr/bin/env python3
"""
Paired within-response label-swap analysis (Day 408+).

Estimates the *causal* effect of the displayed author label on judge scores,
holding the underlying response fixed. Uses native (non-codex) judge scores from
sessions 1 and 2 of the label-swap packets, which by design rotate each of 40
unique responses across 2 of 4 displayed labels.

For each (judge, response) pair the two ratings are differenced from their
within-response mean, yielding label-effect residuals. Means and bootstrap CIs
are reported by displayed label, plus a self-vs-other contrast per judge.

Outputs:
- experiments/replication-wave/results/paired_label_swap.md
- experiments/replication-wave/results/paired_label_swap.csv
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKETS = ROOT / "data" / "label_swap_packets"
SCORES = ROOT / "score_sheets" / "label_swap"
RESULTS = ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
LABELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]


def load_packet_meta(judge: str) -> dict[str, dict]:
    meta = {}
    for s in (1, 2):
        f = PACKETS / judge / f"session_{s}.json"
        if not f.exists():
            continue
        for e in json.load(open(f))["entries"]:
            meta[e["blind_id"]] = {
                "session": s,
                "prompt_id": e["prompt_id"],
                "displayed_label": e["displayed_label"],
                "response_hash": hashlib.md5(e["response_text"].encode()).hexdigest()[:10],
            }
    return meta


def is_native(raw) -> bool:
    """Heuristic: a native-scored file is either a list (Gemini-style) or a dict
    with scoring_method=='native_in_context' (Claude-style). Anything else is
    assumed to be the older codex-backed wrapper output and is excluded."""
    if isinstance(raw, list):
        return True
    if isinstance(raw, dict):
        return raw.get("scoring_method") == "native_in_context"
    return False


def load_judge_rows(judge: str) -> list[dict]:
    meta = load_packet_meta(judge)
    rows = []
    for s in (1, 2):
        f = SCORES / judge / f"session_{s}_scored.json"
        if not f.exists():
            continue
        raw = json.load(open(f))
        if not is_native(raw):
            continue
        entries = raw if isinstance(raw, list) else raw.get("entries", [])
        for e in entries:
            if not all(isinstance(e.get(d), (int, float)) for d in DIMS):
                continue
            m = meta.get(e["blind_id"])
            if not m:
                continue
            rows.append({
                "judge": judge,
                "session": m["session"],
                "blind_id": e["blind_id"],
                "prompt_id": m["prompt_id"],
                "displayed_label": e.get("displayed_label", m["displayed_label"]),
                "response_hash": m["response_hash"],
                "composite": sum(e[d] for d in DIMS) / 5.0,
            })
    return rows


def paired_residuals(rows: list[dict]) -> tuple[dict[str, list[float]], list[list[dict]]]:
    by_resp = defaultdict(list)
    for r in rows:
        by_resp[r["response_hash"]].append(r)
    pairs = [v for v in by_resp.values() if len(v) == 2]
    residuals: dict[str, list[float]] = defaultdict(list)
    for pair in pairs:
        m = (pair[0]["composite"] + pair[1]["composite"]) / 2
        for p in pair:
            residuals[p["displayed_label"]].append(p["composite"] - m)
    return residuals, pairs


def bootstrap(rows: list[dict], judge_self: str, B: int = 2000, seed: int = 42) -> dict:
    by_resp = defaultdict(list)
    for r in rows:
        by_resp[r["response_hash"]].append(r)
    pairs = [v for v in by_resp.values() if len(v) == 2]
    rng = random.Random(seed)
    boots_label = defaultdict(list)
    boots_gap = []
    n = len(pairs)
    for _ in range(B):
        sample = [pairs[rng.randrange(n)] for _ in range(n)]
        residuals = defaultdict(list)
        for pair in sample:
            m = (pair[0]["composite"] + pair[1]["composite"]) / 2
            for p in pair:
                residuals[p["displayed_label"]].append(p["composite"] - m)
        for lab, vals in residuals.items():
            if vals:
                boots_label[lab].append(sum(vals) / len(vals))
        sv = residuals.get(judge_self, [])
        ov = [v for lab, vals in residuals.items() if lab != judge_self for v in vals]
        if sv and ov:
            boots_gap.append(sum(sv) / len(sv) - sum(ov) / len(ov))
    out = {}
    for lab, vals in boots_label.items():
        s = sorted(vals)
        out[lab] = (s[int(0.025 * len(s))], s[int(0.975 * len(s))])
    s = sorted(boots_gap)
    out["__self_other_gap__"] = (s[int(0.025 * len(s))], s[int(0.975 * len(s))]) if s else (float("nan"), float("nan"))
    return out


def write_csv(all_rows: dict[str, list[dict]], path: Path) -> None:
    with open(path, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["judge", "session", "blind_id", "prompt_id", "displayed_label", "response_hash", "composite"])
        rows_sorted = sorted(
            (r for rows in all_rows.values() for r in rows),
            key=lambda r: (
                r["judge"],
                int(r["session"]),
                r["prompt_id"],
                r["response_hash"],
                r["displayed_label"],
                r["blind_id"],
            ),
        )
        for r in rows_sorted:
            w.writerow([r["judge"], r["session"], r["blind_id"], r["prompt_id"], r["displayed_label"], r["response_hash"], f"{r['composite']:.3f}"])


def main(out_md: Path = RESULTS / "paired_label_swap.md") -> None:
    judges_with_data = []
    all_rows = {}
    for j in LABELS:
        rows = load_judge_rows(j)
        if rows:
            judges_with_data.append(j)
            all_rows[j] = rows

    lines = [
        "# Paired within-response label-swap analysis",
        "",
        "Generated by `analysis/paired_label_swap_analysis.py`. Estimates the causal effect of",
        "the *displayed* author label on judge composite ratings, controlling for the",
        "underlying response identity (each of 40 unique responses is rated twice — under two",
        "different displayed labels — across sessions 1 and 2). Native, in-context judge scores",
        "only; no codex/OpenAI-backend rows.",
        "",
        f"Judges with native S1+S2 data: {', '.join(judges_with_data)}",
        "",
    ]

    write_csv(all_rows, RESULTS / "paired_label_swap.csv")

    summary_table = ["| Judge | Self-label residual | n_self | CI(label_self) | Self−Other gap CI |", "|---|---:|---:|---|---|"]
    label_table = ["| Judge | Displayed label | Residual mean | n | Bootstrap 95% CI |", "|---|---|---:|---:|---|"]

    for j in judges_with_data:
        rows = all_rows[j]
        residuals, pairs = paired_residuals(rows)
        boots = bootstrap(rows, j)
        lines.append(f"## Judge: {j}")
        lines.append("")
        lines.append(f"- Paired responses: {len(pairs)} (each scored under 2 distinct displayed labels)")
        for lab in LABELS:
            vals = residuals.get(lab, [])
            if not vals:
                continue
            sd = statistics.stdev(vals) if len(vals) > 1 else float("nan")
            ci = boots.get(lab, (float("nan"), float("nan")))
            lines.append(f"- displayed={lab}: residual={sum(vals)/len(vals):+.3f} (n={len(vals)}, sd={sd:.3f}) CI=[{ci[0]:+.3f}, {ci[1]:+.3f}]")
            label_table.append(f"| {j} | {lab} | {sum(vals)/len(vals):+.3f} | {len(vals)} | [{ci[0]:+.3f}, {ci[1]:+.3f}] |")
        self_vals = residuals.get(j, [])
        other_vals = [v for lab, vs in residuals.items() if lab != j for v in vs]
        if self_vals and other_vals:
            sg = boots.get("__self_other_gap__", (float("nan"), float("nan")))
            gap = sum(self_vals) / len(self_vals) - sum(other_vals) / len(other_vals)
            lines.append(f"- **SELF − OTHER residual gap = {gap:+.3f}  CI=[{sg[0]:+.3f}, {sg[1]:+.3f}]**")
            ci_self = boots.get(j, (float("nan"), float("nan")))
            summary_table.append(f"| {j} | {sum(self_vals)/len(self_vals):+.3f} | {len(self_vals)} | [{ci_self[0]:+.3f}, {ci_self[1]:+.3f}] | [{sg[0]:+.3f}, {sg[1]:+.3f}] |")
        lines.append("")

    lines.append("## Summary table")
    lines.append("")
    lines.extend(summary_table)
    lines.append("")
    lines.append("## Per-label residual table (all judges)")
    lines.append("")
    lines.extend(label_table)
    lines.append("")
    lines.append("## Method note")
    lines.append("")
    lines.append("For each pair of ratings of the same response under two different labels, we compute")
    lines.append("the within-response mean and report each rating's deviation from that mean. The")
    lines.append("mean deviation by displayed label is the within-response label fixed-effect")
    lines.append("contrast. 95% confidence intervals use a percentile bootstrap (B=2000) over the 40")
    lines.append("response pairs. The self-vs-other gap is the difference between the residual mean")
    lines.append("under the judge's own label and the pooled mean under the three other labels.")
    lines.append("")

    out_md.write_text("\n".join(lines))
    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
