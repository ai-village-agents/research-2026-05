#!/usr/bin/env python3
"""Profile redundancy and separability of the five rubric dimensions.

Post-v1.3.0 exploratory supplement. Uses only canonical long_scores.csv.
No SciPy dependency.
"""
from __future__ import annotations

from pathlib import Path
import itertools
import math

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "experiments" / "replication-wave" / "results"
INPUT = RESULTS / "long_scores.csv"

DIMENSIONS = [
    "correctness",
    "completeness",
    "clarity",
    "creativity",
    "constraint_adherence",
]


def _spearman_no_scipy(x: pd.Series, y: pd.Series) -> float:
    paired = pd.concat([x, y], axis=1).dropna()
    if len(paired) < 2:
        return float("nan")
    rx = paired.iloc[:, 0].rank(method="average")
    ry = paired.iloc[:, 1].rank(method="average")
    if rx.nunique() < 2 or ry.nunique() < 2:
        return float("nan")
    return float(rx.corr(ry, method="pearson"))


def _cronbach_alpha(frame: pd.DataFrame) -> float:
    x = frame[DIMENSIONS].dropna().astype(float)
    k = len(DIMENSIONS)
    if len(x) < 2:
        return float("nan")
    item_vars = x.var(axis=0, ddof=1).sum()
    total_var = x.sum(axis=1).var(ddof=1)
    if total_var <= 0:
        return float("nan")
    return float(k / (k - 1) * (1 - item_vars / total_var))


def _pc_summary(frame: pd.DataFrame) -> dict[str, float]:
    x = frame[DIMENSIONS].dropna().astype(float)
    if len(x) < 2:
        return {"pc1_variance_share": float("nan"), "pc2_variance_share": float("nan")}
    z = (x - x.mean()) / x.std(ddof=1)
    z = z.fillna(0.0)
    corr = np.corrcoef(z.to_numpy(), rowvar=False)
    vals, _vecs = np.linalg.eigh(corr)
    vals = np.sort(vals)[::-1]
    total = vals.sum()
    return {
        "pc1_variance_share": float(vals[0] / total) if total else float("nan"),
        "pc2_variance_share": float(vals[1] / total) if len(vals) > 1 and total else float("nan"),
    }


def _pc_loadings(frame: pd.DataFrame) -> pd.DataFrame:
    x = frame[DIMENSIONS].dropna().astype(float)
    z = (x - x.mean()) / x.std(ddof=1)
    z = z.fillna(0.0)
    corr = np.corrcoef(z.to_numpy(), rowvar=False)
    vals, vecs = np.linalg.eigh(corr)
    order = np.argsort(vals)[::-1]
    vals = vals[order]
    vecs = vecs[:, order]
    # Orient PC1 so all quality dimensions load positive on average.
    if vecs[:, 0].mean() < 0:
        vecs[:, 0] *= -1
    if vecs[:, 1].sum() < 0:
        vecs[:, 1] *= -1
    return pd.DataFrame({
        "dimension": DIMENSIONS,
        "pc1_loading": vecs[:, 0],
        "pc2_loading": vecs[:, 1],
        "pc1_eigenvalue": vals[0],
        "pc2_eigenvalue": vals[1],
        "pc1_variance_share": vals[0] / vals.sum(),
        "pc2_variance_share": vals[1] / vals.sum(),
    })


def _self_gap(frame: pd.DataFrame, dims: list[str]) -> float:
    c1 = frame[frame["condition"].str.lower() == "c1"].copy()
    c1["score"] = c1[dims].mean(axis=1)
    gaps = []
    prompt_col = "prompt_id" if "prompt_id" in c1.columns else "prompt"
    for (judge, prompt), g in c1.groupby(["judge", prompt_col]):
        self_rows = g[g["author"] == judge]
        other_rows = g[g["author"] != judge]
        if len(self_rows) and len(other_rows):
            gaps.append(float(self_rows["score"].mean() - other_rows["score"].mean()))
    return float(np.mean(gaps))


def _fmt(x: float, nd: int = 3) -> str:
    if pd.isna(x):
        return "NA"
    return f"{x:.{nd}f}"


def _md_table(df: pd.DataFrame, cols: list[str], formats: dict[str, str] | None = None) -> str:
    formats = formats or {}
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] + ["---:" for _ in cols[1:]]) + "|"]
    for _, row in df[cols].iterrows():
        vals = []
        for col in cols:
            val = row[col]
            if col in formats and pd.notna(val):
                vals.append(format(val, formats[col]))
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def main() -> None:
    df = pd.read_csv(INPUT)
    df["composite"] = df[DIMENSIONS].mean(axis=1)

    summary_rows = []
    groups: list[tuple[str, str, pd.DataFrame]] = [("all", "all", df)]
    groups += [("condition", k, g) for k, g in df.groupby("condition")]
    groups += [("judge", k, g) for k, g in df.groupby("judge")]
    for scope, value, g in groups:
        pcs = _pc_summary(g)
        summary_rows.append({
            "scope": scope,
            "value": value,
            "n": len(g),
            "cronbach_alpha": _cronbach_alpha(g),
            "mean_pairwise_pearson": float(np.nanmean([g[a].corr(g[b]) for a, b in itertools.combinations(DIMENSIONS, 2)])),
            "mean_pairwise_spearman": float(np.nanmean([_spearman_no_scipy(g[a], g[b]) for a, b in itertools.combinations(DIMENSIONS, 2)])),
            **pcs,
        })
    summary = pd.DataFrame(summary_rows)

    corr_rows = []
    for a, b in itertools.combinations(DIMENSIONS, 2):
        corr_rows.append({
            "dimension_a": a,
            "dimension_b": b,
            "pearson": df[a].corr(df[b]),
            "spearman": _spearman_no_scipy(df[a], df[b]),
            "mean_abs_difference": float((df[a] - df[b]).abs().mean()),
        })
    corr = pd.DataFrame(corr_rows).sort_values("pearson", ascending=False)

    full_gap = _self_gap(df, DIMENSIONS)
    loo_rows = []
    for dropped in DIMENSIONS:
        kept = [d for d in DIMENSIONS if d != dropped]
        gap = _self_gap(df, kept)
        loo_rows.append({
            "dropped_dimension": dropped,
            "kept_dimensions": "+".join(kept),
            "c1_pooled_self_gap": gap,
            "delta_vs_full_composite": gap - full_gap,
        })
    loo = pd.DataFrame(loo_rows).sort_values("delta_vs_full_composite")

    loadings = _pc_loadings(df)

    summary.to_csv(RESULTS / "dimension_redundancy_profile.csv", index=False)
    corr.to_csv(RESULTS / "dimension_pairwise_correlations.csv", index=False)
    loadings.to_csv(RESULTS / "dimension_pca_loadings.csv", index=False)
    loo.to_csv(RESULTS / "dimension_leave_one_out_self_gap.csv", index=False)

    all_row = summary[(summary.scope == "all") & (summary.value == "all")].iloc[0]
    strongest = corr.iloc[0]
    weakest = corr.iloc[-1]
    most_shift = loo.iloc[loo["delta_vs_full_composite"].abs().argmax()]

    md = []
    md.append("# Rubric-dimension redundancy profile (post-v1.3.0 exploratory supplement)\n")
    md.append("This supplement does **not** change the headline v1.3.0 estimands. It asks a measurement question: are the five 1–10 rubric dimensions behaving like five largely independent axes, or mostly as repeated noisy views of a single latent quality factor? It uses only canonical `long_scores.csv`.\n")
    md.append("## Main result\n")
    md.append(f"Across all 480 replication-wave ratings, Cronbach's alpha across the five dimensions is **{_fmt(all_row.cronbach_alpha)}**, the mean pairwise Pearson correlation is **{_fmt(all_row.mean_pairwise_pearson)}**, and the first principal component explains **{100*all_row.pc1_variance_share:.1f}%** of standardized dimension variance. That means the composite is mostly a general-quality score, not five independent measurements.\n")
    md.append(f"The strongest dimension pair is **{strongest.dimension_a} ↔ {strongest.dimension_b}** (Pearson {_fmt(strongest.pearson)}, Spearman {_fmt(strongest.spearman)}); the weakest is **{weakest.dimension_a} ↔ {weakest.dimension_b}** (Pearson {_fmt(weakest.pearson)}, Spearman {_fmt(weakest.spearman)}).\n")
    md.append(f"Leaving out any one dimension barely changes the pooled C1 self-preference gap: the largest absolute shift is dropping **{most_shift.dropped_dimension}**, which changes the gap by **{_fmt(most_shift.delta_vs_full_composite)}** points from the full-composite gap of **{_fmt(full_gap)}**.\n")
    md.append("## Overall/by-condition/by-judge reliability\n")
    md.append(_md_table(summary, ["scope", "value", "n", "cronbach_alpha", "mean_pairwise_pearson", "mean_pairwise_spearman", "pc1_variance_share", "pc2_variance_share"], {"cronbach_alpha": ".3f", "mean_pairwise_pearson": ".3f", "mean_pairwise_spearman": ".3f", "pc1_variance_share": ".3f", "pc2_variance_share": ".3f"}))
    md.append("\n## Pairwise dimension correlations\n")
    md.append(_md_table(corr, ["dimension_a", "dimension_b", "pearson", "spearman", "mean_abs_difference"], {"pearson": ".3f", "spearman": ".3f", "mean_abs_difference": ".3f"}))
    md.append("\n## First two principal components\n")
    md.append("Loadings are from a PCA of the all-row dimension correlation matrix; PC1 is oriented positive so larger scores mean higher general quality.\n")
    md.append(_md_table(loadings, ["dimension", "pc1_loading", "pc2_loading", "pc1_variance_share", "pc2_variance_share"], {"pc1_loading": ".3f", "pc2_loading": ".3f", "pc1_variance_share": ".3f", "pc2_variance_share": ".3f"}))
    md.append("\n## Leave-one-dimension C1 self-gap sensitivity\n")
    md.append(_md_table(loo, ["dropped_dimension", "c1_pooled_self_gap", "delta_vs_full_composite"], {"c1_pooled_self_gap": ".3f", "delta_vs_full_composite": ".3f"}))
    md.append("\n## Interpretation\n")
    md.append("- The five rubric dimensions are highly redundant: most variance is a shared quality factor. This supports using the simple mean composite for headline analyses.\n")
    md.append("- Redundancy does not mean the dimensions are useless. Per-dimension bias analyses remain informative because self-preference can concentrate more on constraint/completeness than on style, but the composite is not fragile to dropping any single dimension.\n")
    md.append("- This is a post-release measurement-validity diagnostic; it complements, rather than replaces, the observational and label-swap self-preference estimands.\n")
    (RESULTS / "dimension_redundancy_profile.md").write_text("\n".join(md))
    print("wrote dimension redundancy supplement")


if __name__ == "__main__":
    main()
