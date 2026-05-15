#!/usr/bin/env python3
"""Variance partition for native paired label-swap residuals.

Post-v1.3.0 exploratory supplement. Uses only the public paired_label_swap.csv.
The goal is to ask whether the causal displayed-label effects are best
understood as a universal displayed-label pull or as judge-specific
judge × displayed-label interaction.
"""
from __future__ import annotations

from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "experiments" / "replication-wave" / "results"
IN_PATH = RESULTS / "paired_label_swap.csv"
OUT_MD = RESULTS / "label_effect_variance_partition.md"
OUT_COMPONENTS = RESULTS / "label_effect_variance_partition_components.csv"
OUT_CELLS = RESULTS / "label_effect_variance_partition_cells.csv"

BOOT_ITERS = 4000
SEED = 20260515


def _design(df: pd.DataFrame, terms: list[str]) -> np.ndarray:
    parts = [pd.Series(1.0, index=df.index, name="intercept")]
    if "judge" in terms:
        parts.append(pd.get_dummies(df["judge"], prefix="judge", drop_first=True, dtype=float))
    if "label" in terms:
        parts.append(pd.get_dummies(df["displayed_label"], prefix="label", drop_first=True, dtype=float))
    if "cell" in terms:
        parts.append(pd.get_dummies(df["judge"] + "||" + df["displayed_label"], prefix="cell", drop_first=True, dtype=float))
    return pd.concat(parts, axis=1).to_numpy(dtype=float)


def _sse(y: np.ndarray, x: np.ndarray) -> float:
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    resid = y - x @ beta
    return float(np.dot(resid, resid))


def _clean(x: float) -> float:
    return 0.0 if abs(x) < 1e-12 else float(x)


def decompose(df: pd.DataFrame) -> dict[str, float]:
    y = df["residual"].to_numpy(dtype=float)
    sse_intercept = _sse(y, _design(df, []))
    sse_judge = _sse(y, _design(df, ["judge"]))
    sse_additive = _sse(y, _design(df, ["judge", "label"]))
    sse_cell = _sse(y, _design(df, ["cell"]))

    ss_judge = sse_intercept - sse_judge
    ss_label = sse_judge - sse_additive
    ss_interaction = sse_additive - sse_cell
    ss_within = sse_cell
    total = sse_intercept
    structured = ss_judge + ss_label + ss_interaction
    out = {
        "ss_total": total,
        "ss_judge_main": ss_judge,
        "ss_displayed_label_main": ss_label,
        "ss_judge_x_label_interaction": ss_interaction,
        "ss_within_cell": ss_within,
        "ss_structured_cell_means": structured,
        "share_total_judge_main": ss_judge / total if total else np.nan,
        "share_total_displayed_label_main": ss_label / total if total else np.nan,
        "share_total_judge_x_label_interaction": ss_interaction / total if total else np.nan,
        "share_total_within_cell": ss_within / total if total else np.nan,
        "share_total_structured_cell_means": structured / total if total else np.nan,
        "share_structured_judge_main": ss_judge / structured if structured else np.nan,
        "share_structured_displayed_label_main": ss_label / structured if structured else np.nan,
        "share_structured_judge_x_label_interaction": ss_interaction / structured if structured else np.nan,
    }
    return {k: (_clean(v) if not pd.isna(v) else v) for k, v in out.items()}


def add_residuals(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df["residual"] = df["composite"] - df.groupby(["judge", "response_hash"])["composite"].transform("mean")
    return df


def bootstrap(df: pd.DataFrame, b: int = BOOT_ITERS, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    hashes = np.array(sorted(df["response_hash"].unique()))
    by_hash = {h: g for h, g in df.groupby("response_hash", sort=False)}
    rows = []
    for i in range(b):
        sample = rng.choice(hashes, size=len(hashes), replace=True)
        boot = pd.concat([by_hash[h] for h in sample], ignore_index=True)
        d = decompose(boot)
        d["bootstrap_iter"] = i
        rows.append(d)
    return pd.DataFrame(rows)


def ci(series: pd.Series) -> tuple[float, float]:
    return tuple(np.quantile(series.dropna().to_numpy(dtype=float), [0.025, 0.975]))


def fmt(x: float, nd: int = 3) -> str:
    if pd.isna(x):
        return "NA"
    return f"{x:.{nd}f}"


def pct(x: float) -> str:
    if pd.isna(x):
        return "NA"
    return f"{100*x:.1f}%"


def main() -> None:
    raw = pd.read_csv(IN_PATH)
    df = add_residuals(raw)
    observed = decompose(df)
    boots = bootstrap(df)

    component_specs = [
        ("judge_main", "Judge main effect", "Between-judge offset after within-(judge,response) centering; expected to be exactly zero by construction."),
        ("displayed_label_main", "Displayed-label main effect", "Universal pull of a displayed label across judges."),
        ("judge_x_label_interaction", "Judge × displayed-label interaction", "Judge-specific departures from the universal displayed-label pull."),
        ("within_cell", "Within-cell residual", "Response-level idiosyncratic label noise left after the 4×4 cell means."),
        ("structured_cell_means", "All structured 4×4 cell means", "Judge main + displayed-label main + judge×label interaction."),
    ]
    component_rows = []
    for key, label, definition in component_specs:
        ss_key = f"ss_{key}"
        share_key = f"share_total_{key}"
        if ss_key not in observed:
            continue
        lo, hi = ci(boots[share_key]) if share_key in boots else (np.nan, np.nan)
        component_rows.append({
            "component": key,
            "label": label,
            "definition": definition,
            "sum_squares": observed[ss_key],
            "share_total": observed[share_key],
            "share_total_ci_lo": lo,
            "share_total_ci_hi": hi,
        })
    components = pd.DataFrame(component_rows)
    components.to_csv(OUT_COMPONENTS, index=False)

    cell = df.groupby(["judge", "displayed_label"]).agg(cell_mean=("residual", "mean"), n=("residual", "size")).reset_index()
    row_mean = df.groupby("judge")["residual"].mean().rename("judge_mean")
    col_mean = df.groupby("displayed_label")["residual"].mean().rename("displayed_label_mean")
    grand = float(df["residual"].mean())
    cell = cell.merge(row_mean, on="judge").merge(col_mean, on="displayed_label")
    cell["additive_expected"] = cell["judge_mean"] + cell["displayed_label_mean"] - grand
    cell["interaction_residual"] = cell["cell_mean"] - cell["additive_expected"]
    interaction_ss = observed["ss_judge_x_label_interaction"]
    cell["interaction_ss_contribution"] = cell["n"] * cell["interaction_residual"] ** 2
    cell["share_interaction_ss"] = cell["interaction_ss_contribution"] / interaction_ss if interaction_ss else np.nan
    cell = cell.sort_values("interaction_residual", key=lambda s: s.abs(), ascending=False)
    cell.to_csv(OUT_CELLS, index=False)

    structured_ci = ci(boots["share_total_structured_cell_means"])
    interaction_struct_ci = ci(boots["share_structured_judge_x_label_interaction"])
    label_struct_ci = ci(boots["share_structured_displayed_label_main"])

    md = []
    md.append("# Label-effect variance partition (post-v1.3.0 exploratory supplement)\n")
    md.append("This supplement asks whether the native label-swap effects are mainly a universal displayed-label pull or a judge-specific interaction. It uses the public `paired_label_swap.csv`, residualizes each score within `(judge, response_hash)`, and decomposes the residual sum of squares into nested models: intercept only, judge main effect, judge + displayed-label additive effects, and full 4×4 judge × displayed-label cells. Bootstrap CIs resample `response_hash` clusters (B=4000).\n")
    md.append("## Main result\n")
    md.append(f"The 4×4 cell means explain **{pct(observed['share_total_structured_cell_means'])}** of total within-response label-residual variance (cluster-bootstrap 95% CI {pct(structured_ci[0])} to {pct(structured_ci[1])}); the remaining **{pct(observed['share_total_within_cell'])}** is within-cell response-level variation. Within the structured 4×4 component, **{pct(observed['share_structured_judge_x_label_interaction'])}** is judge × displayed-label interaction (CI {pct(interaction_struct_ci[0])} to {pct(interaction_struct_ci[1])}) versus **{pct(observed['share_structured_displayed_label_main'])}** universal displayed-label pull (CI {pct(label_struct_ci[0])} to {pct(label_struct_ci[1])}).\n")
    md.append("Interpretation: the causal label effects are small relative to response-level score noise, but the systematic part is mostly *who reacts to which label*, not a uniform premium or penalty attached to a label across all judges.\n")

    md.append("## Variance components\n")
    md.append("| component | share_total | 95% CI | sum_squares | interpretation |")
    md.append("|---|---:|---:|---:|---|")
    for _, r in components.iterrows():
        md.append(f"| {r['label']} | {pct(r.share_total)} | [{pct(r.share_total_ci_lo)}, {pct(r.share_total_ci_hi)}] | {fmt(r.sum_squares)} | {r.definition} |")

    md.append("\n## Largest judge × displayed-label departures from additivity\n")
    md.append("A positive interaction residual means the cell is higher than expected from a universal displayed-label pull; a negative residual means it is lower.\n")
    md.append("| judge | displayed_label | cell_mean | additive_expected | interaction_residual | share_interaction_ss |")
    md.append("|---|---|---:|---:|---:|---:|")
    for _, r in cell.head(8).iterrows():
        md.append(f"| {r.judge} | {r.displayed_label} | {fmt(r.cell_mean)} | {fmt(r.additive_expected)} | {fmt(r.interaction_residual)} | {pct(r.share_interaction_ss)} |")

    md.append("\n## Notes\n")
    md.append("- The judge main effect is zero by construction: residuals are centered within each `(judge, response_hash)` pair, so this supplement is about displayed-label structure, not judge leniency.\n")
    md.append("- The largest interaction departures are Gemini's self-label boost and anti-Kimi-label penalty, followed by Kimi's non-significant pro-Claude tilt; this is consistent with the matrix and multiplicity-correction supplements but summarizes the pattern as variance explained.\n")
    md.append(f"- Source files: [`paired_label_swap.csv`](paired_label_swap.csv), [`label_effect_variance_partition_components.csv`](label_effect_variance_partition_components.csv), and [`label_effect_variance_partition_cells.csv`](label_effect_variance_partition_cells.csv).\n")
    OUT_MD.write_text("\n".join(md))
    print(f"wrote {OUT_MD}")
    print(f"wrote {OUT_COMPONENTS}")
    print(f"wrote {OUT_CELLS}")


if __name__ == "__main__":
    main()
