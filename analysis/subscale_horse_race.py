#!/usr/bin/env python3
"""
Subscale × condition horse-race: predicted_self vs style_prob_self per rubric dim.

For each (dimension D, condition C) cell (5 dims × 3 conditions = 15 cells):
  Y = score for (D,C)
  T = author_is_self
  M1 = predicted_self            (binary, verbalised belief from C4 probe)
  M2 = style_prob_self           (continuous, stylometric LR prob, from PR #60)

Fits:
  Y ~ T            -> c    (total effect)
  M1 ~ T           -> a1
  M2 ~ T           -> a2
  Y ~ T + M1 + M2  -> c', b1, b2

Indirects: a1*b1 (belief channel), a2*b2 (style channel).
Bootstrap: 2000 iter, cluster on prompt_id, seed 20260512.

Inputs:
  - data/unified/unified_long.csv
  - data/derived/style_prob_self.csv

Outputs:
  - results/subscale_horse_race.csv
  - results/subscale_horse_race_report.md
"""
import os
import sys
import numpy as np
import pandas as pd

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SEED = 20260512
B = 2000
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
CONDS = ["c1", "c2", "c3"]


OFF_TOPIC = [
    "history-001", "philosophy-001",
    "creative-002", "creative-003", "creative-004", "creative-005",
    "explain-001", "explain-002", "explain-003",
    "ethics-001", "ethics-002",
]


def ols(X, y):
    """Plain OLS via lstsq. Returns coef vector (incl intercept as first elem)."""
    X1 = np.column_stack([np.ones(len(y)), X])
    coef, *_ = np.linalg.lstsq(X1, y, rcond=None)
    return coef


def fit_cell(df):
    """Returns dict of point estimates for one (dim, cond) cell."""
    y = df["score"].to_numpy(dtype=float)
    T = df["author_is_self"].to_numpy(dtype=float)
    M1 = df["predicted_self"].to_numpy(dtype=float)
    M2 = df["style_prob_self"].to_numpy(dtype=float)
    # c
    c = ols(T.reshape(-1, 1), y)[1]
    # a1, a2
    a1 = ols(T.reshape(-1, 1), M1)[1]
    a2 = ols(T.reshape(-1, 1), M2)[1]
    # c', b1, b2
    X = np.column_stack([T, M1, M2])
    coef = ols(X, y)
    c_prime, b1, b2 = coef[1], coef[2], coef[3]
    return {
        "c": c, "c_prime": c_prime,
        "a1": a1, "a2": a2,
        "b1": b1, "b2": b2,
        "indirect_pred": a1 * b1,
        "indirect_style": a2 * b2,
    }


def cluster_bootstrap(df, n_iter=B, seed=SEED):
    """Cluster bootstrap on prompt_id, with replacement.
    Returns dict of arrays of bootstrap replicates."""
    rng = np.random.default_rng(seed)
    prompts = df["prompt_id"].unique()
    # group rows by prompt
    groups = {p: df[df["prompt_id"] == p] for p in prompts}
    n_p = len(prompts)
    keys = ["c", "c_prime", "a1", "a2", "b1", "b2", "indirect_pred", "indirect_style"]
    out = {k: np.empty(n_iter) for k in keys}
    for i in range(n_iter):
        idx = rng.integers(0, n_p, size=n_p)
        boot_frames = [groups[prompts[j]] for j in idx]
        boot_df = pd.concat(boot_frames, ignore_index=True)
        try:
            est = fit_cell(boot_df)
            for k in keys:
                out[k][i] = est[k]
        except Exception:
            for k in keys:
                out[k][i] = np.nan
    return out


def ci(arr, lo=2.5, hi=97.5):
    arr = arr[~np.isnan(arr)]
    if len(arr) == 0:
        return (np.nan, np.nan)
    return (np.percentile(arr, lo), np.percentile(arr, hi))


def fmt_ci(point, lo, hi):
    return f"{point:+.3f} [{lo:+.3f}, {hi:+.3f}]"


def main():
    print("Loading data...")
    df_long = pd.read_csv(os.path.join(REPO, "data/unified/unified_long.csv"))
    df_style = pd.read_csv(os.path.join(REPO, "data/derived/style_prob_self.csv"))
    # Merge on (judge, author, prompt_id, condition)
    merge_keys = ["judge", "author", "prompt_id", "condition"]
    df = df_long.merge(
        df_style[merge_keys + ["style_prob_self"]],
        on=merge_keys, how="inner",
    )
    df = df[df["condition"].isin(CONDS)].copy()
    print(f"Merged N = {len(df)} rows ({len(df)//5} unique scores × 5 dims)")

    rows = []
    for dim in DIMS:
        for cond in CONDS:
            sub = df[(df["dimension"] == dim) & (df["condition"] == cond)].copy()
            n = len(sub)
            est = fit_cell(sub)
            print(f"  {dim:>22s} × {cond}: N={n}  c={est['c']:+.3f}  "
                  f"c'={est['c_prime']:+.3f}  a1b1={est['indirect_pred']:+.3f}  "
                  f"a2b2={est['indirect_style']:+.3f}")
            boot = cluster_bootstrap(sub)
            row = {
                "dimension": dim, "condition": cond, "N": n,
                "c": est["c"], "c_lo": ci(boot["c"])[0], "c_hi": ci(boot["c"])[1],
                "c_prime": est["c_prime"],
                "c_prime_lo": ci(boot["c_prime"])[0], "c_prime_hi": ci(boot["c_prime"])[1],
                "a1": est["a1"], "b1": est["b1"],
                "indirect_pred": est["indirect_pred"],
                "indirect_pred_lo": ci(boot["indirect_pred"])[0],
                "indirect_pred_hi": ci(boot["indirect_pred"])[1],
                "a2": est["a2"], "b2": est["b2"],
                "indirect_style": est["indirect_style"],
                "indirect_style_lo": ci(boot["indirect_style"])[0],
                "indirect_style_hi": ci(boot["indirect_style"])[1],
                "b1_lo": ci(boot["b1"])[0], "b1_hi": ci(boot["b1"])[1],
                "b2_lo": ci(boot["b2"])[0], "b2_hi": ci(boot["b2"])[1],
            }
            rows.append(row)

    out_df = pd.DataFrame(rows)
    csv_path = os.path.join(REPO, "results/subscale_horse_race.csv")
    out_df.to_csv(csv_path, index=False)
    print(f"\nWrote {csv_path}")

    # Write markdown report
    md = []
    md.append("# Subscale × condition horse-race: belief vs style channel\n")
    md.append("**Design.** For each rubric dimension D (correctness, completeness, "
              "clarity, creativity, constraint_adherence) and each scoring condition C "
              "(C1 baseline, C2 paraphrased, C3 warned), we fit the two-mediator "
              "horse-race used in PR #60:\n")
    md.append("```\n"
              "Y_D ~ T (author_is_self)  →  c\n"
              "M1  ~ T                   →  a1   (M1 = predicted_self, verbalised belief from C4)\n"
              "M2  ~ T                   →  a2   (M2 = style_prob_self, stylometric LR prob)\n"
              "Y_D ~ T + M1 + M2         →  c', b1, b2\n"
              "```\n")
    md.append("Indirect via belief = a1·b1; indirect via style = a2·b2. "
              "95% CIs from 2000-iter cluster bootstrap on `prompt_id`, seed 20260512. "
              "N per cell = 480 (4 judges × 4 authors × 30 prompts). "
              "Pooled across judges; per-judge heterogeneity is not modeled in this subscale table.\n")
    md.append("\n**Scope caveat.** This is an exploratory observed-variable "
              "mediation-style decomposition, not an identified causal mediation design. "
              "`predicted_self` was measured later in C4 rather than manipulated, "
              "`style_prob_self` is only an 11-feature lightweight stylometric proxy, "
              "and the bootstrap intervals are descriptive uncertainty summaries for "
              "these cells rather than proof of a transportable mechanism.\n")

    for cond in CONDS:
        sub = out_df[out_df["condition"] == cond]
        md.append(f"\n## {cond.upper()}\n")
        md.append("| Dimension | c (total) | c' (direct) | a1·b1 (belief) | a2·b2 (style) | b1 | b2 |")
        md.append("|---|---:|---:|---:|---:|---:|---:|")
        for _, r in sub.iterrows():
            md.append(
                f"| {r['dimension']} | "
                f"{fmt_ci(r['c'], r['c_lo'], r['c_hi'])} | "
                f"{fmt_ci(r['c_prime'], r['c_prime_lo'], r['c_prime_hi'])} | "
                f"{fmt_ci(r['indirect_pred'], r['indirect_pred_lo'], r['indirect_pred_hi'])} | "
                f"{fmt_ci(r['indirect_style'], r['indirect_style_lo'], r['indirect_style_hi'])} | "
                f"{fmt_ci(r['b1'], r['b1_lo'], r['b1_hi'])} | "
                f"{fmt_ci(r['b2'], r['b2_lo'], r['b2_hi'])} |"
            )

    # Headlines section
    md.append("\n## Headlines\n")

    def sig(row, key):
        lo, hi = row[f"{key}_lo"], row[f"{key}_hi"]
        return (lo > 0) or (hi < 0)

    # 1. Largest |belief indirect|
    abs_pred = out_df.assign(absind=out_df["indirect_pred"].abs())
    top_pred = abs_pred.sort_values("absind", ascending=False).head(3)
    md.append("- **Largest belief-channel indirect (|a1·b1|):**")
    for _, r in top_pred.iterrows():
        md.append(
            f"  - {r['condition'].upper()} × {r['dimension']}: "
            f"{fmt_ci(r['indirect_pred'], r['indirect_pred_lo'], r['indirect_pred_hi'])}"
        )

    abs_style = out_df.assign(absind=out_df["indirect_style"].abs())
    top_style = abs_style.sort_values("absind", ascending=False).head(3)
    md.append("- **Largest style-channel indirect (|a2·b2|):**")
    for _, r in top_style.iterrows():
        md.append(
            f"  - {r['condition'].upper()} × {r['dimension']}: "
            f"{fmt_ci(r['indirect_style'], r['indirect_style_lo'], r['indirect_style_hi'])}"
        )

    # Sign of belief vs style per cell
    md.append("- **Sign opposition (belief positive, style negative) — cells where CI of belief excludes 0 above AND CI of style excludes 0 below:**")
    opp = out_df[
        (out_df["indirect_pred_lo"] > 0) & (out_df["indirect_style_hi"] < 0)
    ]
    if len(opp) == 0:
        md.append("  - (none reach significance in both directions simultaneously)")
    else:
        for _, r in opp.iterrows():
            md.append(
                f"  - {r['condition'].upper()} × {r['dimension']}: "
                f"belief {fmt_ci(r['indirect_pred'], r['indirect_pred_lo'], r['indirect_pred_hi'])}; "
                f"style {fmt_ci(r['indirect_style'], r['indirect_style_lo'], r['indirect_style_hi'])}"
            )

    md.append("- **Both channels POS (both CIs > 0):**")
    both_pos = out_df[(out_df["indirect_pred_lo"] > 0) & (out_df["indirect_style_lo"] > 0)]
    if len(both_pos) == 0:
        md.append("  - (none)")
    else:
        for _, r in both_pos.iterrows():
            md.append(f"  - {r['condition'].upper()} × {r['dimension']}")

    md.append("\n_Source: `analysis/subscale_horse_race.py`, generated D406._\n")
    md_path = os.path.join(REPO, "results/subscale_horse_race_report.md")
    with open(md_path, "w") as f:
        f.write("\n".join(md))
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
