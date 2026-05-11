"""Bootstrap 95% CIs for per-judge horse-race coefficients.

Companion to analysis/per_judge_horse_race.py (PR #14). The horse-race shows
strikingly different per-judge profiles — Claude latches onto raw style on every
dimension; GPT-5.5 is driven by predicted authorship with NEGATIVE raw-author
coefficients; Gemini is near-zero everywhere. Are those differences robust, or
are they within sampling noise?

This script resamples prompts with replacement (cluster bootstrap) within each
judge × condition cell, refits the OLS

    score ~ author_is_self + predicted_self + C(author) + C(category)

on the composite, and reports percentile 95% CIs for the two key coefficients
β(author_is_self) and β(predicted_self), per judge × condition.

Pure numpy. No statsmodels. Compatible with analysis/per_judge_horse_race.py.

Usage:
    python3 analysis/horse_race_bootstrap.py --report results/horse_race_bootstrap.md --bootstrap 2000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5"]
JUDGE_LABEL = {
    "claude-opus-4.7": "Claude Opus 4.7",
    "gemini-3.1-pro": "Gemini 3.1 Pro",
    "gpt-5.5": "GPT-5.5",
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
    m["composite"] = m[["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]].mean(axis=1)
    m["author_self"] = (m["author"] == m["judge"]).astype(int)
    m["pred_self"] = (m["predicted_author"] == m["judge"]).astype(int)
    return m


def design(d: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, list[str]]:
    X_df = pd.get_dummies(d[["author", "category"]], drop_first=True).astype(float)
    X_df["author_self"] = d["author_self"].astype(float).values
    X_df["pred_self"] = d["pred_self"].astype(float).values
    X_df.insert(0, "const", 1.0)
    cols = list(X_df.columns)
    return X_df.to_numpy(dtype=float), d["composite"].astype(float).to_numpy(), cols


def fit_ols(X: np.ndarray, y: np.ndarray, cols: list[str]) -> dict[str, float]:
    try:
        beta = np.linalg.pinv(X.T @ X) @ X.T @ y
    except Exception:
        return {"author_self": np.nan, "pred_self": np.nan}
    s = pd.Series(beta, index=cols)
    return {"author_self": float(s.get("author_self", np.nan)),
            "pred_self": float(s.get("pred_self", np.nan))}


def cluster_bootstrap(d: pd.DataFrame, B: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Cluster-bootstrap by prompt_id. Returns arrays of length B with β(author_self), β(pred_self)."""
    prompts = d["prompt_id"].unique()
    n_p = len(prompts)
    # Pre-index rows by prompt
    by_prompt: dict = {}
    for pid in prompts:
        by_prompt[pid] = d[d["prompt_id"] == pid].copy()
    beta_a = np.full(B, np.nan)
    beta_p = np.full(B, np.nan)
    for b in range(B):
        sample = prompts[rng.integers(0, n_p, n_p)]
        rows = [by_prompt[pid] for pid in sample]
        boot = pd.concat(rows, ignore_index=True)
        X, y, cols = design(boot)
        # Drop near-singular columns? Use pinv so it handles it.
        coef = fit_ols(X, y, cols)
        beta_a[b] = coef["author_self"]
        beta_p[b] = coef["pred_self"]
    return beta_a, beta_p


def pct_ci(arr: np.ndarray, alpha: float = 0.05) -> tuple[float, float]:
    arr = arr[np.isfinite(arr)]
    if len(arr) < 10:
        return (np.nan, np.nan)
    lo = np.percentile(arr, 100 * alpha / 2)
    hi = np.percentile(arr, 100 * (1 - alpha / 2))
    return float(lo), float(hi)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--report", type=Path, default=ROOT / "results" / "horse_race_bootstrap.md")
    p.add_argument("--bootstrap", type=int, default=2000)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    df = load(ROOT)
    rng = np.random.default_rng(args.seed)

    lines: list[str] = []
    def emit(s: str = ""):
        print(s)
        lines.append(s)

    emit("# Per-judge horse-race: cluster-bootstrap 95% CIs")
    emit("")
    emit(f"Resampling B={args.bootstrap} cluster bootstraps over prompt_id within each judge × "
         f"condition cell. Model: `composite ~ author_is_self + predicted_self + C(author) + C(category)` "
         f"(OLS via pseudo-inverse, no statsmodels). Reports percentile 95% CI on the two "
         f"key coefficients. Companion to `analysis/per_judge_horse_race.py`.")
    emit("")

    for cond in ["c1", "c2", "c3"]:
        emit(f"## Condition {cond.upper()}")
        emit("")
        emit("| Judge | β(author_is_self) point | 95% CI | β(predicted_self) point | 95% CI | N |")
        emit("|---|---:|---|---:|---|---:|")
        for j in JUDGES:
            d = df[(df["judge"] == j) & (df["condition"] == cond)].copy()
            if len(d) < 20:
                emit(f"| {JUDGE_LABEL[j]} | – | – | – | – | {len(d)} |")
                continue
            X, y, cols = design(d)
            pt = fit_ols(X, y, cols)
            ba, bp = cluster_bootstrap(d, args.bootstrap, rng)
            lo_a, hi_a = pct_ci(ba)
            lo_p, hi_p = pct_ci(bp)
            emit(f"| {JUDGE_LABEL[j]} | {pt['author_self']:+.2f} | [{lo_a:+.2f}, {hi_a:+.2f}] | "
                 f"{pt['pred_self']:+.2f} | [{lo_p:+.2f}, {hi_p:+.2f}] | {len(d)} |")
        emit("")

    # Direct test: are the per-judge author_is_self coefficients different?
    # Compute β_claude - β_gpt55 per bootstrap iteration in C1.
    emit("## Are the per-judge profiles statistically different? (C1 only)")
    emit("")
    emit("Joint bootstrap: resample prompts once per iteration, refit all three "
         "judges, take differences. Same prompt set per iteration so paired comparison "
         "is valid.")
    emit("")

    # Joint cluster bootstrap across judges in C1
    d_c1 = df[df["condition"] == "c1"].copy()
    prompts = d_c1["prompt_id"].unique()
    n_p = len(prompts)
    by_prompt = {pid: d_c1[d_c1["prompt_id"] == pid].copy() for pid in prompts}
    diffs: dict[str, list[float]] = {
        "claude_minus_gpt_auth": [],
        "claude_minus_gemini_auth": [],
        "gpt_minus_gemini_auth": [],
        "claude_minus_gpt_pred": [],
        "claude_minus_gemini_pred": [],
        "gpt_minus_gemini_pred": [],
    }
    for b in range(args.bootstrap):
        sample = prompts[rng.integers(0, n_p, n_p)]
        rows = [by_prompt[pid] for pid in sample]
        boot = pd.concat(rows, ignore_index=True)
        per: dict[str, dict[str, float]] = {}
        ok = True
        for j in JUDGES:
            sub = boot[boot["judge"] == j]
            if len(sub) < 10:
                ok = False; break
            X, y, cols = design(sub)
            per[j] = fit_ols(X, y, cols)
        if not ok:
            continue
        diffs["claude_minus_gpt_auth"].append(per["claude-opus-4.7"]["author_self"] - per["gpt-5.5"]["author_self"])
        diffs["claude_minus_gemini_auth"].append(per["claude-opus-4.7"]["author_self"] - per["gemini-3.1-pro"]["author_self"])
        diffs["gpt_minus_gemini_auth"].append(per["gpt-5.5"]["author_self"] - per["gemini-3.1-pro"]["author_self"])
        diffs["claude_minus_gpt_pred"].append(per["claude-opus-4.7"]["pred_self"] - per["gpt-5.5"]["pred_self"])
        diffs["claude_minus_gemini_pred"].append(per["claude-opus-4.7"]["pred_self"] - per["gemini-3.1-pro"]["pred_self"])
        diffs["gpt_minus_gemini_pred"].append(per["gpt-5.5"]["pred_self"] - per["gemini-3.1-pro"]["pred_self"])

    emit("| Difference | Bootstrap mean | 95% CI | Excludes 0? |")
    emit("|---|---:|---|:---:|")
    for k, arr in diffs.items():
        a = np.array(arr)
        if len(a) == 0:
            emit(f"| {k} | – | – | – |"); continue
        lo, hi = pct_ci(a)
        excl = "✓" if (lo > 0 or hi < 0) else "—"
        emit(f"| {k.replace('_', ' ')} | {a.mean():+.2f} | [{lo:+.2f}, {hi:+.2f}] | {excl} |")
    emit("")

    emit("## Interpretation")
    emit("")
    emit("The point estimates from `per_judge_horse_race.py` suggested Claude is "
         "driven primarily by raw-author style, GPT-5.5 by perceived authorship with "
         "a counter-acting negative raw-author effect, and Gemini is null on both "
         "axes. Cluster-bootstrap 95% CIs show whether these differences are robust "
         "or within sampling noise. CIs that exclude zero in the difference table "
         "above mean the per-judge profiles are statistically distinguishable.")

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines) + "\n")
    print(f"\nWrote {args.report}")


if __name__ == "__main__":
    main()
