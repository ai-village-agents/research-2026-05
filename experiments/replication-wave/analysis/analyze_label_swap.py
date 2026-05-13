#!/usr/bin/env python3
"""Analyze the D408 label-swap randomized experiment.

The experiment shows each judge every C1 response four times, once with each
visible author label. This script deliberately avoids statsmodels so it runs in
our village environment. It loads local answer keys (gitignored until scoring is
complete), joins them to committed scored sessions, writes a long CSV, and
reports within-response paired label effects.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCORE_SHEETS_DIR = ROOT / "score_sheets" / "label_swap"
KEYS_DIR = ROOT / "data" / "label_swap_keys"
RESULTS_DIR = ROOT / "results"

MODELS = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
SUBSCALES = [
    "correctness",
    "completeness",
    "clarity",
    "creativity",
    "constraint_adherence",
]


def _read_json(path: Path):
    return json.loads(path.read_text())


def _as_score(value, *, path: Path, blind_id: str, subscale: str) -> float:
    if value == "" or value is None:
        raise ValueError(f"missing {subscale} in {path} blind_id={blind_id}")
    try:
        score = float(value)
    except Exception as exc:  # pragma: no cover - defensive message
        raise ValueError(f"non-numeric {subscale}={value!r} in {path} blind_id={blind_id}") from exc
    if not 1 <= score <= 10:
        raise ValueError(f"out-of-range {subscale}={score} in {path} blind_id={blind_id}")
    return score


def load_keys() -> dict[tuple[str, str], dict]:
    """Load keys as (judge, session_blind_id) -> key row.

    Current randomization is identical across judges, but judge-specific keys are
    safer if a later rerun uses judge-specific remapping.
    """
    keys: dict[tuple[str, str], dict] = {}
    if not KEYS_DIR.exists():
        return keys
    for judge_dir in sorted(p for p in KEYS_DIR.iterdir() if p.is_dir()):
        judge = judge_dir.name
        for key_file in sorted(judge_dir.glob("session_*_key.json")):
            for item in _read_json(key_file):
                item = dict(item)
                item["key_file"] = str(key_file.relative_to(ROOT))
                keys[(judge, item["session_blind_id"])] = item
    return keys


def load_data() -> pd.DataFrame:
    keys = load_keys()
    rows = []
    if not SCORE_SHEETS_DIR.exists():
        return pd.DataFrame()

    for judge_dir in sorted(p for p in SCORE_SHEETS_DIR.iterdir() if p.is_dir()):
        judge = judge_dir.name
        for score_file in sorted(judge_dir.glob("session_*_scored.json")):
            data = _read_json(score_file)
            session = data.get("session") or score_file.stem.replace("_scored", "")
            for entry in data.get("entries", []):
                blind_id = entry["blind_id"]
                key = keys.get((judge, blind_id))
                if key is None:
                    raise KeyError(
                        f"No label-swap key for judge={judge} blind_id={blind_id}; "
                        "regenerate local keys with run_label_swap.py using the same salt."
                    )
                scores = {
                    sub: _as_score(entry.get(sub), path=score_file, blind_id=blind_id, subscale=sub)
                    for sub in SUBSCALES
                }
                composite = float(np.mean([scores[sub] for sub in SUBSCALES]))
                actual_author = key["actual_author"]
                displayed_label = entry["displayed_label"]
                if displayed_label != key["displayed_label"]:
                    raise ValueError(
                        f"Displayed label mismatch for {score_file} blind_id={blind_id}: "
                        f"sheet={displayed_label} key={key['displayed_label']}"
                    )
                rows.append(
                    {
                        "judge": judge,
                        "session": session,
                        "prompt_id": entry["prompt_id"],
                        "blind_id": blind_id,
                        "original_blind_id": key["original_blind_id"],
                        "actual_author": actual_author,
                        "displayed_label": displayed_label,
                        "is_true_self": judge == actual_author,
                        "is_displayed_self": judge == displayed_label,
                        "is_displayed_kimi": displayed_label == "kimi-k2.6",
                        "composite_score": composite,
                        **scores,
                    }
                )
    return pd.DataFrame(rows)


def mean_ci(gaps: Iterable[float], *, seed: int = 408, b: int = 5000) -> tuple[float, float, float, int, float]:
    arr = np.array(list(gaps), dtype=float)
    arr = arr[np.isfinite(arr)]
    n = int(arr.size)
    if n == 0:
        return math.nan, math.nan, math.nan, 0, math.nan
    mean = float(arr.mean())
    sd = float(arr.std(ddof=1)) if n > 1 else 0.0
    if n == 1:
        return mean, mean, mean, n, sd
    rng = np.random.default_rng(seed)
    boot = np.empty(b, dtype=float)
    for i in range(b):
        boot[i] = rng.choice(arr, size=n, replace=True).mean()
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return mean, float(lo), float(hi), n, sd


def paired_label_gaps(df: pd.DataFrame) -> pd.DataFrame:
    """Compute within-response paired estimands.

    Each row summarizes one judge × original response when all four displayed
    labels are present.
    """
    rows = []
    for (judge, original_blind_id), g in df.groupby(["judge", "original_blind_id"], sort=True):
        by_label = g.set_index("displayed_label")["composite_score"]
        if set(MODELS) - set(by_label.index):
            continue
        self_label = judge
        nonself = [m for m in MODELS if m != self_label]
        nonkimi = [m for m in MODELS if m != "kimi-k2.6"]
        rows.append(
            {
                "judge": judge,
                "original_blind_id": original_blind_id,
                "prompt_id": g["prompt_id"].iloc[0],
                "actual_author": g["actual_author"].iloc[0],
                "self_label_minus_other_labels": float(by_label[self_label] - by_label[nonself].mean()),
                "kimi_label_minus_non_kimi_labels": float(by_label["kimi-k2.6"] - by_label[nonkimi].mean()),
                "displayed_self_score": float(by_label[self_label]),
                "displayed_kimi_score": float(by_label["kimi-k2.6"]),
                "all_label_mean": float(by_label.mean()),
            }
        )
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame, gaps: pd.DataFrame) -> pd.DataFrame:
    rows = []

    def add(scope: str, judge: str, estimand: str, values: Iterable[float]):
        mean, lo, hi, n, sd = mean_ci(values)
        rows.append(
            {
                "scope": scope,
                "judge": judge,
                "estimand": estimand,
                "n_paired_units": n,
                "mean": mean,
                "boot_ci_low": lo,
                "boot_ci_high": hi,
                "sd": sd,
            }
        )

    if not gaps.empty:
        add("all_judges", "ALL", "displayed_self_minus_other_labels", gaps["self_label_minus_other_labels"])
        add("all_judges", "ALL", "displayed_kimi_minus_non_kimi_labels", gaps["kimi_label_minus_non_kimi_labels"])
        nk = gaps[gaps["judge"] != "kimi-k2.6"]
        add("non_kimi_judges", "ALL_EXCEPT_KIMI", "displayed_kimi_minus_non_kimi_labels", nk["kimi_label_minus_non_kimi_labels"])
        for judge, g in gaps.groupby("judge", sort=True):
            add("judge", judge, "displayed_self_minus_other_labels", g["self_label_minus_other_labels"])
            add("judge", judge, "displayed_kimi_minus_non_kimi_labels", g["kimi_label_minus_non_kimi_labels"])

    # Raw displayed-label means are useful for sanity checks but are not the
    # paired estimand because actual response quality differs across rows.
    for (judge, label), g in df.groupby(["judge", "displayed_label"], sort=True):
        rows.append(
            {
                "scope": "raw_mean_by_judge_label",
                "judge": judge,
                "estimand": f"mean_score_displayed_{label}",
                "n_paired_units": int(len(g)),
                "mean": float(g["composite_score"].mean()),
                "boot_ci_low": math.nan,
                "boot_ci_high": math.nan,
                "sd": float(g["composite_score"].std(ddof=1)) if len(g) > 1 else 0.0,
            }
        )
    return pd.DataFrame(rows)


def write_markdown(df: pd.DataFrame, gaps: pd.DataFrame, summary: pd.DataFrame) -> None:
    out = RESULTS_DIR / "label_swap_analysis.md"
    RESULTS_DIR.mkdir(exist_ok=True)
    lines = [
        "# D408 label-swap analysis",
        "",
        "This file is generated by `experiments/replication-wave/analysis/analyze_label_swap.py`.",
        "It uses local gitignored answer keys; do not publish keys until scoring is complete.",
        "",
        "> **Backend caveat (Day 407 closeout):** the currently committed Gemini/GPT label-swap score sheets were produced through the `eval_all_sessions.py` / `run_my_label_swap.sh` path, which was later found to call `codex exec` under an OpenAI backend. Treat the estimates below as backend-contaminated codex/GPT-backend robustness output, not as native Gemini 3.1 Pro or GPT-5.5 judgments. Native in-context rescoring is required before interpreting this as a causal multi-judge RCT.",
        "",
        f"Loaded scored rows: **{len(df)}**.",
    ]
    if len(df):
        lines += [
            "",
            "## Coverage",
            "",
            df.groupby("judge").size().rename("scored_rows").to_frame().to_markdown(),
            "",
            "## Primary paired estimands",
            "",
        ]
        primary = summary[summary["scope"].isin(["all_judges", "non_kimi_judges", "judge"])]
        lines.append(primary.to_markdown(index=False, floatfmt=".4f"))
        lines += [
            "",
            "Interpretation: `displayed_self_minus_other_labels` is computed within each judge × original response as the score under that judge's own displayed label minus the mean score under the other three labels. `displayed_kimi_minus_non_kimi_labels` is the score under a Kimi displayed label minus the mean under the three non-Kimi labels.",
            "",
            "## Raw displayed-label means (sanity check, not paired causal estimands)",
            "",
        ]
        raw = summary[summary["scope"] == "raw_mean_by_judge_label"]
        lines.append(raw.to_markdown(index=False, floatfmt=".4f"))
    out.write_text("\n".join(lines) + "\n")


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    df = load_data()
    long_path = RESULTS_DIR / "label_swap_long.csv"
    gaps_path = RESULTS_DIR / "label_swap_paired_gaps.csv"
    summary_path = RESULTS_DIR / "label_swap_summary.csv"
    df.to_csv(long_path, index=False)
    gaps = paired_label_gaps(df) if not df.empty else pd.DataFrame()
    gaps.to_csv(gaps_path, index=False)
    summary = summarize(df, gaps) if not df.empty else pd.DataFrame()
    summary.to_csv(summary_path, index=False)
    write_markdown(df, gaps, summary)
    print(f"Loaded {len(df)} scored label-swap rows")
    print(f"Wrote {long_path.relative_to(ROOT)}")
    print(f"Wrote {gaps_path.relative_to(ROOT)}")
    print(f"Wrote {summary_path.relative_to(ROOT)}")
    print(f"Wrote {(RESULTS_DIR / 'label_swap_analysis.md').relative_to(ROOT)}")
    if not summary.empty:
        primary = summary[summary["scope"].isin(["all_judges", "non_kimi_judges", "judge"])]
        print(primary.to_string(index=False))


if __name__ == "__main__":
    main()
