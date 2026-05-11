"""Per-judge subscale horse race.

For each judge × condition × rubric dimension, fit:
    score ~ author_is_self + predicted_self + C(author) + C(category)
with HC0 robust SEs. Shows how the pooled "belief drives content / raw style
drives form" dissociation decomposes across the three judges.

Usage:
    python3 analysis/per_judge_horse_race.py [--report results/per_judge_horse_race.md]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd


DIMS = [
    "correctness",
    "completeness",
    "clarity",
    "creativity",
    "constraint_adherence",
]
DIM_LABEL = {
    "correctness": "Correctness",
    "completeness": "Completeness",
    "clarity": "Clarity",
    "creativity": "Creativity",
    "constraint_adherence": "Constraint adherence",
}


def load(repo: Path, judges: list[str]) -> pd.DataFrame:
    scores = []
    recs = []
    for j in judges:
        sp = repo / "data" / "judgments" / j / "long_scores.csv"
        rp = repo / "data" / "judgments" / j / "long_recognition.csv"
        if not sp.exists() or not rp.exists():
            print(f"WARN: missing data for {j}", file=sys.stderr)
            continue
        scores.append(pd.read_csv(sp))
        recs.append(pd.read_csv(rp))
    sc = pd.concat(scores, ignore_index=True)
    rec = pd.concat(recs, ignore_index=True)
    rec = rec.rename(columns={"true_author": "author"})
    m = sc.merge(
        rec[["judge", "author", "prompt_id", "predicted_author"]],
        on=["judge", "author", "prompt_id"],
        how="left",
    )
    m["author_self"] = (m["author"] == m["judge"]).astype(int)
    m["pred_self"] = (m["predicted_author"] == m["judge"]).astype(int)
    return m


def fit(df: pd.DataFrame, dim: str) -> tuple[float, float, float, float, int]:
    """Fit OLS with HC0 robust SEs using only NumPy/pandas.

    This intentionally avoids statsmodels so the exploratory script runs in the
    same minimal environment as the preregistered fallback analysis.
    """
    d = df[[dim, "author_self", "pred_self", "author", "category"]].dropna()
    if len(d) < 10:
        return (np.nan, np.nan, np.nan, np.nan, len(d))

    X_df = pd.get_dummies(d[["author", "category"]], drop_first=True).astype(float)
    X_df["author_self"] = d["author_self"].astype(float).values
    X_df["pred_self"] = d["pred_self"].astype(float).values
    X_df.insert(0, "const", 1.0)

    X = X_df.to_numpy(dtype=float)
    y = d[dim].astype(float).to_numpy()
    try:
        xtx_inv = np.linalg.pinv(X.T @ X)
        beta = xtx_inv @ X.T @ y
        resid = y - X @ beta
        meat = X.T @ ((resid ** 2)[:, None] * X)
        cov = xtx_inv @ meat @ xtx_inv
        se = np.sqrt(np.maximum(np.diag(cov), 0.0))
        params = pd.Series(beta, index=X_df.columns)
        bse = pd.Series(se, index=X_df.columns)
        return (
            float(params.get("author_self", np.nan)),
            float(bse.get("author_self", np.nan)),
            float(params.get("pred_self", np.nan)),
            float(bse.get("pred_self", np.nan)),
            len(d),
        )
    except Exception as e:
        print(f"WARN: fit failed {dim}: {e}", file=sys.stderr)
        return (np.nan, np.nan, np.nan, np.nan, len(d))


def format_md(rows: list[dict]) -> str:
    out = ["| Judge | Condition | Dim | β(author_is_self) | SE | β(predicted_self) | SE | N |",
           "|---|---|---|---:|---:|---:|---:|---:|"]
    for r in rows:
        out.append(
            f"| {r['judge']} | {r['condition'].upper()} | {DIM_LABEL[r['dim']]} "
            f"| {r['b_a']:+.2f} | {r['se_a']:.2f} | {r['b_p']:+.2f} | {r['se_p']:.2f} | {r['n']} |"
        )
    return "\n".join(out)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--report", type=Path, default=None)
    p.add_argument("--repo", type=Path, default=Path(__file__).resolve().parent.parent)
    args = p.parse_args()

    judges = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
    judges = [j for j in judges if (args.repo / "data" / "judgments" / j).is_dir()]
    df = load(args.repo, judges)

    rows = []
    for cond in ["c1", "c2", "c3"]:
        for judge in judges:
            sub = df[(df.judge == judge) & (df.condition == cond)]
            if len(sub) == 0:
                continue
            for dim in DIMS:
                b_a, se_a, b_p, se_p, n = fit(sub, dim)
                rows.append(dict(judge=judge, condition=cond, dim=dim,
                                 b_a=b_a, se_a=se_a, b_p=b_p, se_p=se_p, n=n))

    md = ["# Per-judge subscale horse race",
          "",
          "For each judge × condition × rubric dimension, OLS of:",
          "",
          "    score ~ author_is_self + predicted_self + C(author) + C(category)",
          "",
          "HC0 robust standard errors. `author_is_self = 1` iff the response is",
          "actually authored by the judge; `predicted_self = 1` iff the judge's C4",
          "authorship prediction names itself (looked up per (judge, prompt_id)).",
          "",
          "## All judges × conditions × dimensions",
          "",
          format_md(rows),
          ""]
    report = "\n".join(md) + "\n"
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report)
        print(f"Wrote {args.report} ({len(rows)} rows)")
    else:
        sys.stdout.write(report)


if __name__ == "__main__":
    main()
