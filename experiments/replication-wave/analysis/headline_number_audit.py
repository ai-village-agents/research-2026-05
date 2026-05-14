#!/usr/bin/env python3
"""Audit public-facing headline numbers against canonical replication outputs.

This script is intentionally lightweight: it does not re-run the full analysis
pipeline, but it recomputes/collects the headline values used in README.md,
results/elevator_pitch.md, and results/findings_summary_table.md from the
canonical CSV/Markdown outputs. It also checks that the rounded values most
likely to go stale are present in the public-facing prose.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "experiments" / "replication-wave" / "results"
OUT = RESULTS / "headline_number_audit.md"

JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def plus(x: float, digits: int = 2) -> str:
    return f"{x:+.{digits}f}"


def plain(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}"


def load_self_gaps() -> dict[tuple[str, str], float]:
    rows = read_csv(RESULTS / "self_preference_gaps.csv")
    return {(r["condition"], r["judge"]): float(r["self_preference_gap"]) for r in rows}


def load_condition_gaps() -> dict[str, float]:
    rows = read_csv(RESULTS / "condition_summary.csv")
    return {r["condition"]: float(r["self_minus_other"]) for r in rows}


def load_recognition() -> dict[str, dict[str, str]]:
    return {r["judge"]: r for r in read_csv(RESULTS / "recognition_accuracy.csv")}


def load_author_quality() -> dict[str, dict[str, str]]:
    return {r["author"]: r for r in read_csv(RESULTS / "author_quality_nonself_c1.csv")}


@dataclass
class PairedJudge:
    self_gap: float
    self_ci_lo: float
    self_ci_hi: float
    kimi_label_residual: float | None = None
    kimi_ci_lo: float | None = None
    kimi_ci_hi: float | None = None


def parse_paired_md() -> dict[str, PairedJudge]:
    text = (RESULTS / "paired_label_swap.md").read_text()
    out: dict[str, PairedJudge] = {}
    for judge in JUDGES:
        m = re.search(rf"## Judge: {re.escape(judge)}\n(?P<body>.*?)(?=\n## Judge:|\n## Summary table|\Z)", text, re.S)
        if not m:
            continue
        body = m.group("body")
        gap = re.search(r"SELF − OTHER residual gap = ([+\-]?[0-9.]+)\s+CI=\[([+\-]?[0-9.]+), ([+\-]?[0-9.]+)\]", body)
        if not gap:
            raise SystemExit(f"Could not parse self gap for {judge}")
        kimi = re.search(r"displayed=kimi-k2\.6: residual=([+\-]?[0-9.]+).*?CI=\[([+\-]?[0-9.]+), ([+\-]?[0-9.]+)\]", body)
        out[judge] = PairedJudge(
            self_gap=float(gap.group(1)),
            self_ci_lo=float(gap.group(2)),
            self_ci_hi=float(gap.group(3)),
            kimi_label_residual=float(kimi.group(1)) if kimi else None,
            kimi_ci_lo=float(kimi.group(2)) if kimi else None,
            kimi_ci_hi=float(kimi.group(3)) if kimi else None,
        )
    return out


def load_quality_adjusted_residual() -> dict[str, dict[str, float]]:
    rows = read_csv(RESULTS / "quality_adjusted_residual.csv")
    return {r["judge"]: {k: float(v) for k, v in r.items() if k != "judge"} for r in rows}


def load_perceived() -> dict[str, tuple[float, float, float]]:
    rows = read_csv(RESULTS / "perceived_self_main_coefficients.csv")
    return {r["term"]: (float(r["beta"]), float(r["boot_ci_low"]), float(r["boot_ci_high"])) for r in rows}


def sign_counts(judge: str, displayed_label: str) -> tuple[int, int, int]:
    rows = [r for r in read_csv(RESULTS / "paired_label_swap_by_prompt.csv") if r["judge"] == judge and r["displayed_label"] == displayed_label]
    vals = [float(r["mean_residual"]) for r in rows]
    positives = sum(v > 0 for v in vals)
    negatives = sum(v < 0 for v in vals)
    nonzero = positives + negatives
    return positives, negatives, nonzero


def dimension_values(judge: str, displayed_label: str) -> list[float]:
    rows = [r for r in read_csv(RESULTS / "paired_label_swap_by_dim.csv") if r["judge"] == judge and r["displayed_label"] == displayed_label]
    return [float(r["residual_mean"]) for r in rows]


def require_snippets(path: Path, snippets: list[str]) -> list[str]:
    text = path.read_text()
    missing = [s for s in snippets if s not in text]
    return missing


def main() -> None:
    self_gaps = load_self_gaps()
    pooled = load_condition_gaps()
    recog = load_recognition()
    quality = load_author_quality()
    paired = parse_paired_md()
    perceived = load_perceived()
    qadj = load_quality_adjusted_residual()

    kimi_q = float(quality["kimi-k2.6"]["mean"])
    non_kimi_q = sum(float(quality[j]["mean"]) for j in JUDGES if j != "kimi-k2.6") / 3
    pred_beta, pred_lo, pred_hi = perceived["predicted_self"]
    actual_beta, actual_lo, actual_hi = perceived["actual_self"]
    gem_kimi_dims = dimension_values("gemini-3.1-pro", "kimi-k2.6")
    gem_self_dims = dimension_values("gemini-3.1-pro", "gemini-3.1-pro")
    _, gem_kimi_neg, gem_kimi_nonzero = sign_counts("gemini-3.1-pro", "kimi-k2.6")
    gem_self_pos, _, gem_self_nonzero = sign_counts("gemini-3.1-pro", "gemini-3.1-pro")

    errors: list[str] = []
    if not all(v < 0 for v in gem_kimi_dims):
        errors.append("Gemini anti-Kimi per-dimension residuals are not all negative.")
    if not all(v > 0 for v in gem_self_dims):
        errors.append("Gemini self-label per-dimension residuals are not all positive.")
    if (gem_kimi_neg, gem_kimi_nonzero) != (7, 7):
        errors.append(f"Gemini anti-Kimi prompt sign count changed: {gem_kimi_neg}/{gem_kimi_nonzero} negative.")
    if (gem_self_pos, gem_self_nonzero) != (9, 10):
        errors.append(f"Gemini self-label prompt sign count changed: {gem_self_pos}/{gem_self_nonzero} positive.")

    qadj_residuals = [qadj[j]["residual"] for j in JUDGES]
    qadj_obs = [qadj[j]["obs_gap"] for j in JUDGES]
    mean_resid = sum(qadj_residuals) / len(qadj_residuals)
    mean_obs_qadj = sum(qadj_obs) / len(qadj_obs)
    if abs(mean_resid - mean_obs_qadj) > 0.01:
        errors.append(f"Quality-adjusted residual decomposition identity broken: mean_resid={mean_resid:+.4f} vs mean_obs={mean_obs_qadj:+.4f}")

    public_checks = {
        ROOT / "README.md": ["+0.38", "5.18", "8.72", "+0.29", "−0.24", "+1.53"],
        RESULTS / "elevator_pitch.md": ["+0.38", "5.18", "8.72", "+0.29", "−0.24", "7/7", "9/10", "+1.53"],
        RESULTS / "findings_summary_table.md": ["+2.43", "+0.12", "+0.29", "+0.00", "−2.87", "5.180", "8.716", "β_predicted_self = **+1.53**"],
    }
    for path, snippets in public_checks.items():
        missing = require_snippets(path, snippets)
        if missing:
            errors.append(f"{path.relative_to(ROOT)} is missing expected snippets: {missing}")

    lines: list[str] = []
    lines.append("# Headline number audit")
    lines.append("")
    lines.append("Generated by `analysis/headline_number_audit.py` from canonical replication outputs. This is a maintenance check for the README, elevator pitch, and one-page findings summary; it does not replace the full analysis pipeline.")
    lines.append("")
    lines.append("## Recomputed headline values")
    lines.append("")
    lines.append("| Quantity | Value | Source |")
    lines.append("|---|---:|---|")
    lines.append(f"| Pooled C1 self−other | {plus(pooled['c1'])} | `condition_summary.csv` |")
    lines.append(f"| Pooled C2 self−other | {plus(pooled['c2'])} | `condition_summary.csv` |")
    lines.append(f"| Pooled C3 self−other | {plus(pooled['c3'])} | `condition_summary.csv` |")
    for judge in JUDGES:
        lines.append(f"| {judge} C1 self-pref gap | {plus(self_gaps[('c1', judge)])} | `self_preference_gaps.csv` |")
    for judge in [j for j in JUDGES if j in paired]:
        pj = paired[judge]
        lines.append(f"| {judge} paired SELF−OTHER label gap | {plus(pj.self_gap)} [{plus(pj.self_ci_lo)}, {plus(pj.self_ci_hi)}] | `paired_label_swap.md` |")
    lines.append(f"| Gemini displayed-`kimi-k2.6` label residual | {plus(paired['gemini-3.1-pro'].kimi_label_residual or 0)} [{plus(paired['gemini-3.1-pro'].kimi_ci_lo or 0)}, {plus(paired['gemini-3.1-pro'].kimi_ci_hi or 0)}] | `paired_label_swap.md` |")
    lines.append(f"| Kimi non-self C1 author quality | {plain(kimi_q, 3)} | `author_quality_nonself_c1.csv` |")
    lines.append(f"| Non-Kimi non-self C1 author quality | {plain(non_kimi_q, 3)} | `author_quality_nonself_c1.csv` |")
    lines.append(f"| β_predicted_self | {plus(pred_beta)} [{plus(pred_lo)}, {plus(pred_hi)}] | `perceived_self_main_coefficients.csv` |")
    lines.append(f"| β_actual_self | {plus(actual_beta)} [{plus(actual_lo)}, {plus(actual_hi)}] | `perceived_self_main_coefficients.csv` |")
    for judge in JUDGES:
        r = qadj[judge]
        lines.append(f"| {judge} quality-adjusted C1 residual | {plus(r['residual'], 3)} | `quality_adjusted_residual.csv` |")
    lines.append(f"| Mean quality-adjusted residual (=pooled C1 self-pref) | {plus(mean_resid, 3)} | `quality_adjusted_residual.csv` |")
    lines.append("")
    lines.append("## Recognition")
    lines.append("")
    lines.append("| Judge | Overall | Self |")
    lines.append("|---|---:|---:|")
    for judge in JUDGES:
        r = recog[judge]
        lines.append(f"| {judge} | {r['correct']}/{r['n']} ({float(r['accuracy'])*100:.1f}%) | {r['self_recognition_hits']}/{r['self_recognition_n']} |")
    lines.append("")
    lines.append("## Breadth checks")
    lines.append("")
    lines.append(f"- Gemini anti-Kimi label per-dimension residuals: {', '.join(plus(v, 3) for v in gem_kimi_dims)} (all negative).")
    lines.append(f"- Gemini self-label per-dimension residuals: {', '.join(plus(v, 3) for v in gem_self_dims)} (all positive).")
    lines.append(f"- Gemini anti-Kimi prompt signs: {gem_kimi_neg}/{gem_kimi_nonzero} nonzero prompts negative.")
    lines.append(f"- Gemini self-label prompt signs: {gem_self_pos}/{gem_self_nonzero} nonzero prompts positive.")
    lines.append("")
    lines.append("## Public-facing snippet check")
    lines.append("")
    if errors:
        lines.append("**FAIL.**")
        for e in errors:
            lines.append(f"- {e}")
    else:
        lines.append("**PASS.** Key rounded headline values are present in `README.md`, `results/elevator_pitch.md`, and `results/findings_summary_table.md`.")
    lines.append("")
    OUT.write_text("\n".join(lines) + "\n")
    if errors:
        raise SystemExit("headline number audit failed; see results/headline_number_audit.md")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
