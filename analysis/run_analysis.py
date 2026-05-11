"""
run_analysis.py — pre-registered hypothesis tests for the LLM-judge bias study.

Primary inputs can be either:
  data/judgments/<judge>/long_scores.csv
  data/judgments/<judge>/long_recognition.csv

or legacy/locally merged files:
  results/long_scores.csv
  results/long_recognition.csv

Score rows are one per (judge, author, prompt_id, condition) with columns:
  judge, author, prompt_id, category, condition (c1|c2|c3),
  correctness, completeness, clarity, creativity, constraint_adherence
A composite column is computed as the mean of the five subscale columns.

Recognition rows are one per (judge, prompt_id, true_author) in C4 with columns:
  judge, true_author, predicted_author, prompt_id, and optionally confidence.

Outputs:
  results/analysis_report.md by default, plus stdout.

Hypothesis mapping (see DESIGN.md):
  H1: fixed effect for author_is_self on composite score is positive in C1,
      after controlling for judge, author, category, and a random intercept
      for prompt_id.
  H2: >= 2 of 4 judges identify their own outputs above the 25% chance rate in C4,
      per-judge one-sided binomial test, Benjamini-Hochberg FDR-adjusted.
  H3: C2 (style-neutralized) attenuates the C1 author_is_self coefficient by >= 30%.
  H4: C3 (bias-warned) attenuates LESS than C2.

Usage:
  python analysis/run_analysis.py
  python analysis/run_analysis.py --from-judgments-dir
  python analysis/run_analysis.py --judgments-dir data/judgments --report /tmp/report.md
  python analysis/run_analysis.py --scores results/long_scores.csv --recognition results/long_recognition.csv
  python analysis/run_analysis.py --mixedlm-timeout-seconds 0  # disable MixedLM timeout
"""

from __future__ import annotations

import argparse
import contextlib
import math
import signal
import sys
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SCORES_PATH = REPO_ROOT / "results" / "long_scores.csv"
DEFAULT_RECOG_PATH = REPO_ROOT / "results" / "long_recognition.csv"
DEFAULT_REPORT_PATH = REPO_ROOT / "results" / "analysis_report.md"
DEFAULT_JUDGMENTS_DIR = REPO_ROOT / "data" / "judgments"

SUBSCALES = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
JUDGES = ["gpt-5.5", "claude-opus-4.7", "gemini-3.1-pro", "kimi-k2.6"]
SCORE_REQUIRED = ["judge", "author", "prompt_id", "category", "condition"] + SUBSCALES
RECOG_REQUIRED = ["judge", "true_author", "predicted_author", "prompt_id"]

_report_lines: list[str] = []


def emit(line: str = "") -> None:
    print(line)
    _report_lines.append(line)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except Exception:
        return str(path)


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run pre-registered evaluator-bias analyses.")
    p.add_argument("--scores", type=Path, default=DEFAULT_SCORES_PATH, help="Merged long_scores.csv path.")
    p.add_argument("--recognition", type=Path, default=DEFAULT_RECOG_PATH, help="Merged long_recognition.csv path.")
    p.add_argument("--judgments-dir", type=Path, default=DEFAULT_JUDGMENTS_DIR, help="Directory containing per-judge judgment subdirectories.")
    p.add_argument("--from-judgments-dir", action="store_true", help="Force concatenating data from --judgments-dir/* instead of using merged results files.")
    p.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH, help="Markdown report output path.")
    p.add_argument("--mixedlm-timeout-seconds", type=int, default=45, help="Seconds to allow MixedLM fit before falling back to OLS; use 0 to disable timeout.")
    return p.parse_args(argv)


def resolve_path(path: Path) -> Path:
    return path if path.is_absolute() else REPO_ROOT / path


def _expected_schema_msg(scores_path: Path, recog_path: Path, judgments_dir: Path) -> str:
    return (
        "Expected either:\n"
        f"  {rel(scores_path)}: columns [" + ", ".join(SCORE_REQUIRED) + "]\n"
        f"  {rel(recog_path)}: columns [" + ", ".join(RECOG_REQUIRED) + "]\n"
        "or per-judge files under:\n"
        f"  {rel(judgments_dir)}/*/long_scores.csv\n"
        f"  {rel(judgments_dir)}/*/long_recognition.csv"
    )


def read_csv_if_exists(path: Path) -> Optional[pd.DataFrame]:
    if path.exists():
        return pd.read_csv(path)
    return None


def concat_judgment_files(judgments_dir: Path, filename: str) -> tuple[Optional[pd.DataFrame], list[Path]]:
    paths = sorted(judgments_dir.glob(f"*/{filename}")) if judgments_dir.exists() else []
    frames = []
    for path in paths:
        df = pd.read_csv(path)
        df["_source_file"] = rel(path)
        frames.append(df)
    if not frames:
        return None, paths
    return pd.concat(frames, ignore_index=True), paths




def table_md(obj, **kwargs) -> str:
    """Render a DataFrame/Series as Markdown, with a plain-text fallback if tabulate is absent."""
    try:
        return obj.to_markdown(**kwargs)
    except Exception as e:
        if obj.__class__.__name__ == "Series":
            obj = obj.to_frame()
        try:
            return "```\n" + obj.to_string(**{k: v for k, v in kwargs.items() if k in {"index"}}) + f"\n```\n(_Markdown table fallback used: {e!s}_)"
        except Exception:
            return "```\n" + str(obj) + f"\n```\n(_Markdown table fallback used: {e!s}_)"

def strip_string_columns(df: pd.DataFrame, columns: Sequence[str]) -> None:
    for c in columns:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()


def validate_scores(scores: pd.DataFrame, expected_msg: str) -> Optional[pd.DataFrame]:
    missing = [c for c in SCORE_REQUIRED if c not in scores.columns]
    if missing:
        emit(f"long_scores missing columns: {missing}")
        emit(expected_msg)
        return None
    strip_string_columns(scores, ["judge", "author", "prompt_id", "category", "condition"])
    scores["condition"] = scores["condition"].str.lower()
    for c in SUBSCALES:
        scores[c] = pd.to_numeric(scores[c], errors="coerce")
    if scores[SUBSCALES].isna().any().any():
        bad = scores[scores[SUBSCALES].isna().any(axis=1)]
        emit(f"WARNING: {len(bad)} score rows contain non-numeric/missing subscale values.")
    scores["composite"] = scores[SUBSCALES].mean(axis=1)
    scores["author_is_self"] = (scores["judge"] == scores["author"]).astype(int)
    dup = scores.duplicated(["judge", "author", "prompt_id", "condition"], keep=False)
    if dup.any():
        emit(f"WARNING: {int(dup.sum())} duplicate score rows on (judge, author, prompt_id, condition); keeping all rows.")
        emit(scores.loc[dup, ["judge", "author", "prompt_id", "condition"]].value_counts().head(20).pipe(table_md))
        emit("")
    return scores


def validate_recog(recog: pd.DataFrame, expected_msg: str) -> Optional[pd.DataFrame]:
    missing = [c for c in RECOG_REQUIRED if c not in recog.columns]
    if missing:
        emit(f"long_recognition missing columns: {missing}")
        emit(expected_msg)
        return None
    strip_string_columns(recog, ["judge", "true_author", "predicted_author", "prompt_id"])
    if "confidence" in recog.columns:
        recog["confidence"] = pd.to_numeric(recog["confidence"], errors="coerce")
    recog["correct"] = (recog["true_author"] == recog["predicted_author"]).astype(int)
    dup = recog.duplicated(["judge", "true_author", "prompt_id"], keep=False)
    if dup.any():
        emit(f"WARNING: {int(dup.sum())} duplicate recognition rows on (judge, true_author, prompt_id); keeping all rows.")
        emit(recog.loc[dup, ["judge", "true_author", "prompt_id"]].value_counts().head(20).pipe(table_md))
        emit("")
    return recog


def emit_coverage(scores: Optional[pd.DataFrame], recog: Optional[pd.DataFrame]) -> None:
    emit("## Loaded data coverage")
    emit("")
    if scores is not None:
        emit(f"Scores rows loaded: {len(scores)} (full expected: 1440; per judge expected: 360)")
        if len(scores) != 1440:
            emit(f"WARNING: score coverage is incomplete or nonstandard ({len(scores)}/1440 rows).")
        score_counts = scores.groupby("judge").size().rename("score_rows").reindex(sorted(scores["judge"].unique()))
        emit(score_counts.to_frame().pipe(table_md))
        per_cond = scores.groupby(["judge", "condition"]).size().unstack(fill_value=0)
        emit("")
        emit("Score rows by judge and condition:")
        emit(per_cond.pipe(table_md))
        emit("")
    else:
        emit("Scores rows loaded: none")
        emit("")
    if recog is not None:
        emit(f"Recognition rows loaded: {len(recog)} (full expected: 480; per judge expected: 120)")
        if len(recog) != 480:
            emit(f"WARNING: recognition coverage is incomplete or nonstandard ({len(recog)}/480 rows).")
        recog_counts = recog.groupby("judge").size().rename("recognition_rows").reindex(sorted(recog["judge"].unique()))
        emit(recog_counts.to_frame().pipe(table_md))
        emit("")
    else:
        emit("Recognition rows loaded: none")
        emit("")


def load_data(args: argparse.Namespace) -> tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    scores_path = resolve_path(args.scores)
    recog_path = resolve_path(args.recognition)
    judgments_dir = resolve_path(args.judgments_dir)
    expected_msg = _expected_schema_msg(scores_path, recog_path, judgments_dir)

    emit("## Data loading")
    emit("")

    use_judgments = bool(args.from_judgments_dir)
    if not use_judgments and not scores_path.exists() and not recog_path.exists():
        use_judgments = True

    if use_judgments:
        scores, score_sources = concat_judgment_files(judgments_dir, "long_scores.csv")
        recog, recog_sources = concat_judgment_files(judgments_dir, "long_recognition.csv")
        emit(f"Loading mode: per-judge judgments directory ({rel(judgments_dir)})")
        emit(f"Score files found: {len(score_sources)}")
        for p in score_sources:
            emit(f"  - {rel(p)}")
        emit(f"Recognition files found: {len(recog_sources)}")
        for p in recog_sources:
            emit(f"  - {rel(p)}")
    else:
        scores = read_csv_if_exists(scores_path)
        recog = read_csv_if_exists(recog_path)
        emit("Loading mode: merged results files")
        emit(f"Scores file: {rel(scores_path)} ({'found' if scores is not None else 'missing'})")
        emit(f"Recognition file: {rel(recog_path)} ({'found' if recog is not None else 'missing'})")
    emit("")

    if scores is None and recog is None:
        emit("No score files found yet.")
        emit(expected_msg)
        return None, None

    scores = validate_scores(scores, expected_msg) if scores is not None else None
    recog = validate_recog(recog, expected_msg) if recog is not None else None
    emit_coverage(scores, recog)
    return scores, recog


def statsmodels_formula_api():
    try:
        import statsmodels.formula.api as smf
        return smf
    except Exception as e:
        emit(f"Model-fitting skipped: statsmodels is unavailable ({e!s}).")
        emit("")
        return None


class TimeoutExpired(RuntimeError):
    pass


@contextlib.contextmanager
def time_limit(seconds: int, label: str):
    """Raise TimeoutExpired after seconds on Unix; seconds <= 0 disables the timeout."""
    if seconds <= 0 or not hasattr(signal, "SIGALRM"):
        yield
        return

    def _handler(signum, frame):  # pragma: no cover - timing dependent
        raise TimeoutExpired(f"{label} exceeded {seconds} seconds")

    previous = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


# ---------- H1 ----------
def test_h1(scores: pd.DataFrame, mixedlm_timeout_seconds: int = 45) -> None:
    emit("## H1: Self-preference in C1 (baseline blind eval)")
    emit("")
    c1 = scores[scores["condition"] == "c1"].copy()
    if c1.empty:
        emit("_No C1 rows present yet._")
        return
    emit(f"N (score-vectors in C1): {len(c1)}")
    emit("")
    desc = c1.groupby(["judge", "author_is_self"])["composite"].mean().unstack()
    if 0 in desc.columns and 1 in desc.columns:
        desc.columns = ["mean_other", "mean_self"]
        desc["self_preference_gap"] = desc["mean_self"] - desc["mean_other"]
        emit("Per-judge descriptive (C1):")
        emit("")
        emit(desc.round(3).pipe(table_md))
        emit("")

    smf = statsmodels_formula_api()
    if smf is None:
        builtin_h1_ols(c1)
        emit("")
        return
    try:
        md = smf.mixedlm(
            "composite ~ author_is_self + C(author) + C(judge) + C(category)",
            data=c1,
            groups=c1["prompt_id"],
        )
        with time_limit(mixedlm_timeout_seconds, "MixedLM fit"):
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
        try:
            ols = smf.ols(
                "composite ~ author_is_self + C(author) + C(judge) + C(category)",
                data=c1,
            ).fit(cov_type="cluster", cov_kwds={"groups": c1["prompt_id"]})
            coef = ols.params.get("author_is_self", np.nan)
            se = ols.bse.get("author_is_self", np.nan)
            pval = ols.pvalues.get("author_is_self", np.nan)
            emit(f"  author_is_self coefficient = {coef:.4f}, SE = {se:.4f}, p = {pval:.4g}")
            emit(f"**H1 verdict (OLS fallback):** {'SUPPORTED' if (coef > 0 and pval < 0.05) else 'NOT SUPPORTED'}.")
        except Exception as e2:
            emit(f"statsmodels OLS fallback also failed ({e2!s}); trying built-in OLS fallback.")
            builtin_h1_ols(c1)
    emit("")



def normal_two_sided_p(z: float) -> float:
    if not np.isfinite(z):
        return float("nan")
    # Two-sided normal tail via the complementary error function.
    return float(math.erfc(abs(z) / math.sqrt(2)))


def builtin_ols_cluster(
    df: pd.DataFrame,
    y_col: str,
    numeric_cols: Sequence[str],
    categorical_cols: Sequence[str],
    cluster_col: str,
    interaction_pairs: Sequence[tuple[str, str]] = (),
) -> dict:
    """Small OLS + cluster-robust covariance fallback using numpy/pandas only."""
    work = df[[y_col, cluster_col] + list(numeric_cols) + list(categorical_cols)].copy()
    work = work.dropna(subset=[y_col, cluster_col] + list(numeric_cols) + list(categorical_cols))
    y = pd.to_numeric(work[y_col], errors="coerce").astype(float)
    cols = {"Intercept": pd.Series(1.0, index=work.index)}
    for c in numeric_cols:
        cols[c] = pd.to_numeric(work[c], errors="coerce").astype(float)
    for c in categorical_cols:
        dummies = pd.get_dummies(work[c].astype(str), prefix=f"C({c})", drop_first=True, dtype=float)
        for name in dummies.columns:
            cols[name] = dummies[name]
    # Add requested interactions after base terms so names are predictable.
    for left, right in interaction_pairs:
        left_values = pd.to_numeric(work[left], errors="coerce").astype(float)
        if right in categorical_cols:
            levels = sorted(work[right].astype(str).unique())
            if levels:
                ref = levels[0]
                for level in levels:
                    if level == ref:
                        continue
                    name = f"{left}:C({right})[T.{level}]"
                    cols[name] = left_values * (work[right].astype(str) == level).astype(float)
        else:
            name = f"{left}:{right}"
            cols[name] = left_values * pd.to_numeric(work[right], errors="coerce").astype(float)
    Xdf = pd.DataFrame(cols, index=work.index).astype(float)
    mask = ~(Xdf.isna().any(axis=1) | y.isna())
    Xdf = Xdf.loc[mask]
    y = y.loc[mask]
    clusters = work.loc[mask, cluster_col].astype(str)
    X = Xdf.to_numpy(float)
    yv = y.to_numpy(float)
    pinv_xtx = np.linalg.pinv(X.T @ X)
    beta = pinv_xtx @ X.T @ yv
    resid = yv - X @ beta
    meat = np.zeros((X.shape[1], X.shape[1]))
    for cluster in clusters.unique():
        idx = (clusters == cluster).to_numpy()
        Xg = X[idx, :]
        ug = resid[idx]
        xu = Xg.T @ ug
        meat += np.outer(xu, xu)
    n, k = X.shape
    g = clusters.nunique()
    cov = pinv_xtx @ meat @ pinv_xtx
    if g > 1 and n > k:
        cov *= (g / (g - 1)) * ((n - 1) / (n - k))
    se = np.sqrt(np.maximum(np.diag(cov), 0))
    params = pd.Series(beta, index=Xdf.columns)
    bse = pd.Series(se, index=Xdf.columns)
    pvals = pd.Series([normal_two_sided_p(b / s) if s > 0 else float("nan") for b, s in zip(beta, se)], index=Xdf.columns)
    return {"params": params, "bse": bse, "pvalues": pvals, "n": n, "clusters": g}


def builtin_h1_ols(c1: pd.DataFrame) -> None:
    emit("Using built-in OLS fallback with cluster-robust SE by prompt_id.")
    fit = builtin_ols_cluster(
        c1,
        y_col="composite",
        numeric_cols=["author_is_self"],
        categorical_cols=["author", "judge", "category"],
        cluster_col="prompt_id",
    )
    coef = fit["params"].get("author_is_self", np.nan)
    se = fit["bse"].get("author_is_self", np.nan)
    pval = fit["pvalues"].get("author_is_self", np.nan)
    emit(f"  author_is_self coefficient = {coef:.4f}, SE = {se:.4f}, p ≈ {pval:.4g}")
    emit(f"  N = {fit['n']}, clusters = {fit['clusters']}")
    emit(f"**H1 verdict (built-in OLS fallback):** {'SUPPORTED' if (coef > 0 and pval < 0.05) else 'NOT SUPPORTED'}.")


def builtin_interaction_fit(scores: pd.DataFrame, conds: list[str]) -> dict:
    df = scores[scores["condition"].isin(conds)].copy()
    if df.empty:
        return {}
    # Force c1 to be the reference by using ordered labels c1 first.
    df["condition"] = pd.Categorical(df["condition"], categories=["c1"] + [c for c in conds if c != "c1"], ordered=False).astype(str)
    fit = builtin_ols_cluster(
        df,
        y_col="composite",
        numeric_cols=["author_is_self"],
        categorical_cols=["condition", "author", "judge", "category"],
        cluster_col="prompt_id",
        interaction_pairs=[("author_is_self", "condition")],
    )
    beta_c1 = fit["params"].get("author_is_self", np.nan)
    results = {"c1_beta": beta_c1, "c1_p": fit["pvalues"].get("author_is_self", np.nan)}
    for c in conds:
        if c == "c1":
            continue
        interaction_term = f"author_is_self:C(condition)[T.{c}]"
        inter = fit["params"].get(interaction_term, np.nan)
        marginal = beta_c1 + inter if not np.isnan(inter) else np.nan
        atten = 1 - marginal / beta_c1 if (beta_c1 and not np.isnan(marginal)) else np.nan
        results[f"{c}_inter"] = inter
        results[f"{c}_marginal"] = marginal
        results[f"{c}_attenuation"] = atten
    results["n"] = fit["n"]
    results["clusters"] = fit["clusters"]
    return results

def binom_sf(k: int, n: int, p: float = 0.25) -> float:
    return float(sum(math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i)) for i in range(k, n + 1)))


def bh_fdr(pvals: Sequence[float], alpha: float = 0.05) -> tuple[list[bool], list[float]]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adjusted = [1.0] * m
    prev = 1.0
    for rank, i in reversed(list(enumerate(order, start=1))):
        val = min(prev, pvals[i] * m / rank)
        adjusted[i] = val
        prev = val
    reject = [adjusted[i] <= alpha for i in range(m)]
    return reject, adjusted


# ---------- H2 ----------
def test_h2(recog: pd.DataFrame) -> None:
    emit("## H2: Self-recognition above chance (C4)")
    emit("")
    if recog is None or recog.empty:
        emit("_No C4 recognition rows present yet._")
        return
    own = recog[recog["judge"] == recog["true_author"]]
    if own.empty:
        emit("_No rows in C4 where judge == true_author._")
        return
    try:
        from scipy.stats import binomtest
        from statsmodels.stats.multitest import multipletests
        scipy_available = True
    except Exception as e:
        emit(f"Using built-in binomial/BH calculations because scipy/statsmodels test helpers are unavailable ({e!s}).")
        scipy_available = False

    rows = []
    pvals = []
    for j in sorted(own["judge"].unique()):
        sub = own[own["judge"] == j]
        k = int(sub["correct"].sum())
        n = int(len(sub))
        acc = k / n if n else float("nan")
        pval = binomtest(k, n, p=0.25, alternative="greater").pvalue if scipy_available else binom_sf(k, n, 0.25)
        rows.append((j, n, k, acc, pval))
        pvals.append(pval)

    if scipy_available:
        rej, padj, *_ = multipletests(pvals, alpha=0.05, method="fdr_bh")
        rej = list(map(bool, rej))
        padj = list(map(float, padj))
    else:
        rej, padj = bh_fdr(pvals, alpha=0.05)
    table = pd.DataFrame(rows, columns=["judge", "n", "correct", "accuracy", "p_raw"])
    table["p_fdr_bh"] = padj
    table["reject_at_5pct_fdr"] = rej
    emit(table.round(4).pipe(table_md, index=False))
    emit("")
    n_supports = int(sum(rej))
    emit(f"Judges identifying their own outputs above chance (FDR-corrected): {n_supports} of {len(rows)}.")
    emit(f"**H2 verdict:** {'SUPPORTED' if n_supports >= 2 else 'NOT SUPPORTED'} (threshold: >= 2 of 4).")
    emit("")

    emit("### C4 confusion matrices (rows = true_author, columns = predicted_author)")
    emit("")
    for j in sorted(recog["judge"].unique()):
        sub = recog[recog["judge"] == j]
        cm = pd.crosstab(sub["true_author"], sub["predicted_author"])
        emit(f"**Judge: {j}**")
        emit("")
        emit(cm.pipe(table_md))
        emit("")


# ---------- H3 / H4 ----------
def test_h3_h4(scores: pd.DataFrame) -> None:
    emit("## H3 / H4: Attenuation by C2 (style) and C3 (warning)")
    emit("")
    conds_present = set(scores["condition"].unique())
    if "c1" not in conds_present:
        emit("_No C1 rows yet; cannot evaluate H3/H4._")
        return
    smf = statsmodels_formula_api()
    use_builtin = smf is None

    def fit_interaction(df: pd.DataFrame, conds: list[str]) -> dict:
        df = df[df["condition"].isin(conds)].copy()
        if df.empty:
            return {}
        df["condition"] = pd.Categorical(df["condition"], categories=["c1"] + [c for c in conds if c != "c1"], ordered=False)
        model = smf.ols(
            "composite ~ author_is_self * C(condition) + C(author) + C(judge) + C(category)",
            data=df,
        ).fit(cov_type="cluster", cov_kwds={"groups": df["prompt_id"]})
        beta_c1 = model.params.get("author_is_self", np.nan)
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

    try:
        if use_builtin:
            emit("Using built-in OLS interaction fallback with cluster-robust SE by prompt_id.")
            h3 = builtin_interaction_fit(scores, ["c1", "c2"]) if "c2" in conds_present else {}
            h4 = builtin_interaction_fit(scores, ["c1", "c3"]) if "c3" in conds_present else {}
        else:
            h3 = fit_interaction(scores, ["c1", "c2"]) if "c2" in conds_present else {}
            h4 = fit_interaction(scores, ["c1", "c3"]) if "c3" in conds_present else {}
    except Exception as e:
        emit(f"H3/H4 interaction model failed ({e!s}); attenuation verdicts not available.")
        emit("")
        return

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
def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    args.scores = resolve_path(args.scores)
    args.recognition = resolve_path(args.recognition)
    args.judgments_dir = resolve_path(args.judgments_dir)
    args.report = resolve_path(args.report)

    emit("# Pre-registered analysis report")
    emit("")
    emit("Generated by `analysis/run_analysis.py`. See `DESIGN.md` for the pre-registered plan.")
    emit("")

    scores, recog = load_data(args)
    if scores is not None:
        test_h1(scores, mixedlm_timeout_seconds=args.mixedlm_timeout_seconds)
        test_h3_h4(scores)
    if recog is not None:
        test_h2(recog)

    emit(f"\nReport written to {rel(args.report)}")
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text("\n".join(_report_lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
