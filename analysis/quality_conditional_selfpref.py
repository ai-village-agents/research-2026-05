"""Quality-conditional self-preference.

Question: does the self-preference effect (β on author_is_self) depend on
external quality of the response being judged? Hypothesis: self-pref is larger
on ambiguous-quality responses where judges have more "room" to inflate.

Quality proxy = `peer_quality`: mean composite from the 3 OTHER judges of the
SAME (author, prompt_id, condition) row. Computed leave-one-out so it never
includes the focal judge's own score.

Outputs:
  results/quality_conditional.csv     (binned and interaction regression results)
  results/quality_conditional_report.md
"""
from __future__ import annotations
import csv
from pathlib import Path
from collections import defaultdict
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "unified" / "unified_wide.csv"
OUT_CSV = ROOT / "results" / "quality_conditional.csv"
OUT_MD = ROOT / "results" / "quality_conditional_report.md"

rng = np.random.default_rng(20260512)

rows = []
with DATA.open() as f:
    for r in csv.DictReader(f):
        rows.append(r)
for r in rows:
    r["composite"] = float(r["composite"])
    r["author_is_self"] = int(r["author_is_self"])
    r["predicted_self"] = int(r["predicted_self"])

# --- Build peer_quality: for each (author, prompt_id, condition), the mean composite
#     from all judges. Then for each row, peer_quality = (sum_all_4 - this_score) / 3
#     i.e. leave-one-out mean over judges.
sum_by_apc = defaultdict(float)
n_by_apc = defaultdict(int)
for r in rows:
    key = (r["author"], r["prompt_id"], r["condition"])
    sum_by_apc[key] += r["composite"]
    n_by_apc[key] += 1

for r in rows:
    key = (r["author"], r["prompt_id"], r["condition"])
    n_other = n_by_apc[key] - 1
    r["peer_quality"] = (sum_by_apc[key] - r["composite"]) / n_other if n_other > 0 else float("nan")

# --- Regression helpers ---
def ols_with_se(y: np.ndarray, X: np.ndarray, clusters=None):
    """OLS coefficients and (optionally cluster) SE."""
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ coef
    n, k = X.shape
    if clusters is None:
        sigma2 = (resid @ resid) / max(n - k, 1)
        cov = sigma2 * np.linalg.pinv(X.T @ X)
    else:
        # Liang-Zeger cluster-robust
        XtX_inv = np.linalg.pinv(X.T @ X)
        cl = np.array(clusters)
        meat = np.zeros((k, k))
        for c in np.unique(cl):
            idx = np.where(cl == c)[0]
            Xc = X[idx]
            uc = resid[idx]
            sc = Xc.T @ uc
            meat += np.outer(sc, sc)
        G = len(np.unique(cl))
        adj = G / max(G - 1, 1)
        cov = adj * (XtX_inv @ meat @ XtX_inv)
    se = np.sqrt(np.diag(cov))
    return coef, se

def fit_interaction(rs, demean_q=True):
    """Y ~ b0 + b1 T + b2 Q + b3 T*Q (Q can be demeaned for interpretability)."""
    rs = [r for r in rs if not np.isnan(r["peer_quality"])]
    Y = np.array([r["composite"] for r in rs])
    T = np.array([r["author_is_self"] for r in rs], dtype=float)
    Q = np.array([r["peer_quality"] for r in rs])
    if demean_q:
        Q = Q - Q.mean()
    X = np.column_stack([np.ones(len(Y)), T, Q, T * Q])
    cl = [r["prompt_id"] for r in rs]
    coef, se = ols_with_se(Y, X, clusters=cl)
    return {
        "n": len(Y),
        "b0": coef[0], "b0_se": se[0],
        "T":  coef[1], "T_se":  se[1],
        "Q":  coef[2], "Q_se":  se[2],
        "TxQ": coef[3], "TxQ_se": se[3],
        "qmean": Q.mean() if not demean_q else 0.0,
    }

def fit_binned_T(rs, q_lo, q_hi):
    """β(author_is_self) within a quality stratum."""
    rs2 = [r for r in rs if (not np.isnan(r["peer_quality"]))
           and q_lo <= r["peer_quality"] <= q_hi]
    if len(rs2) < 5:
        return {"n": len(rs2), "T": np.nan, "T_se": np.nan}
    Y = np.array([r["composite"] for r in rs2])
    T = np.array([r["author_is_self"] for r in rs2], dtype=float)
    n_self = int(T.sum())
    n_other = int(len(T) - n_self)
    if len(np.unique(T)) < 2:
        # A within-bin self-vs-other contrast is not identified if the bin contains
        # only self rows or only non-self rows. Reporting 0.000 would be misleading.
        return {"n": len(rs2), "n_self": n_self, "n_other": n_other,
                "T": np.nan, "T_se": np.nan}
    X = np.column_stack([np.ones(len(Y)), T])
    cl = [r["prompt_id"] for r in rs2]
    coef, se = ols_with_se(Y, X, clusters=cl)
    return {"n": len(Y), "n_self": n_self, "n_other": n_other, "T": coef[1], "T_se": se[1]}

# --- Define quality terciles using the overall pooled distribution (peer_quality) ---
peer_q_all = np.array([r["peer_quality"] for r in rows if not np.isnan(r["peer_quality"])])
tertiles = np.percentile(peer_q_all, [33.33, 66.67])
q_min = peer_q_all.min(); q_max = peer_q_all.max()
print(f"Peer-quality terciles: t33={tertiles[0]:.3f}, t67={tertiles[1]:.3f}, "
      f"range=[{q_min:.2f}, {q_max:.2f}]")

def bins():
    return [
        ("low",  q_min,        tertiles[0]),
        ("mid",  tertiles[0]+1e-9, tertiles[1]),
        ("high", tertiles[1]+1e-9, q_max),
    ]

judges = sorted({r["judge"] for r in rows})
conds = ["c1", "c2", "c3"]

# Interaction regressions: pooled + per-judge × condition (C1, C2, C3)
results_int = []
scopes = [("pooled", None)] + [(j, j) for j in judges]
for scope_name, judge_filter in scopes:
    for cond in conds:
        rs = [r for r in rows
              if r["condition"] == cond
              and (judge_filter is None or r["judge"] == judge_filter)]
        if len(rs) < 30:
            continue
        fit = fit_interaction(rs, demean_q=True)
        fit.update({"scope": scope_name, "condition": cond, "kind": "interaction"})
        results_int.append(fit)

# Binned β(T) by tercile, C1 only (cleanest), per-judge + pooled
results_bin = []
for scope_name, judge_filter in scopes:
    for cond in conds:
        for bname, lo, hi in bins():
            rs = [r for r in rows
                  if r["condition"] == cond
                  and (judge_filter is None or r["judge"] == judge_filter)]
            res = fit_binned_T(rs, lo, hi)
            res.update({"scope": scope_name, "condition": cond, "bin": bname,
                        "kind": "binned"})
            results_bin.append(res)

# Write CSVs
def write_csv(path, rows_list, keys):
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, lineterminator="\n")
        w.writeheader()
        for r in rows_list:
            out = {}
            for k in keys:
                v = r.get(k, "")
                out[k] = f"{v:.4f}" if isinstance(v, float) else v
            w.writerow(out)

int_keys = ["scope", "condition", "kind", "n", "b0", "b0_se", "T", "T_se",
            "Q", "Q_se", "TxQ", "TxQ_se"]
bin_keys = ["scope", "condition", "bin", "kind", "n", "n_self", "n_other", "T", "T_se"]

# Concatenate for a single CSV with kind discriminator
all_keys = sorted(set(int_keys + bin_keys))
combined = []
for r in results_int + results_bin:
    out = {k: r.get(k, "") for k in all_keys}
    combined.append(out)
with OUT_CSV.open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=all_keys, lineterminator="\n")
    w.writeheader()
    for r in combined:
        out = {}
        for k in all_keys:
            v = r.get(k, "")
            out[k] = f"{v:.4f}" if isinstance(v, float) else v
        w.writerow(out)

# Markdown report
def fmt(v, se):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v:+.3f} ({se:.3f})"

lines = ["# Quality-conditional self-preference", "",
         "**Question.** Is self-preference larger when external quality is *ambiguous* "
         "(mid-tier responses) than when responses are clearly excellent or clearly weak?",
         "",
         f"**Quality proxy.** `peer_quality` = mean composite from the 3 *other* judges "
         f"of the same (author, prompt, condition). Computed leave-one-out so the focal "
         f"judge's own score never enters its own quality control.",
         "",
         f"**Tercile cutpoints (pooled distribution of peer_quality):** "
         f"t33 = {tertiles[0]:.3f}, t67 = {tertiles[1]:.3f}, range = "
         f"[{q_min:.2f}, {q_max:.2f}].",
         "",
         "**Caveats.** This is an exploratory observational diagnostic, not a preregistered causal test. `peer_quality` is derived from other AI judges' scores, not an external ground truth label; tercile bins can be compositionally imbalanced by author/judge, especially because Kimi-authored off-topic rows occupy much of the low-quality tail. Binned contrasts are reported only when a bin contains both self and non-self rows.",
         "",
         "## 1. Interaction regressions (T × Q)",
         "",
         "Model: `composite ~ b0 + T*author_is_self + Q*peer_quality_centered "
         "+ TxQ`. SEs clustered by prompt_id. A **negative TxQ** would mean "
         "self-preference shrinks as quality rises (ambiguous-quality hypothesis).",
         "",
         "| Scope | Cond | N | β(T) | β(Q) | β(T×Q) |",
         "|---|---|---:|---|---|---|"]
for r in results_int:
    lines.append(f"| {r['scope']} | {r['condition']} | {r['n']} | "
                 f"{fmt(r['T'], r['T_se'])} | {fmt(r['Q'], r['Q_se'])} | "
                 f"{fmt(r['TxQ'], r['TxQ_se'])} |")

lines.append("")
lines.append("## 2. β(T) within peer-quality terciles (binned)")
lines.append("")
lines.append("| Scope | Cond | Bin | N | Self rows | Other rows | β(T) ± SE |")
lines.append("|---|---|---|---:|---:|---:|---|")
for r in results_bin:
    lines.append(f"| {r['scope']} | {r['condition']} | {r['bin']} | {r['n']} | "
                 f"{r.get('n_self', '')} | {r.get('n_other', '')} | "
                 f"{fmt(r['T'], r['T_se'])} |")

lines.append("")
lines.append("## Reading guide")
lines.append("")
lines.append("- **TxQ < 0 (and clearly larger than its SE)** ⇒ self-preference larger for low-quality "
             "responses (a descriptive \"benefit-of-the-doubt\" pattern).")
lines.append("- **TxQ ≈ 0** ⇒ self-pref roughly constant across quality tiers (a baseline "
             "rate effect, no interaction).")
lines.append("- **TxQ > 0** ⇒ self-pref larger for high-quality responses (\"rich get "
             "richer\" pattern; would suggest judges *recognize own work better* when it's "
             "good, then amplify).")
lines.append("")
lines.append("Compare TxQ across the four judges — given the different mechanisms each "
             "exhibits in v1.0.0 (Claude raw +1.74, GPT perceived +1.35, Kimi off-topic, "
             "Gemini ~0), we expect heterogeneous TxQ.")
lines.append("")
lines.append("_Generated by `analysis/quality_conditional_selfpref.py`. "
             "Random seed 20260512._")

OUT_MD.write_text("\n".join(lines))
print(f"Wrote {OUT_CSV.name} and {OUT_MD.name}")


# === Appendix: Judge-fixed-effects pooled regression and Kimi-exclusion sensitivity ===

def fit_interaction_with_fe(rs, fe_var: str = "judge", demean_q=True):
    """Same as fit_interaction but with within-FE on `fe_var` (demean Y, T, Q within each FE level)."""
    rs = [r for r in rs if not np.isnan(r["peer_quality"])]
    Y = np.array([r["composite"] for r in rs])
    T = np.array([r["author_is_self"] for r in rs], dtype=float)
    Q = np.array([r["peer_quality"] for r in rs])
    fe_vals = np.array([r[fe_var] for r in rs])
    # within-transform
    Yw, Tw, Qw = Y.copy(), T.copy(), Q.copy()
    for u in np.unique(fe_vals):
        idx = np.where(fe_vals == u)[0]
        Yw[idx] -= Y[idx].mean()
        Tw[idx] -= T[idx].mean()
        Qw[idx] -= Q[idx].mean()
    TQ = Tw * Qw  # interaction in within space
    X = np.column_stack([Tw, Qw, TQ])
    coef, *_ = np.linalg.lstsq(X, Yw, rcond=None)
    resid = Yw - X @ coef
    cl = np.array([r["prompt_id"] for r in rs])
    XtXi = np.linalg.pinv(X.T @ X)
    meat = np.zeros((3, 3))
    for c in np.unique(cl):
        i = np.where(cl == c)[0]
        sc = X[i].T @ resid[i]
        meat += np.outer(sc, sc)
    G = len(np.unique(cl))
    cov = (G / max(G - 1, 1)) * (XtXi @ meat @ XtXi)
    se = np.sqrt(np.diag(cov))
    return {
        "n": len(Y), "T": coef[0], "T_se": se[0],
        "Q": coef[1], "Q_se": se[1],
        "TxQ": coef[2], "TxQ_se": se[2],
    }

appendix_rows = []
sensitivity_scopes = [
    ("pooled+judgeFE", lambda r: True),
    ("no-Kimi-judge",  lambda r: r["judge"]  != "kimi-k2.6"),
    ("no-Kimi-author", lambda r: r["author"] != "kimi-k2.6"),
    ("no-Kimi-both",   lambda r: r["judge"]  != "kimi-k2.6" and r["author"] != "kimi-k2.6"),
]
for scope_name, pred in sensitivity_scopes:
    for cond in ["c1", "c2", "c3"]:
        rs = [r for r in rows if r["condition"] == cond and pred(r)]
        fit = fit_interaction_with_fe(rs, fe_var="judge", demean_q=False)
        fit.update({"scope": scope_name, "condition": cond})
        appendix_rows.append(fit)

# Append appendix to markdown
with OUT_MD.open("a") as f:
    f.write("\n\n## Appendix: Judge fixed-effects and Kimi-exclusion sensitivity\n\n")
    f.write("Within-judge specification (judge FE absorbed) and Kimi exclusions. SEs clustered by prompt_id.\n\n")
    f.write("| Scope | Cond | N | β(T) | β(Q) | β(T×Q) |\n")
    f.write("|---|---|---:|---|---|---|\n")
    for r in appendix_rows:
        f.write(f"| {r['scope']} | {r['condition']} | {r['n']} | "
                f"{r['T']:+.3f} ({r['T_se']:.3f}) | "
                f"{r['Q']:+.3f} ({r['Q_se']:.3f}) | "
                f"{r['TxQ']:+.3f} ({r['TxQ_se']:.3f}) |\n")
    f.write("\n**Key reading:**\n")
    f.write("- `pooled+judgeFE`: T×Q remains strongly positive (≈ +0.84 to +1.00 across conditions). Across all four judges combined and net of judge-level intercepts, the data are consistent with a rich-get-richer pattern — but this pooled summary mixes heterogeneous mechanisms and should be treated as descriptive.\n")
    f.write("- `no-Kimi-judge`: positive T×Q softens substantially, indicating that Kimi-as-judge contributes heavily to the pooled slope.\n")
    f.write("- `no-Kimi-author` and `no-Kimi-both`: T×Q flips negative in C1 and C3, with C2 near zero/noisy. Removing Kimi-authored low-quality tail rows changes the substantive reading toward a benefit-of-the-doubt pattern among the remaining author set.\n")
    f.write("- Compare with per-judge tables above: Claude shows a negative T×Q in C1/C3, GPT-5.5 most clearly in C3, Gemini is nearly flat, and Kimi is dominated by the off-topic confound.\n")

# Also write the appendix as a separate CSV
with (ROOT / "results" / "quality_conditional_appendix.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["scope","condition","n","T","T_se","Q","Q_se","TxQ","TxQ_se"], lineterminator="\n")
    w.writeheader()
    for r in appendix_rows:
        w.writerow({k: (f"{r[k]:.4f}" if isinstance(r[k], float) else r[k]) for k in w.fieldnames})

print("Appendix written.")
