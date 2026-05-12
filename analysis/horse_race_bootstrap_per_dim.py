"""Per-dimension cluster-bootstrap 95% CIs on the horse-race coefficients.

PR #27 reported bootstrap CIs only on the composite score. PR #14 (per-judge
horse-race) already showed striking *per-dimension* patterns:
  - Claude's raw-style coefficient is uniform across all 5 dims.
  - GPT-5.5's negative raw-author + positive predicted-author signature
    appears on every dim but is largest on correctness/completeness/constraint.
  - The clarity/creativity (form) vs correctness/completeness/constraint (content)
    dissociation from PR #10 is a pooled-judge statement; we should check
    whether the dissociation is itself stable under resampling.

This script resamples prompts with replacement (cluster bootstrap) within each
judge × condition cell and refits

    score_DIM ~ author_is_self + predicted_self + C(author) + C(category)

separately for each of the five rubric dimensions: correctness, completeness,
clarity, creativity, constraint_adherence. It reports percentile 95% CIs on
β(author_is_self) and β(predicted_self) for every (dim, judge, cond) cell.

Pure numpy. No statsmodels.

Usage:
    python3 analysis/horse_race_bootstrap_per_dim.py \
        --report results/horse_race_bootstrap_per_dim.md --bootstrap 500
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
JUDGE_LABEL = {
    "claude-opus-4.7": "Claude Opus 4.7",
    "gemini-3.1-pro": "Gemini 3.1 Pro",
    "gpt-5.5": "GPT-5.5",
    "kimi-k2.6": "Kimi K2.6",
}
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
DIM_LABEL = {
    "correctness": "Correctness",
    "completeness": "Completeness",
    "clarity": "Clarity",
    "creativity": "Creativity",
    "constraint_adherence": "Constraint adherence",
}


def load(repo: Path) -> pd.DataFrame:
    scores, recs = [], []
    for j in JUDGES:
        sp = repo / "data" / "judgments" / j / "long_scores.csv"
        rp = repo / "data" / "judgments" / j / "long_recognition.csv"
        if not sp.exists() or not rp.exists():
            print(f"WARN: missing {j}", file=sys.stderr)
            continue
        scores.append(pd.read_csv(sp))
        recs.append(pd.read_csv(rp))
    sc = pd.concat(scores, ignore_index=True)
    rec = pd.concat(recs, ignore_index=True).rename(columns={"true_author": "author"})
    m = sc.merge(
        rec[["judge", "author", "prompt_id", "predicted_author"]],
        on=["judge", "author", "prompt_id"],
        how="left",
    )
    m["author_self"] = (m["author"] == m["judge"]).astype(int)
    m["pred_self"] = (m["predicted_author"] == m["judge"]).astype(int)
    return m


def design(d: pd.DataFrame, y_col: str) -> tuple[np.ndarray, np.ndarray, list[str]]:
    X_df = pd.get_dummies(d[["author", "category"]], drop_first=True).astype(float)
    X_df["author_self"] = d["author_self"].astype(float).values
    X_df["pred_self"] = d["pred_self"].astype(float).values
    X_df.insert(0, "const", 1.0)
    cols = list(X_df.columns)
    return X_df.to_numpy(dtype=float), d[y_col].astype(float).to_numpy(), cols


def fit_ols(X: np.ndarray, y: np.ndarray, cols: list[str]) -> dict[str, float]:
    try:
        beta = np.linalg.pinv(X.T @ X) @ X.T @ y
    except Exception:
        return {"author_self": np.nan, "pred_self": np.nan}
    s = pd.Series(beta, index=cols)
    return {
        "author_self": float(s.get("author_self", np.nan)),
        "pred_self": float(s.get("pred_self", np.nan)),
    }


def pct_ci(arr: np.ndarray, alpha: float = 0.05) -> tuple[float, float]:
    arr = arr[np.isfinite(arr)]
    if len(arr) < 10:
        return (np.nan, np.nan)
    return (
        float(np.percentile(arr, 100 * alpha / 2)),
        float(np.percentile(arr, 100 * (1 - alpha / 2))),
    )


def bootstrap_cell(d: pd.DataFrame, y_col: str, B: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    prompts = d["prompt_id"].unique()
    n_p = len(prompts)
    by_prompt = {pid: d[d["prompt_id"] == pid] for pid in prompts}
    a = np.full(B, np.nan)
    p = np.full(B, np.nan)
    for b in range(B):
        sample = prompts[rng.integers(0, n_p, n_p)]
        rows = [by_prompt[pid] for pid in sample]
        boot = pd.concat(rows, ignore_index=True)
        X, y, cols = design(boot, y_col)
        coef = fit_ols(X, y, cols)
        a[b] = coef["author_self"]
        p[b] = coef["pred_self"]
    return a, p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", type=Path, default=ROOT / "results" / "horse_race_bootstrap_per_dim.md")
    ap.add_argument("--bootstrap", type=int, default=500)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    df = load(ROOT)
    rng = np.random.default_rng(args.seed)

    lines: list[str] = []

    def emit(s: str = ""):
        print(s)
        lines.append(s)

    emit("# Per-dimension horse-race: cluster-bootstrap 95% CIs")
    emit("")
    emit(
        f"For each of the five rubric dimensions, cluster-bootstrap by prompt_id "
        f"(B={args.bootstrap}) within every judge × condition cell, refit "
        f"`score_DIM ~ author_is_self + predicted_self + C(author) + C(category)` "
        f"(OLS via pseudo-inverse, pure numpy), and report percentile 95% CIs on "
        f"β(author_is_self) and β(predicted_self). Companion to "
        f"`analysis/per_judge_horse_race.py` and `analysis/horse_race_bootstrap.py` "
        f"(the latter is the composite-only version)."
    )
    emit("")

    # Use a fresh RNG per cell for reproducibility.
    for cond in ["c1", "c2", "c3"]:
        emit(f"## Condition {cond.upper()}")
        emit("")
        for dim in DIMS:
            emit(f"### {DIM_LABEL[dim]}")
            emit("")
            emit("| Judge | β(author_is_self) | 95% CI | β(predicted_self) | 95% CI | N |")
            emit("|---|---:|---|---:|---|---:|")
            for j in JUDGES:
                d = df[(df["judge"] == j) & (df["condition"] == cond)].copy()
                if len(d) < 20:
                    emit(f"| {JUDGE_LABEL[j]} | – | – | – | – | {len(d)} |")
                    continue
                X, y, cols = design(d, dim)
                pt = fit_ols(X, y, cols)
                a, p = bootstrap_cell(d, dim, args.bootstrap, rng)
                lo_a, hi_a = pct_ci(a)
                lo_p, hi_p = pct_ci(p)
                excl_a = "✓" if (lo_a > 0 or hi_a < 0) else "—"
                excl_p = "✓" if (lo_p > 0 or hi_p < 0) else "—"
                emit(
                    f"| {JUDGE_LABEL[j]} | {pt['author_self']:+.2f} | [{lo_a:+.2f}, {hi_a:+.2f}] {excl_a} | "
                    f"{pt['pred_self']:+.2f} | [{lo_p:+.2f}, {hi_p:+.2f}] {excl_p} | {len(d)} |"
                )
            emit("")

    emit("## Interpretation")
    emit("")
    emit(
        "**Content vs form dissociation (PR #10) was a *pooled-judge* finding.** The "
        "per-judge × per-dimension bootstrap CIs let us check whether it holds within "
        "each judge or whether it's an artefact of averaging different judge profiles. "
        "If Claude's raw-author β > 0 on clarity/creativity *and* on correctness/"
        "completeness/constraint, the dissociation is judge-specific rather than universal."
    )
    emit("")
    emit(
        "**A coefficient whose 95% CI excludes zero (marked ✓)** is robustly nonzero "
        "after cluster resampling over prompts; coefficients marked — are within "
        "sampling noise. Note: B is small relative to the composite bootstrap (500 vs "
        "2000) because we now run 5×3×4 = 60 cells, each costing one full refit per "
        "iteration; widening B is a matter of compute."
    )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines) + "\n")
    print(f"\nWrote {args.report}")


if __name__ == "__main__":
    main()
