"""Build unified long-form dataset for downstream reuse / dashboards.

Outputs:
    data/unified/unified_wide.csv  — one row per (judge, author, prompt_id, condition), 1440 rows.
    data/unified/unified_long.csv  — one row per (judge, author, prompt_id, condition, dimension), 7200 rows.

Both files include the judge's C4 recognition prediction and confidence as columns,
joined on (judge, true_author, prompt_id) so the belief channel can be analyzed alongside
the per-condition scores. Adds three helper columns:
    author_is_self        — 1 if author == judge
    predicted_self        — 1 if judge's C4 prediction == judge
    correct_recognition   — 1 if judge's C4 prediction == true author

Run with:
    python analysis/build_unified_dataset.py
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
REPO_ROOT = Path(__file__).resolve().parent.parent


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    scores = []
    recs = []
    for j in JUDGES:
        s = pd.read_csv(REPO_ROOT / f"data/judgments/{j}/long_scores.csv")
        r = pd.read_csv(REPO_ROOT / f"data/judgments/{j}/long_recognition.csv")
        scores.append(s)
        recs.append(r)
    return pd.concat(scores, ignore_index=True), pd.concat(recs, ignore_index=True)


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    S, R = load()
    if len(S) != 1440 or len(R) != 480:
        raise SystemExit(
            f"unexpected counts: scores={len(S)} (want 1440), recognition={len(R)} (want 480)"
        )
    S["composite"] = S[DIMS].mean(axis=1)
    R_keyed = R.rename(columns={"true_author": "author"})[
        ["judge", "author", "prompt_id", "predicted_author", "confidence"]
    ]
    if len(R_keyed) != 480:
        raise SystemExit(f"unexpected recognition count after rename: {len(R_keyed)}")
    wide = S.merge(R_keyed, on=["judge", "author", "prompt_id"], how="left")
    long = S.melt(
        id_vars=["judge", "author", "prompt_id", "category", "condition"],
        value_vars=DIMS,
        var_name="dimension",
        value_name="score",
    ).merge(R_keyed, on=["judge", "author", "prompt_id"], how="left")
    for df in (wide, long):
        df["author_is_self"] = (df["author"] == df["judge"]).astype(int)
        df["predicted_self"] = (df["predicted_author"] == df["judge"]).astype(int)
        df["correct_recognition"] = (df["predicted_author"] == df["author"]).astype(int)
    if wide["confidence"].isna().any() or long["confidence"].isna().any():
        raise SystemExit("merge produced NaN confidence — recognition coverage incomplete")
    return wide, long


def main() -> None:
    wide, long = build()
    out_dir = REPO_ROOT / "data/unified"
    out_dir.mkdir(exist_ok=True)
    wide.to_csv(out_dir / "unified_wide.csv", index=False)
    long.to_csv(out_dir / "unified_long.csv", index=False)
    print(f"wrote {out_dir/'unified_wide.csv'} ({len(wide)} rows)")
    print(f"wrote {out_dir/'unified_long.csv'} ({len(long)} rows)")


if __name__ == "__main__":
    main()
