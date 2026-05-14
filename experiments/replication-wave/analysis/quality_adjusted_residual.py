#!/usr/bin/env python3
"""Quality-adjusted self-preference residual analysis (C1, observational).

Decomposes each judge's C1 self-preference gap into:
  obs_gap     = avg(judge_rating | author=self) - avg(judge_rating | author!=self)
  expected_gap = Q[self] - mean(Q[others])
                 where Q[a] = mean rating of author a by all non-a judges
                 (peer-only intrinsic quality)
  residual    = obs_gap - expected_gap     (label/identity bias)

This is a more intuitive presentation of the §3.7 mediator regression:
the mean residual across judges equals the pooled C1 self-preference gap,
while the residuals isolate the slice of each judge's gap that is NOT
attributable to differences in their own response quality.

Reads:
  experiments/replication-wave/results/author_quality_by_judge_c1.csv
Writes:
  experiments/replication-wave/results/quality_adjusted_residual.csv
  experiments/replication-wave/results/quality_adjusted_residual.md
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "results" / "author_quality_by_judge_c1.csv"
OUT_CSV = ROOT / "results" / "quality_adjusted_residual.csv"
OUT_MD = ROOT / "results" / "quality_adjusted_residual.md"


def load_matrix(path: Path) -> tuple[list[str], dict[str, dict[str, float]]]:
    with open(path) as f:
        rdr = csv.reader(f)
        header = next(rdr)
        authors = header[1:]
        M: dict[str, dict[str, float]] = {}
        for row in rdr:
            M[row[0]] = {a: float(v) for a, v in zip(authors, row[1:])}
    return authors, M


def main() -> None:
    authors, M = load_matrix(SRC)
    judges = list(M.keys())
    assert authors == judges, "C1 author/judge labels must match for self-pref decomposition"

    # Peer-only intrinsic author quality (Q): mean rating from non-self judges
    Q = {
        a: sum(M[j][a] for j in judges if j != a) / (len(judges) - 1)
        for a in authors
    }

    rows = []
    for j in judges:
        obs_self = M[j][j]
        obs_other = sum(M[j][a] for a in authors if a != j) / (len(authors) - 1)
        obs_gap = obs_self - obs_other

        exp_self = Q[j]
        exp_other = sum(Q[a] for a in authors if a != j) / (len(authors) - 1)
        exp_gap = exp_self - exp_other

        residual = obs_gap - exp_gap
        rows.append(
            {
                "judge": j,
                "obs_self": round(obs_self, 4),
                "obs_other": round(obs_other, 4),
                "obs_gap": round(obs_gap, 4),
                "Q_self": round(exp_self, 4),
                "Q_other_mean": round(exp_other, 4),
                "expected_gap": round(exp_gap, 4),
                "residual": round(residual, 4),
            }
        )

    mean_resid = sum(r["residual"] for r in rows) / len(rows)
    mean_obs = sum(r["obs_gap"] for r in rows) / len(rows)

    fields = list(rows[0].keys())
    with open(OUT_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    lines = [
        "# Quality-adjusted self-preference residual (C1, observational)",
        "",
        "Decomposes each judge's C1 self-preference gap into a part predicted",
        "by differences in their own response quality (peer-rated, non-self) and",
        "a label/identity residual:",
        "",
        "- `obs_gap` = mean(rating | author=self) − mean(rating | author≠self)",
        "- `Q[a]`    = mean rating of author *a* by all non-*a* judges",
        "- `expected_gap` = Q[self] − mean(Q[others])",
        "- `residual` = `obs_gap` − `expected_gap`",
        "",
        "By construction, the mean of `residual` across judges equals the",
        "pooled C1 self−other gap (see `condition_summary.csv`). Residuals",
        "isolate the slice of each judge's gap **not** attributable to its",
        "responses being intrinsically better or worse than peers'.",
        "",
        "| Judge | obs gap | expected (quality-only) | residual |",
        "|---|---:|---:|---:|",
    ]
    for r in rows:
        short = r["judge"].split("-")[0].capitalize()
        lines.append(
            f"| {short} | {r['obs_gap']:+.3f} | {r['expected_gap']:+.3f} | {r['residual']:+.3f} |"
        )
    lines += [
        f"| **Mean** | **{mean_obs:+.3f}** | — | **{mean_resid:+.3f}** |",
        "",
        "**Reading.** All four judges have a *positive* quality-adjusted",
        "residual (+0.20 to +0.66). Kimi's headline −2.87 observational gap",
        "is more-than-fully explained by its responses scoring −3.54 below",
        "non-self peers; on top of that quality deficit, Kimi rates its own",
        "responses **+0.66 higher** than peer-quality would predict — the",
        "*largest* pro-self residual of any judge. Conversely Claude's",
        "+2.43 headline gap shrinks to a +0.44 residual after quality",
        "adjustment. The mean residual +0.378 reproduces the pooled C1",
        "self-pref exactly, confirming the decomposition is identity.",
        "",
        "**Connection to §3.7.** This is a coefficient-free presentation of",
        "the same partial-out logic as the C1 mediator regression",
        "(β_actual_self ≈ −0.35, β_predicted_self ≈ +1.53): once you remove",
        "the part of each judge's self-rating gap explained by its own",
        "response quality, what's left is a small but consistently positive",
        "identity/label-favoring effect across all four judges.",
        "",
        "**Connection to §3.10.** The quality-adjusted residuals (+0.20…+0.66)",
        "overlap the *range* of the within-response paired SELF−OTHER causal",
        "estimates from the label-swap RCT (Claude +0.12, Gemini +0.29,",
        "GPT-5.5 ≈ +0.000, Kimi pending), but are not identical: the C1",
        "residual still contains *content* differences across self/other,",
        "while the paired causal estimate holds content constant via",
        "label re-randomization.",
        "",
        "*Generated by `analysis/quality_adjusted_residual.py` from",
        "`results/author_quality_by_judge_c1.csv`.*",
        "",
    ]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote {OUT_CSV}")
    print(f"Wrote {OUT_MD}")
    print()
    print(f"Mean obs gap: {mean_obs:+.4f}")
    print(f"Mean residual: {mean_resid:+.4f}")


if __name__ == "__main__":
    main()
