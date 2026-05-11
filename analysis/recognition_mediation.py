"""Exploratory analysis: is self-preference *mediated* by recognition?

For every C1 / C2 / C3 scoring row we know:
- author_is_self        : did the judge actually grade its own response?
- predicted_self        : in the C4 probe, did the judge later think it had
                          authored that response?
- recognized_correctly  : was the C4 prediction correct?

If the self-preference signal in C1 is driven by *style recognition*, we
should see a stronger effect on the predicted_self indicator than on the
author_is_self indicator — i.e. the judge rates higher whatever it *believes*
is its own work, whether or not it really is. A horse-race regression with
both indicators tells us which one carries the signal.

Run:
    python3 analysis/recognition_mediation.py [--report PATH]
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
    df["composite"] = df[RUBRIC].mean(axis=1)
    df["author_is_self"] = (df["judge"] == df["author"]).astype(int)
    return df


def load_recognition() -> pd.DataFrame:
    paths = sorted(glob.glob(str(ROOT / "data" / "judgments" / "*" / "long_recognition.csv")))
    frames = [pd.read_csv(p) for p in paths]
    df = pd.concat(frames, ignore_index=True)
    df = df.rename(columns={"true_author": "author"})
    df["predicted_self"] = (df["predicted_author"] == df["judge"]).astype(int)
    df["recognized_correctly"] = (df["predicted_author"] == df["author"]).astype(int)
    return df[["judge", "author", "prompt_id", "predicted_self",
               "recognized_correctly", "confidence"]]


def merge(df_scores: pd.DataFrame, df_rec: pd.DataFrame) -> pd.DataFrame:
    return df_scores.merge(df_rec, on=["judge", "author", "prompt_id"], how="left")


def ols_with_dummies(df: pd.DataFrame, regressors: list[str],
                     fe: list[str], depvar: str = "composite") -> dict:
    """Plain NumPy OLS with dummy encodings; HC0 robust SEs."""
    parts = [df[depvar].to_numpy()[:, None]]
    cols = []
    X_blocks = [np.ones((len(df), 1))]
    cols.append("Intercept")
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
    n, k = X.shape
    # HC0 sandwich
    Omega = X.T @ (X * (resid ** 2)[:, None])
    cov = XtX_inv @ Omega @ XtX_inv
    se = np.sqrt(np.diag(cov))
    return {"cols": cols, "beta": beta, "se": se, "n": n}


def report_coef(label: str, fit: dict, names: list[str], out: list[str]) -> None:
    out.append(f"### {label}")
    out.append("")
    out.append("| term | estimate | SE | 95% CI |")
    out.append("|---|---:|---:|---:|")
    for name in names:
        idx = fit["cols"].index(name)
        b = fit["beta"][idx]
        s = fit["se"][idx]
        lo, hi = b - 1.96 * s, b + 1.96 * s
        out.append(f"| {name} | {b:+.4f} | {s:.4f} | [{lo:+.4f}, {hi:+.4f}] |")
    out.append(f"\nN = {fit['n']}")
    out.append("")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()

    df_s = load_scores()
    df_r = load_recognition()
    print(f"Loaded {len(df_s)} score rows, {len(df_r)} recognition rows.")
    df = merge(df_s, df_r)
    # Recognition is only meaningful where it joined (which is all rows since
    # each (judge, author, prompt_id) appears once in C4 too).
    print(f"Merged: {len(df)} rows; {(df['predicted_self'].isna()).sum()} unmatched.")
    df = df.dropna(subset=["predicted_self", "recognized_correctly"]).copy()
    df["predicted_self"] = df["predicted_self"].astype(int)
    df["recognized_correctly"] = df["recognized_correctly"].astype(int)

    out: list[str] = []
    out.append("# Recognition-mediation exploratory analysis")
    out.append("")
    out.append("Tests whether the self-preference signal observed in C1/C2/C3")
    out.append("is driven by the judge **actually being the author** "
               "(`author_is_self`) or by the judge **believing it is the author** "
               "(`predicted_self`, from the C4 probe). Same response set across "
               "conditions, joined on (judge, true_author, prompt_id).")
    out.append("")

    # Descriptive 2x2 in C1
    c1 = df[df["condition"] == "c1"]
    out.append(f"## C1 descriptive: mean composite by (author_is_self, predicted_self)")
    out.append("")
    tab = c1.groupby(["author_is_self", "predicted_self"])["composite"].agg(["mean", "count"])
    tab["mean"] = tab["mean"].round(3)
    out.append(tab.reset_index().to_markdown(index=False))
    out.append("")

    # Per-condition horse-race regression
    for cond in ["c1", "c2", "c3"]:
        sub = df[df["condition"] == cond].copy()
        if len(sub) == 0:
            continue
        out.append(f"## Condition {cond.upper()} — horse-race regression")
        out.append("")
        out.append("Each row is one (judge, author, prompt) scoring observation. "
                   "Fixed effects on author, judge, and category absorb mean differences "
                   "between models and task types. HC0 robust standard errors.")
        out.append("")
        # Model A: author_is_self alone
        fit_a = ols_with_dummies(sub,
                                  regressors=["author_is_self"],
                                  fe=["author", "judge", "category"])
        report_coef(f"Model A ({cond.upper()}): composite ~ author_is_self + FE",
                    fit_a, ["author_is_self"], out)
        # Model B: predicted_self alone
        fit_b = ols_with_dummies(sub,
                                  regressors=["predicted_self"],
                                  fe=["author", "judge", "category"])
        report_coef(f"Model B ({cond.upper()}): composite ~ predicted_self + FE",
                    fit_b, ["predicted_self"], out)
        # Model C: both — the horse race
        fit_c = ols_with_dummies(sub,
                                  regressors=["author_is_self", "predicted_self"],
                                  fe=["author", "judge", "category"])
        report_coef(f"Model C ({cond.upper()}): composite ~ author_is_self + predicted_self + FE",
                    fit_c, ["author_is_self", "predicted_self"], out)
        # Interaction: author_is_self × predicted_self
        sub["pred_self_and_true_self"] = sub["author_is_self"] * sub["predicted_self"]
        fit_d = ols_with_dummies(sub,
                                  regressors=["author_is_self", "predicted_self",
                                              "pred_self_and_true_self"],
                                  fe=["author", "judge", "category"])
        report_coef(
            f"Model D ({cond.upper()}): composite ~ author_is_self * predicted_self + FE",
            fit_d, ["author_is_self", "predicted_self", "pred_self_and_true_self"], out)
        out.append("")

    # Off-topic robustness: drop the 11 off-topic prompts
    OFF_TOPIC = [
        "history-001", "philosophy-001",
        "creative-002", "creative-003", "creative-004", "creative-005",
        "explain-001", "explain-002", "explain-003",
        "ethics-001", "ethics-002",
    ]
    out.append("## Off-topic robustness (drop 11 prompts where Kimi K2.6 was off-topic)")
    out.append("")
    out.append("Drops " + ", ".join(OFF_TOPIC) + " — these are the prompts where Kimi K2.6's "
               "original response was off-topic across all three scoring conditions. "
               "Self-preference coefficient should remain positive and similar in magnitude "
               "if it isn't an artifact of Kimi's low scores on these rows.")
    out.append("")
    for cond in ["c1", "c2", "c3"]:
        sub = df[(df["condition"] == cond) & (~df["prompt_id"].isin(OFF_TOPIC))].copy()
        if len(sub) == 0:
            continue
        fit = ols_with_dummies(sub,
                                regressors=["author_is_self"],
                                fe=["author", "judge", "category"])
        # Full-sample comparison
        full = df[df["condition"] == cond]
        full_fit = ols_with_dummies(full,
                                      regressors=["author_is_self"],
                                      fe=["author", "judge", "category"])
        idx_full = full_fit["cols"].index("author_is_self")
        idx_off = fit["cols"].index("author_is_self")
        out.append(f"### {cond.upper()} self-preference robustness")
        out.append("")
        out.append("| sample | N | author_is_self β | SE |")
        out.append("|---|---:|---:|---:|")
        out.append(f"| full | {full_fit['n']} | {full_fit['beta'][idx_full]:+.4f} | {full_fit['se'][idx_full]:.4f} |")
        out.append(f"| drop 11 off-topic | {fit['n']} | {fit['beta'][idx_off]:+.4f} | {fit['se'][idx_off]:.4f} |")
        out.append("")

    text = "\n".join(out)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text)
        print(f"Report written to {args.report}")
    else:
        print(text)


if __name__ == "__main__":
    main()
