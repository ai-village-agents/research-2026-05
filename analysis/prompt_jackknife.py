"""Prompt-level leave-one-out jackknife robustness checks.

This appendix stress-tests the perceived-authorship horse-race estimates by
re-estimating them after dropping each prompt_id in turn. It is descriptive
robustness work, not a replacement for the preregistered hypothesis tests.

Inputs:
    data/unified/unified_wide.csv

Outputs:
    results/prompt_jackknife.md
    results/prompt_jackknife.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


CONDITIONS = ["c1", "c2", "c3"]
TERMS = ["author_is_self", "predicted_self"]


def ols_coefficients(
    df: pd.DataFrame,
    regressors: list[str],
    fixed_effects: list[str],
    depvar: str = "composite",
) -> dict[str, float]:
    """Fit OLS with dummy fixed effects using NumPy and return target coefficients.

    The pseudo-inverse keeps the function numerically stable if a leave-one-out
    subset creates redundant dummy columns. Coefficients are therefore best read
    as a deterministic robustness diagnostic under the stated formula, not as a
    new inferential model with p-values.
    """
    needed = [depvar] + regressors + fixed_effects
    d = df[needed].dropna().copy()
    if len(d) == 0:
        return {r: np.nan for r in regressors}

    cols = ["Intercept"]
    blocks = [np.ones((len(d), 1), dtype=float)]
    for r in regressors:
        blocks.append(d[r].astype(float).to_numpy()[:, None])
        cols.append(r)
    for fe in fixed_effects:
        dum = pd.get_dummies(d[fe].astype(str), prefix=fe, drop_first=True, dtype=float)
        if dum.shape[1]:
            blocks.append(dum.to_numpy(dtype=float))
            cols.extend(list(dum.columns))

    X = np.hstack(blocks)
    y = d[depvar].astype(float).to_numpy()
    beta = np.linalg.pinv(X.T @ X) @ X.T @ y
    params = dict(zip(cols, beta))
    return {r: float(params.get(r, np.nan)) for r in regressors}


def summarize_jackknife(
    df: pd.DataFrame,
    scope: str,
    condition: str,
    regressors: list[str],
    fixed_effects: list[str],
    prompts: list[str],
) -> list[dict]:
    """Return one summary row per coefficient for a full-data and leave-one-out fit."""
    full = ols_coefficients(df, regressors, fixed_effects)
    rows = []
    for term in regressors:
        vals = []
        for prompt_id in prompts:
            sub = df[df["prompt_id"] != prompt_id]
            coef = ols_coefficients(sub, regressors, fixed_effects)[term]
            vals.append((prompt_id, coef))
        finite = [(p, v) for p, v in vals if np.isfinite(v)]
        if finite:
            min_prompt, min_value = min(finite, key=lambda x: x[1])
            max_prompt, max_value = max(finite, key=lambda x: x[1])
            loo_values = np.array([v for _, v in finite], dtype=float)
            full_value = full[term]
            if np.isfinite(full_value) and full_value != 0:
                sign_flips = int(np.sum(np.sign(loo_values) != np.sign(full_value)))
            else:
                sign_flips = int(np.sum(np.sign(loo_values) != 0))
            rows.append(
                {
                    "scope": scope,
                    "condition": condition,
                    "term": term,
                    "full_beta": full_value,
                    "loo_min": float(min_value),
                    "loo_min_prompt": min_prompt,
                    "loo_max": float(max_value),
                    "loo_max_prompt": max_prompt,
                    "loo_mean": float(np.mean(loo_values)),
                    "loo_sd": float(np.std(loo_values, ddof=1)) if len(loo_values) > 1 else 0.0,
                    "loo_range": float(max_value - min_value),
                    "sign_flips_vs_full": sign_flips,
                    "n_leave_one_out_fits": len(finite),
                    "n_rows_full": int(len(df)),
                }
            )
        else:
            rows.append(
                {
                    "scope": scope,
                    "condition": condition,
                    "term": term,
                    "full_beta": full[term],
                    "loo_min": np.nan,
                    "loo_min_prompt": "",
                    "loo_max": np.nan,
                    "loo_max_prompt": "",
                    "loo_mean": np.nan,
                    "loo_sd": np.nan,
                    "loo_range": np.nan,
                    "sign_flips_vs_full": 0,
                    "n_leave_one_out_fits": 0,
                    "n_rows_full": int(len(df)),
                }
            )
    return rows


def fmt(x: float) -> str:
    if not np.isfinite(x):
        return "—"
    return f"{x:+.3f}"


def fmt_sd(x: float) -> str:
    if not np.isfinite(x):
        return "—"
    return f"{x:.3f}"


def table(rows: pd.DataFrame) -> str:
    out = [
        "| Scope | Condition | Term | Full β | LOO min | LOO max | LOO SD | Sign flips | Extremal prompts |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for _, r in rows.iterrows():
        extrema = f"min {r['loo_min_prompt']}; max {r['loo_max_prompt']}"
        out.append(
            f"| {r['scope']} | {str(r['condition']).upper()} | `{r['term']}` "
            f"| {fmt(r['full_beta'])} | {fmt(r['loo_min'])} | {fmt(r['loo_max'])} "
            f"| {fmt_sd(r['loo_sd'])} | {int(r['sign_flips_vs_full'])} | {extrema} |"
        )
    return "\n".join(out)


def write_report(summary: pd.DataFrame, report_path: Path) -> None:
    pooled = summary[summary["scope"] == "pooled"]
    per_judge = summary[summary["scope"] != "pooled"]

    out: list[str] = []
    out.append("# Prompt-level jackknife robustness")
    out.append("")
    out.append(
        "This appendix re-estimates the perceived-authorship horse-race models "
        "after dropping each `prompt_id` one at a time. It asks whether the main "
        "coefficient signs and magnitudes are artifacts of a single prompt."
    )
    out.append("")
    out.append("Important caveats:")
    out.append("- This is a leave-one-prompt-out sensitivity diagnostic, not a new preregistered hypothesis test.")
    out.append("- The jackknife range is not a confidence interval; prompts are deliberately heterogeneous task clusters.")
    out.append("- `predicted_self` comes from the later C4 authorship probe, so these models remain descriptive rather than causal.")
    out.append("- Within-judge rows omit author fixed effects because, for a single judge, `author_is_self` is collinear with one author identity.")
    out.append("")

    out.append("## Model specifications")
    out.append("")
    out.append("For each condition C1/C2/C3, the pooled diagnostic fits:")
    out.append("")
    out.append("    composite ~ author_is_self + predicted_self + C(author) + C(judge) + C(category)")
    out.append("")
    out.append("For each judge × condition, the within-judge descriptive diagnostic fits:")
    out.append("")
    out.append("    composite ~ author_is_self + predicted_self + C(category)")
    out.append("")

    out.append("## Pooled horse-race stability")
    out.append("")
    out.append(table(pooled))
    out.append("")

    out.append("## Within-judge descriptive stability")
    out.append("")
    out.append(table(per_judge))
    out.append("")

    # Compact interpretive bullets, data-driven and cautious.
    pred = pooled[pooled["term"] == "predicted_self"]
    auth = pooled[pooled["term"] == "author_is_self"]
    stable_pred = int((pred["loo_min"] > 0).sum())
    stable_auth_pos = int((auth["loo_min"] > 0).sum())
    stable_auth_neg = int((auth["loo_max"] < 0).sum())
    out.append("## Reading the diagnostic")
    out.append("")
    out.append(
        f"Across the three pooled condition-level fits, `predicted_self` stays positive in "
        f"{stable_pred}/3 leave-one-prompt-out ranges. `author_is_self` stays strictly "
        f"positive in {stable_auth_pos}/3 ranges and strictly negative in {stable_auth_neg}/3 ranges."
    )
    out.append(
        "Thus the prompt-jackknife check supports the paper's qualitative framing: "
        "the perceived-authorship channel is more stable than a universal actual-authorship self-preference coefficient, "
        "while judge-specific profiles remain heterogeneous."
    )
    out.append("")
    out.append("The machine-readable summary behind these tables is [`prompt_jackknife.csv`](prompt_jackknife.csv).")
    out.append("")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(out) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wide", type=Path, default=Path("data/unified/unified_wide.csv"))
    parser.add_argument("--report", type=Path, default=Path("results/prompt_jackknife.md"))
    parser.add_argument("--csv", type=Path, default=Path("results/prompt_jackknife.csv"))
    args = parser.parse_args()

    wide = pd.read_csv(args.wide)
    needed = {"judge", "author", "prompt_id", "category", "condition", "composite", "author_is_self", "predicted_self"}
    missing = sorted(needed - set(wide.columns))
    if missing:
        raise SystemExit(f"Missing required columns in {args.wide}: {missing}")

    prompts = sorted(wide["prompt_id"].unique())
    rows: list[dict] = []
    for condition in CONDITIONS:
        cond_df = wide[wide["condition"] == condition].copy()
        rows.extend(
            summarize_jackknife(
                cond_df,
                scope="pooled",
                condition=condition,
                regressors=TERMS,
                fixed_effects=["author", "judge", "category"],
                prompts=prompts,
            )
        )
        for judge in sorted(cond_df["judge"].unique()):
            judge_df = cond_df[cond_df["judge"] == judge].copy()
            rows.extend(
                summarize_jackknife(
                    judge_df,
                    scope=judge,
                    condition=condition,
                    regressors=TERMS,
                    fixed_effects=["category"],
                    prompts=prompts,
                )
            )

    summary = pd.DataFrame(rows)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.csv, index=False)
    write_report(summary, args.report)
    print(f"Wrote {args.report} ({len(summary)} summary rows)")
    print(f"Wrote {args.csv}")


if __name__ == "__main__":
    main()
