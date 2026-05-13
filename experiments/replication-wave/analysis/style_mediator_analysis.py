#!/usr/bin/env python3
"""Preliminary style-mediator check for replication-wave predicted-label effects.

This dependency-light script reproduces the 4-judge C1 preview without requiring
statsmodels. It asks whether simple surface features of the original response
(length, sentence length, lexical diversity, list density) explain away the
predicted-author label coefficients in a fixed-effect OLS model.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
MODELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
STYLE_FEATURES = ["sentence_length", "lexical_diversity", "list_density", "char_length"]


def extract_features(text: str) -> dict[str, float]:
    if not isinstance(text, str) or not text.strip():
        return {name: 0.0 for name in STYLE_FEATURES}
    words = text.split()
    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    list_items = len(re.findall(r"^[\s]*[-*•]\s|^[\s]*\d+\.\s", text, flags=re.MULTILINE))
    n_words = len(words)
    return {
        "sentence_length": (n_words / len(sentences)) if sentences else 0.0,
        "lexical_diversity": (len({w.lower() for w in words}) / n_words) if n_words else 0.0,
        "list_density": (list_items / n_words) if n_words else 0.0,
        "char_length": float(len(text)),
    }


def load_data() -> pd.DataFrame:
    scores = pd.read_csv(ROOT / "results" / "long_scores.csv")
    recog = pd.read_csv(ROOT / "results" / "long_recognition.csv").rename(columns={"true_author": "author"})
    c1 = scores[scores["condition"].str.lower() == "c1"].copy()
    c1["mean5"] = c1[DIMS].mean(axis=1)
    merged = c1.merge(recog, on=["judge", "prompt_id", "author"], how="inner", validate="one_to_one")
    merged["actual_self"] = (merged["judge"] == merged["author"]).astype(int)
    merged["predicted_self"] = (merged["judge"] == merged["predicted_author"]).astype(int)

    responses = []
    for author_dir in sorted((ROOT / "responses").iterdir()):
        if not author_dir.is_dir():
            continue
        author = author_dir.name
        for path in sorted(author_dir.glob("*.json")):
            data = json.loads(path.read_text())
            prompt_id = path.stem.replace("prompt-", "", 1)
            responses.append({"author": author, "prompt_id": prompt_id, "response_text": data.get("response", "")})
    resp = pd.DataFrame(responses)
    out = merged.merge(resp, on=["author", "prompt_id"], how="inner", validate="many_to_one")

    features = out["response_text"].apply(extract_features).apply(pd.Series)
    out = pd.concat([out, features], axis=1)
    for col in STYLE_FEATURES:
        sd = float(out[col].std(ddof=1))
        out[col] = (out[col] - float(out[col].mean())) / sd if sd else 0.0
    return out


def fit_ols(df: pd.DataFrame, continuous_terms: list[str], categorical_terms: list[str]) -> tuple[pd.Series, float]:
    parts = [pd.Series(1.0, index=df.index, name="Intercept")]
    parts.extend(df[term].astype(float).rename(term) for term in continuous_terms)
    for term in categorical_terms:
        parts.append(pd.get_dummies(df[term], prefix=f"C({term})", drop_first=True, dtype=float))
    x = pd.concat(parts, axis=1)
    y = df["mean5"].astype(float).to_numpy()
    beta, *_ = np.linalg.lstsq(x.to_numpy(dtype=float), y, rcond=None)
    pred = x.to_numpy(dtype=float) @ beta
    ss_res = float(np.sum((y - pred) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot else float("nan")
    return pd.Series(beta, index=x.columns), r2


def bootstrap_terms(
    df: pd.DataFrame,
    continuous_terms: list[str],
    categorical_terms: list[str],
    terms: list[str],
    b: int = 2000,
    seed: int = 20260513,
) -> pd.DataFrame:
    prompts = sorted(df["prompt_id"].unique())
    rng = np.random.default_rng(seed)
    draws = {term: [] for term in terms}
    for _ in range(b):
        sampled = rng.choice(prompts, size=len(prompts), replace=True)
        boot = pd.concat([df[df["prompt_id"] == prompt] for prompt in sampled], ignore_index=True)
        coef, _ = fit_ols(boot, continuous_terms, categorical_terms)
        for term in terms:
            draws[term].append(float(coef.get(term, np.nan)))
    rows = []
    for term in terms:
        arr = np.array(draws[term], dtype=float)
        arr = arr[np.isfinite(arr)]
        rows.append(
            {
                "term": term,
                "beta": np.nan,
                "boot_ci_low": float(np.percentile(arr, 2.5)),
                "boot_ci_high": float(np.percentile(arr, 97.5)),
                "bootstrap_n": int(len(arr)),
            }
        )
    return pd.DataFrame(rows)


def label_terms() -> list[str]:
    return [f"predicted_author={m}" for m in MODELS if m != "kimi-k2.6"] + [
        f"actual_author={m}" for m in MODELS if m != "kimi-k2.6"
    ]


def add_label_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for model in MODELS:
        if model == "kimi-k2.6":
            continue
        out[f"predicted_author={model}"] = (out["predicted_author"] == model).astype(int)
        out[f"actual_author={model}"] = (out["author"] == model).astype(int)
    return out


def fmt(x: float) -> str:
    return f"{0.0 if abs(float(x)) < 5e-13 else float(x):+.3f}"


def main() -> None:
    df = add_label_indicators(load_data())
    terms = label_terms()

    base_coef, base_r2 = fit_ols(df, ["actual_self", "predicted_self"], ["judge", "prompt_id"])
    label_coef, label_r2 = fit_ols(df, terms, ["judge", "prompt_id"])
    style_coef, style_r2 = fit_ols(df, terms + STYLE_FEATURES, ["judge", "prompt_id"])

    rows = []
    for term in terms:
        rows.append(
            {
                "term": term,
                "without_style_beta": float(label_coef[term]),
                "with_style_beta": float(style_coef[term]),
                "delta_after_style": float(style_coef[term] - label_coef[term]),
            }
        )
    summary = pd.DataFrame(rows)

    ci = bootstrap_terms(df, terms + STYLE_FEATURES, ["judge", "prompt_id"], terms, seed=20260514)
    ci = ci.drop(columns=["beta"]).rename(columns={"boot_ci_low": "with_style_boot_ci_low", "boot_ci_high": "with_style_boot_ci_high"})
    summary = summary.merge(ci, on="term")

    out_csv = ROOT / "results" / "style_mediator_coefficients.csv"
    summary.to_csv(out_csv, index=False)

    lines = [
        "# Preliminary style-mediator analysis for predicted-label effect",
        "",
        "Generated by `experiments/replication-wave/analysis/style_mediator_analysis.py` using NumPy OLS (no statsmodels dependency).",
        "",
        f"Data: 4-judge C1 merged score/recognition rows, N={len(df)}.",
        "",
        "Surface features standardized before modeling: sentence length, lexical diversity, list density, character length.",
        "",
        "## Model diagnostics",
        "",
        "| model | R² |",
        "|---|---:|",
        f"| actual_self + predicted_self + judge FE + prompt FE | {base_r2:.3f} |",
        f"| predicted_author + actual_author + judge FE + prompt FE | {label_r2:.3f} |",
        f"| label model + surface style features | {style_r2:.3f} |",
        "",
        "## Label coefficients before/after surface-style controls",
        "",
        "Reference for predicted and actual author indicators is `kimi-k2.6`. Bootstrap CIs resample prompt clusters for the style-controlled model.",
        "",
        "| term | without style β | with style β | Δ after style | with-style boot CI |",
        "|---|---:|---:|---:|---:|",
    ]
    for _, r in summary.iterrows():
        lines.append(
            f"| {r['term']} | {fmt(r['without_style_beta'])} | {fmt(r['with_style_beta'])} | "
            f"{fmt(r['delta_after_style'])} | [{fmt(r['with_style_boot_ci_low'])}, {fmt(r['with_style_boot_ci_high'])}] |"
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "Adding these simple surface-style controls does not explain away the predicted-author label contrast. Predicted Claude/GPT labels remain roughly two rubric points above predicted Kimi, consistent with either deeper quality/style signals used during attribution or a non-causal label-correlated heuristic. A randomized label-swap experiment is still required for causal interpretation.",
            "",
        ]
    )
    out_md = ROOT / "results" / "style_mediator_preview.md"
    out_md.write_text("\n".join(lines))

    print(f"wrote {out_csv}")
    print(f"wrote {out_md}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
