"""Formal causal mediation analysis: does perceived authorship mediate self-preference?

For each condition (C1, C2, C3) and pooled / per-judge:
- Total effect c:  Y ~ T            (Y=composite, T=author_is_self)
- Path a:          M ~ T            (M=predicted_self; linear prob. model)
- Direct + b:      Y ~ T + M
- Indirect effect: a * b, with 2000-iter cluster bootstrap by prompt_id (95% percentile CI).

Outputs results/formal_mediation.csv and results/formal_mediation_report.md.
"""
from __future__ import annotations
import csv
import math
from pathlib import Path
from collections import defaultdict
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "unified" / "unified_wide.csv"
OUT_CSV = ROOT / "results" / "formal_mediation.csv"
OUT_MD = ROOT / "results" / "formal_mediation_report.md"

rng = np.random.default_rng(20260512)

# --- Load ---
rows = []
with DATA.open() as f:
    for r in csv.DictReader(f):
        rows.append(r)

def ols(y: np.ndarray, X: np.ndarray) -> np.ndarray:
    """Plain OLS coefficients (no SEs). X must include intercept column."""
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    return coef

def fit_paths(T: np.ndarray, M: np.ndarray, Y: np.ndarray) -> dict:
    """Return c (total), a (T→M), b (M→Y|T), c_prime (T→Y|M), indirect=a*b."""
    n = len(Y)
    X1 = np.column_stack([np.ones(n), T])
    c = ols(Y, X1)[1]
    a = ols(M, X1)[1]  # linear prob. model for M
    X2 = np.column_stack([np.ones(n), T, M])
    co = ols(Y, X2)
    c_prime = co[1]
    b = co[2]
    return {"c": c, "a": a, "b": b, "c_prime": c_prime, "indirect": a * b}

def cluster_bootstrap(T, M, Y, clusters, B=2000) -> dict:
    """Cluster bootstrap by prompt_id; return 95% percentile CIs."""
    keys = np.array(clusters)
    unique = np.unique(keys)
    # precompute index lists per cluster
    idx_by_cluster = {k: np.where(keys == k)[0] for k in unique}
    point = fit_paths(T, M, Y)
    boots = {k: [] for k in ["c", "a", "b", "c_prime", "indirect"]}
    for _ in range(B):
        sampled = rng.choice(unique, size=len(unique), replace=True)
        idx = np.concatenate([idx_by_cluster[k] for k in sampled])
        Tb, Mb, Yb = T[idx], M[idx], Y[idx]
        if Tb.std() == 0 or Mb.std() == 0:
            continue
        try:
            est = fit_paths(Tb, Mb, Yb)
        except np.linalg.LinAlgError:
            continue
        for k, v in est.items():
            boots[k].append(v)
    cis = {}
    for k, arr in boots.items():
        arr = np.array(arr)
        if len(arr) == 0:
            cis[k] = (np.nan, np.nan, 0)
            continue
        cis[k] = (float(np.percentile(arr, 2.5)),
                  float(np.percentile(arr, 97.5)),
                  len(arr))
    return {"point": point, "ci": cis}

def subset(rows, **kw):
    out = []
    for r in rows:
        ok = True
        for k, v in kw.items():
            if r[k] != v:
                ok = False
                break
        if ok:
            out.append(r)
    return out

def arrays(rs):
    Y = np.array([float(r["composite"]) for r in rs])
    T = np.array([int(r["author_is_self"]) for r in rs])
    M = np.array([int(r["predicted_self"]) for r in rs])
    cl = [r["prompt_id"] for r in rs]
    return T, M, Y, cl

judges = sorted({r["judge"] for r in rows})
conds = ["c1", "c2", "c3"]

results = []
print(f"N total rows: {len(rows)}")

for cond in conds:
    # pooled
    rs = [r for r in rows if r["condition"] == cond]
    T, M, Y, cl = arrays(rs)
    res = cluster_bootstrap(T, M, Y, cl, B=2000)
    results.append({
        "scope": "pooled",
        "condition": cond,
        "n": len(rs),
        **{f"{k}_est": res["point"][k] for k in res["point"]},
        **{f"{k}_lo": res["ci"][k][0] for k in res["ci"]},
        **{f"{k}_hi": res["ci"][k][1] for k in res["ci"]},
    })
    for j in judges:
        rs = [r for r in rows if r["condition"] == cond and r["judge"] == j]
        T, M, Y, cl = arrays(rs)
        res = cluster_bootstrap(T, M, Y, cl, B=2000)
        results.append({
            "scope": j,
            "condition": cond,
            "n": len(rs),
            **{f"{k}_est": res["point"][k] for k in res["point"]},
            **{f"{k}_lo": res["ci"][k][0] for k in res["ci"]},
            **{f"{k}_hi": res["ci"][k][1] for k in res["ci"]},
        })

# Write CSV
keys = list(results[0].keys())
with OUT_CSV.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    for r in results:
        w.writerow({k: (f"{r[k]:.4f}" if isinstance(r[k], float) else r[k]) for k in keys})

# Markdown report
lines = ["# Formal causal mediation analysis", "",
         "**Question.** Does perceived authorship (`predicted_self`) mediate the effect of "
         "actual authorship (`author_is_self`) on composite score?",
         "",
         "**Method.** Per condition × scope, we estimate:",
         "",
         "- `c`  = total effect (Y ~ T)",
         "- `a`  = T → M (linear probability model; coefficient is in probability units)",
         "- `b`  = effect of M on Y, holding T fixed (Y ~ T + M)",
         "- `c'` = direct effect of T on Y, holding M fixed (Y ~ T + M)",
         "- `indirect` = a × b (product-of-coefficients estimator)",
         "",
         "95% CIs are from a 2,000-iteration cluster bootstrap resampling prompt_ids.",
         "",
         "**Sanity check.** c ≈ c' + indirect by OLS identity.",
         ""]

# Format per condition
for cond in conds:
    lines.append(f"## Condition {cond.upper()}")
    lines.append("")
    lines.append("| Scope | N | c (total) | c' (direct) | a (T→M) | b (M→Y|T) | indirect (a·b) |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for r in results:
        if r["condition"] != cond:
            continue
        def fmt(k):
            lo = r.get(f"{k}_lo", float('nan'))
            hi = r.get(f"{k}_hi", float('nan'))
            est = r[f"{k}_est"]
            return f"{est:+.3f} [{lo:+.3f}, {hi:+.3f}]"
        lines.append(f"| {r['scope']} | {r['n']} | {fmt('c')} | {fmt('c_prime')} | "
                     f"{fmt('a')} | {fmt('b')} | {fmt('indirect')} |")
    lines.append("")

lines.append("**Interpretation notes**")
lines.append("")
lines.append("- A CI for `indirect` that excludes 0 supports the claim that perceived "
             "authorship mediates the effect of actual authorship on score.")
lines.append("- Where `c` is near zero but `c'` is sharply negative and `indirect` is "
             "sharply positive, the design is *inconsistently* mediated — actual authorship "
             "would lower score except that judges falsely tag own-style outputs as theirs "
             "and then inflate those.")
lines.append("- Per-judge tables identify which judges drive the pooled pattern.")
lines.append("")
lines.append("_Generated by `analysis/formal_mediation.py`. Random seed 20260512._")

OUT_MD.write_text("\n".join(lines))
print(f"Wrote {OUT_CSV.name} and {OUT_MD.name}")
