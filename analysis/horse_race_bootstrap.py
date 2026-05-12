"""Bootstrap 95% CIs for per-judge horse-race coefficients.

For each available judge × condition cell, cluster-resample prompts with
replacement and refit:

    composite ~ author_is_self + predicted_self + C(author) + C(category)

using a pure NumPy pseudo-inverse OLS. The report gives percentile 95% CIs for
β(author_is_self) and β(predicted_self), plus paired C1 differences between all
available judges.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
JUDGE_LABEL = {
    "claude-opus-4.7": "Claude Opus 4.7",
    "gemini-3.1-pro": "Gemini 3.1 Pro",
    "gpt-5.5": "GPT-5.5",
    "kimi-k2.6": "Kimi K2.6",
}


def available_judges(repo: Path) -> list[str]:
    return [j for j in DEFAULT_JUDGES if (repo / "data" / "judgments" / j).is_dir()]


def load(repo: Path, judges: list[str]) -> pd.DataFrame:
    scores, recs = [], []
    for j in judges:
        sp = repo / "data" / "judgments" / j / "long_scores.csv"
        rp = repo / "data" / "judgments" / j / "long_recognition.csv"
        if not sp.exists() or not rp.exists():
            print(f"WARN: missing {j}", file=sys.stderr)
            continue
        scores.append(pd.read_csv(sp))
        recs.append(pd.read_csv(rp))
    if not scores or not recs:
        raise SystemExit("No judgment data found")
    sc = pd.concat(scores, ignore_index=True)
    rec = pd.concat(recs, ignore_index=True).rename(columns={"true_author": "author"})
    m = sc.merge(rec[["judge", "author", "prompt_id", "predicted_author"]], on=["judge", "author", "prompt_id"], how="left")
    dims = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
    m["composite"] = m[dims].mean(axis=1)
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
    beta = np.linalg.pinv(X.T @ X) @ X.T @ y
    s = pd.Series(beta, index=cols)
    return {"author_self": float(s.get("author_self", np.nan)), "pred_self": float(s.get("pred_self", np.nan))}


def cluster_bootstrap(d: pd.DataFrame, B: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    prompts = d["prompt_id"].unique()
    by_prompt = {pid: d[d["prompt_id"] == pid].copy() for pid in prompts}
    beta_a = np.full(B, np.nan)
    beta_p = np.full(B, np.nan)
    for i in range(B):
        sample = prompts[rng.integers(0, len(prompts), len(prompts))]
        boot = pd.concat([by_prompt[pid] for pid in sample], ignore_index=True)
        X, y, cols = design(boot)
        coef = fit_ols(X, y, cols)
        beta_a[i] = coef["author_self"]
        beta_p[i] = coef["pred_self"]
    return beta_a, beta_p


def pct_ci(arr: np.ndarray, alpha: float = 0.05) -> tuple[float, float]:
    arr = arr[np.isfinite(arr)]
    if len(arr) < 10:
        return (np.nan, np.nan)
    return float(np.percentile(arr, 100 * alpha / 2)), float(np.percentile(arr, 100 * (1 - alpha / 2)))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--report", type=Path, default=ROOT / "results" / "horse_race_bootstrap.md")
    p.add_argument("--bootstrap", type=int, default=2000)
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    judges = available_judges(ROOT)
    df = load(ROOT, judges)
    rng = np.random.default_rng(args.seed)
    lines: list[str] = []
    def emit(s: str = "") -> None:
        print(s); lines.append(s)

    emit("# Per-judge horse-race: cluster-bootstrap 95% CIs")
    emit("")
    emit(f"Available judges: {', '.join(JUDGE_LABEL.get(j, j) for j in judges)}.")
    emit(f"Resampling B={args.bootstrap} cluster bootstraps over prompt_id within each judge × condition cell. Model: `composite ~ author_is_self + predicted_self + C(author) + C(category)` (OLS via pseudo-inverse, no statsmodels).")
    emit("")
    for cond in ["c1", "c2", "c3"]:
        emit(f"## Condition {cond.upper()}")
        emit("")
        emit("| Judge | β(author_is_self) point | 95% CI | β(predicted_self) point | 95% CI | N |")
        emit("|---|---:|---|---:|---|---:|")
        for j in judges:
            d = df[(df["judge"] == j) & (df["condition"] == cond)].copy()
            X, y, cols = design(d)
            pt = fit_ols(X, y, cols)
            ba, bp = cluster_bootstrap(d, args.bootstrap, rng)
            lo_a, hi_a = pct_ci(ba); lo_p, hi_p = pct_ci(bp)
            emit(f"| {JUDGE_LABEL.get(j, j)} | {pt['author_self']:+.2f} | [{lo_a:+.2f}, {hi_a:+.2f}] | {pt['pred_self']:+.2f} | [{lo_p:+.2f}, {hi_p:+.2f}] | {len(d)} |")
        emit("")
    emit("## Are the per-judge profiles statistically different? (C1 only)")
    emit("")
    emit("Joint bootstrap: resample prompts once per iteration, refit all available judges, and take paired differences. Same prompt set per iteration so paired comparison is valid.")
    emit("")
    d_c1 = df[df["condition"] == "c1"].copy()
    prompts = d_c1["prompt_id"].unique()
    by_prompt = {pid: d_c1[d_c1["prompt_id"] == pid].copy() for pid in prompts}
    pairs = [(a, b) for i, a in enumerate(judges) for b in judges[i+1:]]
    diffs = {f"{a}|{b}|auth": [] for a, b in pairs}
    diffs.update({f"{a}|{b}|pred": [] for a, b in pairs})
    for _ in range(args.bootstrap):
        sample = prompts[rng.integers(0, len(prompts), len(prompts))]
        boot = pd.concat([by_prompt[pid] for pid in sample], ignore_index=True)
        per = {}
        for j in judges:
            sub = boot[boot["judge"] == j]
            X, y, cols = design(sub)
            per[j] = fit_ols(X, y, cols)
        for a, b in pairs:
            diffs[f"{a}|{b}|auth"].append(per[a]["author_self"] - per[b]["author_self"])
            diffs[f"{a}|{b}|pred"].append(per[a]["pred_self"] - per[b]["pred_self"])
    emit("| Difference | Bootstrap mean | 95% CI | Excludes 0? |")
    emit("|---|---:|---|:---:|")
    for k, arr in diffs.items():
        left, right, kind = k.split("|")
        arr = np.array(arr); lo, hi = pct_ci(arr)
        excl = "✓" if (lo > 0 or hi < 0) else "—"
        emit(f"| {JUDGE_LABEL.get(left, left)} minus {JUDGE_LABEL.get(right, right)} {kind} | {arr.mean():+.2f} | [{lo:+.2f}, {hi:+.2f}] | {excl} |")
    emit("")
    emit("## Interpretation")
    emit("")
    emit("The per-judge horse-race profiles are highly heterogeneous. The bootstrap CIs quantify which raw-author (`author_is_self`) and perceived-authorship (`predicted_self`) coefficients, and which between-judge contrasts, are stable under prompt-level resampling.")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(lines) + "\n")
    print(f"\nWrote {args.report}")

if __name__ == "__main__":
    main()
