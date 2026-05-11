"""Exploratory analysis: WHICH rubric dimension carries the self-preference signal?

For each of the five 1-10 rubric dimensions (correctness, completeness,
clarity, creativity, constraint_adherence) we re-run the C1 self-preference
regression with author, judge, and category fixed effects and HC0 robust SEs:

    score_dim ~ author_is_self + C(author) + C(judge) + C(category)

If self-preference is driven by *style familiarity* (as the recognition-
mediation result suggests), the effect should concentrate on form-oriented
dimensions (clarity, creativity) and be weaker on substance-oriented
dimensions (correctness, completeness, constraint_adherence).

We also run the horse-race version, adding `predicted_self` from the C4
authorship probe, to see whether *belief* drives all five dimensions or only
some.

Run:
    python3 analysis/subscale_analysis.py [--report PATH]
"""

from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RUBRIC = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]


def load_scores() -> pd.DataFrame:
    paths = sorted(glob.glob(str(ROOT / "data" / "judgments" / "*" / "long_scores.csv")))
    if not paths:
        raise SystemExit("No data/judgments/*/long_scores.csv found.")
    frames = [pd.read_csv(p) for p in paths]
    df = pd.concat(frames, ignore_index=True)
    df["condition"] = df["condition"].str.lower()
    df["author_is_self"] = (df["judge"] == df["author"]).astype(int)
    return df


def load_recognition() -> pd.DataFrame:
    paths = sorted(glob.glob(str(ROOT / "data" / "judgments" / "*" / "long_recognition.csv")))
    frames = [pd.read_csv(p) for p in paths]
    df = pd.concat(frames, ignore_index=True)
    df = df.rename(columns={"true_author": "author"})
    df["predicted_self"] = (df["predicted_author"] == df["judge"]).astype(int)
    return df[["judge", "author", "prompt_id", "predicted_self", "confidence"]]


def ols_with_dummies(df: pd.DataFrame, regressors: list[str],
                     fe: list[str], depvar: str) -> dict:
    """Plain NumPy OLS with dummy encodings; HC0 robust SEs."""
    cols = ["Intercept"]
    X_blocks = [np.ones((len(df), 1))]
    for r in regressors:
        X_blocks.append(df[r].to_numpy()[:, None].astype(float))
        cols.append(r)
    for f in fe:
        d = pd.get_dummies(df[f], prefix=f, drop_first=True, dtype=float).to_numpy()
        X_blocks.append(d)
        cols.extend([f"{f}_{i}" for i in range(d.shape[1])])
    X = np.hstack(X_blocks)
    y = df[depvar].to_numpy().astype(float)
    XtX = X.T @ X
    XtX_inv = np.linalg.pinv(XtX)
    beta = XtX_inv @ X.T @ y
    resid = y - X @ beta
    Omega = X.T @ (X * (resid ** 2)[:, None])
    cov = XtX_inv @ Omega @ XtX_inv
    se = np.sqrt(np.diag(cov))
    return {"cols": cols, "beta": beta, "se": se, "n": len(X)}


def coef_row(fit: dict, term: str) -> tuple[float, float, float, float, float]:
    idx = fit["cols"].index(term)
    b = float(fit["beta"][idx])
    s = float(fit["se"][idx])
    z = b / s if s > 0 else float("nan")
    lo, hi = b - 1.96 * s, b + 1.96 * s
    return b, s, z, lo, hi


def stars(z: float) -> str:
    a = abs(z)
    if a >= 3.29: return "***"
    if a >= 2.58: return "** "
    if a >= 1.96: return "*  "
    return "   "


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()

    df_s = load_scores()
    df_r = load_recognition()
    df = df_s.merge(df_r, on=["judge", "author", "prompt_id"], how="left")
    df = df.dropna(subset=["predicted_self"]).copy()
    df["predicted_self"] = df["predicted_self"].astype(int)
    print(f"Loaded {len(df)} merged rows.")

    out: list[str] = []
    out.append("# Per-rubric-dimension self-preference (subscale analysis)")
    out.append("")
    out.append("Same horse-race specification as the recognition-mediation analysis, "
               "but the dependent variable is each of the five 1–10 rubric "
               "dimensions (rather than the composite mean). All regressions include "
               "author / judge / category fixed effects and use HC0 robust standard "
               "errors. * p<0.05, ** p<0.01, *** p<0.001.")
    out.append("")

    # Descriptive: per-dimension self-pref gap in C1 (raw mean diff)
    c1 = df[df["condition"] == "c1"]
    out.append("## C1 descriptive: per-dimension self-preference gap")
    out.append("")
    rows = []
    for dim in RUBRIC:
        m_self = c1[c1["author_is_self"] == 1][dim].mean()
        m_other = c1[c1["author_is_self"] == 0][dim].mean()
        rows.append((dim, m_self, m_other, m_self - m_other))
    desc = pd.DataFrame(rows, columns=["dimension", "mean(self)", "mean(other)", "gap"])
    desc.iloc[:, 1:] = desc.iloc[:, 1:].round(3)
    out.append(desc.to_markdown(index=False))
    out.append("")

    # Per-condition, per-dimension regression (author_is_self alone, then horse race)
    for cond in ["c1", "c2", "c3"]:
        sub = df[df["condition"] == cond].copy()
        out.append(f"## Condition {cond.upper()} — per-dimension regressions")
        out.append("")

        # author_is_self alone
        out.append(f"### {cond.upper()}: composite ~ author_is_self + FE (no belief control)")
        out.append("")
        out.append("| dimension | β(author_is_self) | SE | 95% CI | p-stars |")
        out.append("|---|---:|---:|---:|:---:|")
        for dim in RUBRIC:
            fit = ols_with_dummies(sub, ["author_is_self"],
                                    ["author", "judge", "category"], depvar=dim)
            b, s, z, lo, hi = coef_row(fit, "author_is_self")
            out.append(f"| {dim} | {b:+.3f} | {s:.3f} | [{lo:+.3f}, {hi:+.3f}] | {stars(z).strip()} |")
        out.append("")

        # Horse race
        out.append(f"### {cond.upper()} horse race: dim ~ author_is_self + predicted_self + FE")
        out.append("")
        out.append("| dimension | β(author_is_self) | SE | β(predicted_self) | SE |")
        out.append("|---|---:|---:|---:|---:|")
        for dim in RUBRIC:
            fit = ols_with_dummies(sub, ["author_is_self", "predicted_self"],
                                    ["author", "judge", "category"], depvar=dim)
            ba, sa, za, *_ = coef_row(fit, "author_is_self")
            bp, sp, zp, *_ = coef_row(fit, "predicted_self")
            out.append(
                f"| {dim} | {ba:+.3f}{stars(za).strip()} | {sa:.3f} "
                f"| {bp:+.3f}{stars(zp).strip()} | {sp:.3f} |"
            )
        out.append("")

    out.append("## Interpretation")
    out.append("")
    out.append("If self-preference were driven by privileged access to correctness "
               "(\"I am better able to tell that *my* answer is right\"), the effect "
               "should concentrate on **correctness** and **completeness**. If it is "
               "driven by **style familiarity** instead — the form of one's own writing "
               "looking subjectively better — the effect should concentrate on "
               "**clarity** and **creativity**, the two dimensions that most directly "
               "track surface form. The table above lets readers see this directly.")
    out.append("")

    text = "\n".join(out)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text)
        print(f"Wrote report to {args.report}")
    else:
        print(text)


if __name__ == "__main__":
    main()
