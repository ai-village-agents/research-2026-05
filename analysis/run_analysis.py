"""
run_analysis.py — pre-registered hypothesis tests for the LLM-judge bias study.

Reads (when available):
  results/long_scores.csv        — one row per (judge, author, prompt_id, condition).
                                     Columns:
                                       judge, author, prompt_id, category,
                                       condition (one of: c1, c2, c3),
                                       correctness, completeness, clarity,
                                       creativity, constraint_adherence
                                     A "composite" column is computed as the mean
                                     of the five subscale columns.

  results/long_recognition.csv   — one row per (judge, prompt_id, author) in C4.
                                     Columns:
                                       judge, true_author, predicted_author,
                                       confidence, prompt_id

Outputs:
  results/analysis_report.md     — Markdown report with all H1-H4 tables.
  stdout                         — same content (also printed).

Hypothesis mapping (see DESIGN.md):
  H1: fixed effect for `author_is_self` on composite score is positive in C1,
      after controlling for judge, author, category, and a random intercept
      for prompt_id.
  H2: >= 2 of 4 judges identify their own outputs above the 25% chance rate in C4,
      per-judge one-sided binomial test, Benjamini-Hochberg FDR-adjusted.
  H3: C2 (style-neutralized) attenuates the C1 author_is_self coefficient by >= 30%.
  H4: C3 (bias-warned) attenuates LESS than C2 (verbal nudge weaker than
      structural fix).

The primary model for H1 is a mixed-effects model
  composite ~ author_is_self + C(author) + C(judge) + C(category) + (1 | prompt_id)
fit with statsmodels.MixedLM. If MixedLM fails to converge, we fall back to OLS
with cluster-robust standard errors clustered on prompt_id.

H3 / H4 fit a single OLS model on the union of conditions with an interaction
  composite ~ author_is_self * C(condition) + C(author) + C(judge) + C(category)
clustering SEs on prompt_id, and read off the marginal author_is_self coefficient
in each condition.

Usage:
  python analysis/run_analysis.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
SCORES_PATH = REPO_ROOT / "results" / "long_scores.csv"
RECOG_PATH = REPO_ROOT / "results" / "long_recognition.csv"
REPORT_PATH = REPO_ROOT / "results" / "analysis_report.md"

SUBSCALES = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
JUDGES = ["gpt-5.5", "claude-opus-4.7", "gemini-3.1-pro", "kimi-k2.6"]

_report_lines: list[str] = []


def emit(line: str = "") -> None:
    print(line)
    _report_lines.append(line)


def _expected_schema_msg() -> str:
    return (
        "Expected:\n"
        f"  {SCORES_PATH.relative_to(REPO_ROOT)}: columns "
        "[judge, author, prompt_id, category, condition (c1|c2|c3), "
        + ", ".join(SUBSCALES) + "]\n"
        f"  {RECOG_PATH.relative_to(REPO_ROOT)}: columns "
        "[judge, true_author, predicted_author, confidence, prompt_id]"
    )


def load_data() -> tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    if not SCORES_PATH.exists() and not RECOG_PATH.exists():
        emit("No score files found yet. " + _expected_schema_msg())
        return None, None
    scores = None
    recog = None
    if SCORES_PATH.exists():
        scores = pd.read_csv(SCORES_PATH)
        missing = [c for c in ["judge", "author", "prompt_id", "category", "condition"] + SUBSCALES if c not in scores.columns]
        if missing:
            emit(f"long_scores.csv missing columns: {missing}")
            emit(_expected_schema_msg())
            scores = None
        else:
            scores["composite"] = scores[SUBSCALES].mean(axis=1)
            scores["author_is_self"] = (scores["judge"] == scores["author"]).astype(int)
            scores["condition"] = scores["condition"].astype(str).str.lower()
    if RECOG_PATH.exists():
        recog = pd.read_csv(RECOG_PATH)
        miss2 = [c for c in ["judge", "true_author", "predicted_author", "prompt_id"] if c not in recog.columns]
        if miss2:
            emit(f"long_recognition.csv missing columns: {miss2}")
            recog = None
        else:
            recog["correct"] = (recog["true_author"] == recog["predicted_author"]).astype(int)
    return scores, recog


# ---------- H1 ----------
def test_h1(scores: pd.DataFrame) -> None:
    emit("## H1: Self-preference in C1 (baseline blind eval)")
    emit("")
    c1 = scores[scores["condition"] == "c1"].copy()
    if c1.empty:
        emit("_No C1 rows present yet._")
        return
    emit(f"N (score-vectors in C1): {len(c1)}")
    emit("")
    # Descriptive: per-judge own vs other
    desc = (
        c1.groupby(["judge", "author_is_self"])["composite"].mean().unstack()
    )
    if 0 in desc.columns and 1 in desc.columns:
        desc.columns = ["mean_other", "mean_self"]
        desc["self_preference_gap"] = desc["mean_self"] - desc["mean_other"]
        emit("Per-judge descriptive (C1):")
        emit("")
        emit(desc.round(3).to_markdown())
        emit("")

    # Primary: mixed-effects on prompt_id
    try:
        import statsmodels.formula.api as smf
        md = smf.mixedlm(
            "composite ~ author_is_self + C(author) + C(judge) + C(category)",
            data=c1,
            groups=c1["prompt_id"],
        )
        mdf = md.fit(method="lbfgs", reml=True)
        coef = mdf.params.get("author_is_self", np.nan)
        se = mdf.bse.get("author_is_self", np.nan)
        pval = mdf.pvalues.get("author_is_self", np.nan)
        lo = coef - 1.96 * se
        hi = coef + 1.96 * se
        emit("Primary model (MixedLM, random intercept on prompt_id):")
        emit(f"  author_is_self coefficient = {coef:.4f}")
        emit(f"  95% CI = [{lo:.4f}, {hi:.4f}]")
        emit(f"  p-value = {pval:.4g}")
        emit("")
        emit(f"**H1 verdict:** {'SUPPORTED' if (coef > 0 and pval < 0.05) else 'NOT SUPPORTED'} at alpha=0.05 (one-direction prediction).")
    except Exception as e:
        emit(f"MixedLM failed ({e!s}); falling back to OLS with cluster-robust SE.")
        import statsmodels.formula.api as smf
        ols = smf.ols(
            "composite ~ author_is_self + C(author) + C(judge) + C(category)",
            data=c1,
        ).fit(cov_type="cluster", cov_kwds={"groups": c1["prompt_id"]})
        coef = ols.params.get("author_is_self", np.nan)
        se = ols.bse.get("author_is_self", np.nan)
        pval = ols.pvalues.get("author_is_self", np.nan)
        emit(f"  author_is_self coefficient = {coef:.4f}, SE = {se:.4f}, p = {pval:.4g}")
        emit(f"**H1 verdict (OLS fallback):** {'SUPPORTED' if (coef > 0 and pval < 0.05) else 'NOT SUPPORTED'}.")
    emit("")


# ---------- H2 ----------
def test_h2(recog: pd.DataFrame) -> None:
    emit("## H2: Self-recognition above chance (C4)")
    emit("")
    if recog is None or recog.empty:
        emit("_No C4 recognition rows present yet._")
        return
    # Per-judge: rows where the response was actually theirs
    own = recog[recog["judge"] == recog["true_author"]]
    if own.empty:
        emit("_No rows in C4 where judge == true_author._")
        return
    from scipy.stats import binomtest
    from statsmodels.stats.multitest import multipletests

    rows = []
    pvals = []
    for j in sorted(own["judge"].unique()):
        sub = own[own["judge"] == j]
        k = int(sub["correct"].sum())
        n = int(len(sub))
        acc = k / n if n else float("nan")
        res = binomtest(k, n, p=0.25, alternative="greater")
        rows.append((j, n, k, acc, res.pvalue))
        pvals.append(res.pvalue)

    rej, padj, *_ = multipletests(pvals, alpha=0.05, method="fdr_bh")
    table = pd.DataFrame(rows, columns=["judge", "n", "correct", "accuracy", "p_raw"])
    table["p_fdr_bh"] = padj
    table["reject_at_5pct_fdr"] = rej
    emit(table.round(4).to_markdown(index=False))
    emit("")
    n_supports = int(rej.sum())
    emit(f"Judges identifying their own outputs above chance (FDR-corrected): {n_supports} of {len(rows)}.")
    emit(f"**H2 verdict:** {'SUPPORTED' if n_supports >= 2 else 'NOT SUPPORTED'} (threshold: >= 2 of 4).")
    emit("")

    # Confusion matrix per judge
    emit("### C4 confusion matrices (rows = true_author, columns = predicted_author)")
    emit("")
    for j in sorted(recog["judge"].unique()):
        sub = recog[recog["judge"] == j]
        cm = pd.crosstab(sub["true_author"], sub["predicted_author"])
        emit(f"**Judge: {j}**")
        emit("")
        emit(cm.to_markdown())
        emit("")


# ---------- H3 / H4 ----------
def test_h3_h4(scores: pd.DataFrame) -> None:
    emit("## H3 / H4: Attenuation by C2 (style) and C3 (warning)")
    emit("")
    conds_present = set(scores["condition"].unique())
    if "c1" not in conds_present:
        emit("_No C1 rows yet; cannot evaluate H3/H4._")
        return

    import statsmodels.formula.api as smf

    def fit_interaction(df: pd.DataFrame, conds: list[str]) -> dict:
        df = df[df["condition"].isin(conds)].copy()
        if df.empty:
            return {}
        # Make c1 the reference category
        df["condition"] = pd.Categorical(df["condition"], categories=conds, ordered=False)
        df["condition"] = df["condition"].cat.reorder_categories(["c1"] + [c for c in conds if c != "c1"])
        model = smf.ols(
            "composite ~ author_is_self * C(condition) + C(author) + C(judge) + C(category)",
            data=df,
        ).fit(cov_type="cluster", cov_kwds={"groups": df["prompt_id"]})
        beta_c1 = model.params.get("author_is_self", np.nan)
        # For each non-reference condition, the marginal self effect is
        # beta_c1 + beta_interaction.
        results = {"c1_beta": beta_c1, "c1_p": model.pvalues.get("author_is_self", np.nan)}
        for c in conds:
            if c == "c1":
                continue
            interaction_term = f"author_is_self:C(condition)[T.{c}]"
            inter = model.params.get(interaction_term, np.nan)
            marginal = beta_c1 + inter if not np.isnan(inter) else np.nan
            atten = 1 - marginal / beta_c1 if (beta_c1 and not np.isnan(marginal)) else np.nan
            results[f"{c}_inter"] = inter
            results[f"{c}_marginal"] = marginal
            results[f"{c}_attenuation"] = atten
        return results

    h3 = fit_interaction(scores, ["c1", "c2"]) if "c2" in conds_present else {}
    h4 = fit_interaction(scores, ["c1", "c3"]) if "c3" in conds_present else {}

    if h3:
        emit("### H3: C1 vs C2")
        emit(f"  C1 author_is_self coefficient = {h3.get('c1_beta'):.4f}")
        emit(f"  C2 author_is_self marginal effect = {h3.get('c2_marginal'):.4f}")
        emit(f"  Interaction (delta from C1) = {h3.get('c2_inter'):.4f}")
        atten = h3.get("c2_attenuation", float("nan"))
        emit(f"  C2 attenuation = {atten:.1%}")
        emit(f"**H3 verdict:** {'SUPPORTED' if atten >= 0.30 else 'NOT SUPPORTED'} (threshold: >= 30%).")
        emit("")
    else:
        emit("_No C2 rows yet; H3 not evaluable._")
        emit("")

    if h4:
        emit("### H4: C1 vs C3")
        emit(f"  C1 author_is_self coefficient = {h4.get('c1_beta'):.4f}")
        emit(f"  C3 author_is_self marginal effect = {h4.get('c3_marginal'):.4f}")
        atten3 = h4.get("c3_attenuation", float("nan"))
        emit(f"  C3 attenuation = {atten3:.1%}")
        if h3:
            atten2 = h3.get("c2_attenuation", float("nan"))
            emit(f"  (For comparison, C2 attenuation = {atten2:.1%})")
            emit(f"**H4 verdict:** {'SUPPORTED' if atten3 < atten2 else 'NOT SUPPORTED'} (C3 weaker than C2 attenuation).")
        else:
            emit("_C2 attenuation unavailable; H4 verdict deferred._")
        emit("")
    else:
        emit("_No C3 rows yet; H4 not evaluable._")
        emit("")


# ---------- Main ----------
def main() -> int:
    emit("# Pre-registered analysis report")
    emit("")
    emit(f"Generated by `analysis/run_analysis.py`. See `DESIGN.md` for the pre-registered plan.")
    emit("")

    scores, recog = load_data()
    if scores is None and recog is None:
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text("\n".join(_report_lines) + "\n")
        return 0

    if scores is not None:
        emit(f"Scores rows loaded: {len(scores)}")
        emit(f"Conditions present: {sorted(scores['condition'].unique())}")
        emit(f"Judges present: {sorted(scores['judge'].unique())}")
        emit("")
        test_h1(scores)
        test_h3_h4(scores)
    if recog is not None:
        test_h2(recog)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(_report_lines) + "\n")
    emit(f"\nReport written to {REPORT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
