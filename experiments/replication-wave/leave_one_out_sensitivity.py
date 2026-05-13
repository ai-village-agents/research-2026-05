#!/usr/bin/env python3
"""Recompute leave-one-out sensitivity for replication-wave self-preference gaps."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DIMS = [
    "correctness",
    "completeness",
    "clarity",
    "creativity",
    "constraint_adherence",
]
CONDITIONS = ["c1", "c2", "c3"]


def repo_dir() -> Path:
    return Path(__file__).resolve().parent


def load_scores() -> pd.DataFrame:
    path = repo_dir() / "results" / "long_scores.csv"
    df = pd.read_csv(path)
    df["composite"] = df[DIMS].mean(axis=1)
    df["author_is_self"] = df["judge"] == df["author"]
    return df


def paired_cells(df: pd.DataFrame, condition: str) -> pd.DataFrame:
    rows = []
    sub = df[df["condition"] == condition]
    for (judge, prompt_id), cell in sub.groupby(["judge", "prompt_id"], sort=True):
        self_scores = cell[cell["author_is_self"]]["composite"]
        other_scores = cell[~cell["author_is_self"]]["composite"]
        if len(self_scores) != 1 or len(other_scores) != 3:
            raise ValueError(
                f"Expected 1 self and 3 other rows for {(condition, judge, prompt_id)}, "
                f"got {len(self_scores)} and {len(other_scores)}"
            )
        rows.append(
            {
                "condition": condition,
                "judge": judge,
                "prompt_id": prompt_id,
                "gap": float(self_scores.iloc[0] - other_scores.mean()),
            }
        )
    return pd.DataFrame(rows)


def gap(cells: pd.DataFrame) -> float:
    return float(cells["gap"].mean())


def lopo(cells: pd.DataFrame) -> pd.DataFrame:
    full = gap(cells)
    rows = []
    for prompt_id in sorted(cells["prompt_id"].unique()):
        estimate = gap(cells[cells["prompt_id"] != prompt_id])
        rows.append({"dropped_prompt": prompt_id, "gap": estimate, "delta_vs_full": estimate - full})
    return pd.DataFrame(rows)


def lojo(cells: pd.DataFrame) -> pd.DataFrame:
    full = gap(cells)
    rows = []
    for judge in sorted(cells["judge"].unique()):
        estimate = gap(cells[cells["judge"] != judge])
        rows.append({"dropped_judge": judge, "gap": estimate, "delta_vs_full": estimate - full})
    return pd.DataFrame(rows)


def fmt(x: float) -> str:
    return f"{x:+.3f}"


def main() -> None:
    df = load_scores()
    by_condition = {condition: paired_cells(df, condition) for condition in CONDITIONS}

    print("Leave-one-out sensitivity for prompt-paired self-preference gaps")
    print("Source: experiments/replication-wave/results/long_scores.csv")
    print()

    print("Headline by condition")
    for condition, cells in by_condition.items():
        full = gap(cells)
        dropped = lopo(cells)
        lo = dropped.loc[dropped["gap"].idxmin()]
        hi = dropped.loc[dropped["gap"].idxmax()]
        print(
            f"{condition.upper()}: full {fmt(full)}; "
            f"LOPO range [{fmt(lo.gap)} drop {lo.dropped_prompt}, "
            f"{fmt(hi.gap)} drop {hi.dropped_prompt}]"
        )
    print()

    print("Leave-one-judge-out")
    judges = sorted(df["judge"].unique())
    print("condition," + ",".join(f"drop_{j}" for j in judges))
    for condition, cells in by_condition.items():
        estimates = lojo(cells).set_index("dropped_judge")["gap"]
        print(condition.upper() + "," + ",".join(fmt(estimates[j]) for j in judges))
    print()

    print("All C1 leave-one-prompt-out rows")
    for row in lopo(by_condition["c1"]).itertuples(index=False):
        print(f"{row.dropped_prompt},{fmt(row.gap)},{fmt(row.delta_vs_full)}")


if __name__ == "__main__":
    main()
