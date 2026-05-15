#!/usr/bin/env python3
"""Summarize row/column asymmetry in the 4x4 label-effect matrix.

Post-v1.3.0 exploratory supplement. Uses the public label_effect_matrix.csv
and label_effect_matrix_multiplicity.csv; does not recompute native scores.
"""
from __future__ import annotations

from pathlib import Path
import math

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RESULTS = ROOT / "experiments" / "replication-wave" / "results"
MATRIX_PATH = RESULTS / "label_effect_matrix.csv"
MULT_PATH = RESULTS / "label_effect_matrix_multiplicity.csv"


def _entropy_signed(values: pd.Series) -> float:
    weights = values.abs().to_numpy(dtype=float)
    total = weights.sum()
    if total <= 0:
        return float("nan")
    p = weights / total
    p = p[p > 0]
    return float(-(p * np.log(p)).sum() / math.log(len(values)))


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
            if pd.isna(val):
                vals.append("NA")
            elif col in formats:
                vals.append(format(val, formats[col]))
            else:
                vals.append(str(val))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)


def main() -> None:
    matrix = pd.read_csv(MATRIX_PATH)
    mult = pd.read_csv(MULT_PATH)
    if "mean" in mult.columns:
        mult = mult.rename(columns={"mean": "mean_residual_multiplicity"})
    df = matrix.merge(mult[["judge", "displayed_label", "bh_q", "sig_bh_05", "sig_bonf_05"]], on=["judge", "displayed_label"], how="left")
    labels = sorted(df["judge"].unique())

    row_rows = []
    for judge, g in df.groupby("judge"):
        g = g.copy()
        diag = float(g.loc[g["displayed_label"] == judge, "mean_residual"].iloc[0])
        off = g[g["displayed_label"] != judge]
        strongest_pos = g.sort_values("mean_residual", ascending=False).iloc[0]
        strongest_neg = g.sort_values("mean_residual", ascending=True).iloc[0]
        l1 = float(g["mean_residual"].abs().sum())
        l2 = float(np.sqrt((g["mean_residual"] ** 2).sum()))
        row_rows.append({
            "judge": judge,
            "row_mean": float(g["mean_residual"].mean()),
            "row_l1_abs": l1,
            "row_l2_norm": l2,
            "max_abs_cell": float(g["mean_residual"].abs().max()),
            "diagonal_self_effect": diag,
            "offdiag_mean": float(off["mean_residual"].mean()),
            "diag_minus_offdiag_mean": diag - float(off["mean_residual"].mean()),
            "diagonal_abs_share": float(abs(diag) / l1) if l1 else pd.NA,
            "signed_entropy_abs_effects": _entropy_signed(g["mean_residual"]),
            "n_positive_cells": int((g["mean_residual"] > 0).sum()),
            "n_negative_cells": int((g["mean_residual"] < 0).sum()),
            "n_zero_cells": int((g["mean_residual"] == 0).sum()),
            "n_bh_sig_cells": int(g["sig_bh_05"].fillna(0).sum()),
            "strongest_positive_label": str(strongest_pos["displayed_label"]),
            "strongest_positive_effect": float(strongest_pos["mean_residual"]),
            "strongest_negative_label": str(strongest_neg["displayed_label"]),
            "strongest_negative_effect": float(strongest_neg["mean_residual"]),
        })
    rows = pd.DataFrame(row_rows).sort_values("row_l1_abs", ascending=False)

    col_rows = []
    for label, g in df.groupby("displayed_label"):
        strongest_pos = g.sort_values("mean_residual", ascending=False).iloc[0]
        strongest_neg = g.sort_values("mean_residual", ascending=True).iloc[0]
        col_rows.append({
            "displayed_label": label,
            "column_mean": float(g["mean_residual"].mean()),
            "column_l1_abs": float(g["mean_residual"].abs().sum()),
            "column_l2_norm": float(np.sqrt((g["mean_residual"] ** 2).sum())),
            "n_positive_judges": int((g["mean_residual"] > 0).sum()),
            "n_negative_judges": int((g["mean_residual"] < 0).sum()),
            "n_zero_judges": int((g["mean_residual"] == 0).sum()),
            "n_bh_sig_judges": int(g["sig_bh_05"].fillna(0).sum()),
            "strongest_positive_judge": str(strongest_pos["judge"]),
            "strongest_positive_effect": float(strongest_pos["mean_residual"]),
            "strongest_negative_judge": str(strongest_neg["judge"]),
            "strongest_negative_effect": float(strongest_neg["mean_residual"]),
        })
    cols = pd.DataFrame(col_rows).sort_values("column_l1_abs", ascending=False)

    # Directed asymmetry: for each unordered pair A/B, compare A-judge response to B-label vs B-judge response to A-label.
    pair_rows = []
    for i, a in enumerate(labels):
        for b in labels[i+1:]:
            ab = float(df[(df["judge"] == a) & (df["displayed_label"] == b)]["mean_residual"].iloc[0])
            ba = float(df[(df["judge"] == b) & (df["displayed_label"] == a)]["mean_residual"].iloc[0])
            pair_rows.append({
                "pair": f"{a} ↔ {b}",
                "a_judge": a,
                "b_judge": b,
                "a_response_to_b_label": ab,
                "b_response_to_a_label": ba,
                "directed_difference_a_to_b_minus_b_to_a": ab - ba,
                "mean_mutual_effect": (ab + ba) / 2,
                "mean_abs_mutual_effect": (abs(ab) + abs(ba)) / 2,
            })
    pairs = pd.DataFrame(pair_rows).sort_values("mean_abs_mutual_effect", ascending=False)

    rows.to_csv(RESULTS / "label_effect_asymmetry_by_judge.csv", index=False)
    cols.to_csv(RESULTS / "label_effect_asymmetry_by_label.csv", index=False)
    pairs.to_csv(RESULTS / "label_effect_directed_pair_asymmetry.csv", index=False)

    top_row = rows.iloc[0]
    low_row = rows.iloc[-1]
    top_col = cols.iloc[0]
    top_pair = pairs.iloc[0]
    sig_rows = rows[rows["n_bh_sig_cells"] > 0]

    md = []
    md.append("# Label-effect asymmetry profile (post-v1.3.0 exploratory supplement)\n")
    md.append("This supplement does **not** change the v1.3.0 headline estimands. It compresses the 4×4 causal displayed-label matrix into row, column, and directed-pair asymmetry summaries: which judges are most label-sensitive, which displayed labels attract the most movement, and whether pairwise label reactions are reciprocated.\n")
    md.append("## Main result\n")
    md.append(f"By total absolute row movement, the most label-sensitive judge is **{top_row.judge}** (row L1 = {_fmt(top_row.row_l1_abs)}), while the least label-sensitive is **{low_row.judge}** (row L1 = {_fmt(low_row.row_l1_abs)}). The largest displayed-label column by absolute movement is **{top_col.displayed_label}** (column L1 = {_fmt(top_col.column_l1_abs)}).\n")
    if len(sig_rows):
        sig_text = ", ".join(f"{r.judge} ({int(r.n_bh_sig_cells)} BH-significant cells)" for _, r in sig_rows.iterrows())
        md.append(f"Only **{sig_text}** has any BH-significant cells; all other row/column asymmetry should be read descriptively.\n")
    md.append(f"The strongest directed pair by mean absolute mutual off-diagonal movement is **{top_pair.pair}** (mean abs mutual effect {_fmt(top_pair.mean_abs_mutual_effect)}), driven by {top_pair.a_judge}'s response to the {top_pair.b_judge} label ({_fmt(top_pair.a_response_to_b_label)}) versus {top_pair.b_judge}'s response to the {top_pair.a_judge} label ({_fmt(top_pair.b_response_to_a_label)}).\n")
    md.append("## Row profile: label sensitivity by judge\n")
    md.append(_md_table(rows, ["judge", "row_l1_abs", "row_l2_norm", "diagonal_self_effect", "offdiag_mean", "diag_minus_offdiag_mean", "diagonal_abs_share", "n_positive_cells", "n_negative_cells", "n_zero_cells", "n_bh_sig_cells", "strongest_positive_label", "strongest_positive_effect", "strongest_negative_label", "strongest_negative_effect"], {"row_l1_abs": ".3f", "row_l2_norm": ".3f", "diagonal_self_effect": ".3f", "offdiag_mean": ".3f", "diag_minus_offdiag_mean": ".3f", "diagonal_abs_share": ".3f", "strongest_positive_effect": ".3f", "strongest_negative_effect": ".3f"}))
    md.append("\n## Column profile: movement attracted by displayed label\n")
    md.append(_md_table(cols, ["displayed_label", "column_l1_abs", "column_l2_norm", "column_mean", "n_positive_judges", "n_negative_judges", "n_zero_judges", "n_bh_sig_judges", "strongest_positive_judge", "strongest_positive_effect", "strongest_negative_judge", "strongest_negative_effect"], {"column_l1_abs": ".3f", "column_l2_norm": ".3f", "column_mean": ".3f", "strongest_positive_effect": ".3f", "strongest_negative_effect": ".3f"}))
    md.append("\n## Directed pair asymmetry\n")
    md.append(_md_table(pairs, ["pair", "a_response_to_b_label", "b_response_to_a_label", "directed_difference_a_to_b_minus_b_to_a", "mean_mutual_effect", "mean_abs_mutual_effect"], {"a_response_to_b_label": ".3f", "b_response_to_a_label": ".3f", "directed_difference_a_to_b_minus_b_to_a": ".3f", "mean_mutual_effect": ".3f", "mean_abs_mutual_effect": ".3f"}))
    md.append("\n## Interpretation\n")
    md.append("- Label sensitivity is row-concentrated rather than universal: Gemini supplies most total movement and all multiplicity-robust cells; GPT is exactly invariant.\n")
    md.append("- The largest displayed-label column by total absolute movement is Claude, mostly because Kimi has a non-significant pro-Claude tilt; the largest single negative cell remains Gemini's anti-Kimi-label effect.\n")
    md.append("- Directed reactions are not reciprocal: a judge's response to another model's label generally does not predict the other model's response to the first judge's label.\n")
    (RESULTS / "label_effect_asymmetry_profile.md").write_text("\n".join(md))
    print("wrote label effect asymmetry supplement")


if __name__ == "__main__":
    main()
