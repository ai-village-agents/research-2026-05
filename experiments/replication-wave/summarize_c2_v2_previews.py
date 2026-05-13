#!/usr/bin/env python3
"""Summarize preliminary C2-v2 preview rescoring sheets.

This script does not modify canonical score data. It reads the canonical v1 C2
rows in results/long_scores.csv, reads every shared C2-v2 preview sheet under
``data/c2_v2_scores/*/C2_v2.json``, and computes the self-preference gap that
would result from replacing only the rows present in each preview sheet.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
DEFAULT_ROOT = Path(__file__).resolve().parent


def composite(row: pd.Series) -> float:
    return float(row[DIMS].mean())


def entry_composite(entry: dict[str, Any]) -> float:
    missing = [dim for dim in DIMS if dim not in entry]
    if missing:
        raise ValueError(f"v2 entry {entry.get('blind_id')} is missing score fields: {missing}")
    return sum(float(entry[dim]) for dim in DIMS) / len(DIMS)


def load_key_map(root: Path, judge: str) -> dict[str, dict[str, Any]]:
    key_path = root / "evaluation_packets" / "keys" / judge / "C2_key.json"
    if not key_path.exists():
        raise FileNotFoundError(f"Missing C2 key for {judge}: {key_path}")
    entries = json.loads(key_path.read_text())
    if not isinstance(entries, list):
        raise ValueError(f"Expected list-shaped key file for {judge}: {key_path}")
    out: dict[str, dict[str, Any]] = {}
    for item in entries:
        blind_id = item.get("blind_id")
        if not blind_id:
            raise ValueError(f"Key entry missing blind_id in {key_path}: {item}")
        if blind_id in out:
            raise ValueError(f"Duplicate blind_id {blind_id} in {key_path}")
        out[blind_id] = item
    return out


def self_gap(df: pd.DataFrame) -> float:
    self_scores = df.loc[df["judge"] == df["author"], "composite"]
    other_scores = df.loc[df["judge"] != df["author"], "composite"]
    if self_scores.empty or other_scores.empty:
        raise ValueError("Cannot compute self gap without both self and other rows")
    return float(self_scores.mean() - other_scores.mean())


def summarize(root: Path) -> pd.DataFrame:
    long_path = root / "results" / "long_scores.csv"
    long = pd.read_csv(long_path)
    c2 = long[long["condition"].str.lower() == "c2"].copy()
    if c2.empty:
        raise ValueError(f"No C2 rows found in {long_path}")
    c2["composite"] = c2[DIMS].mean(axis=1)

    rows: list[dict[str, Any]] = []
    sheet_paths = sorted((root / "data" / "c2_v2_scores").glob("*/C2_v2.json"))
    if not sheet_paths:
        raise ValueError("No C2-v2 preview sheets found")

    for sheet_path in sheet_paths:
        data = json.loads(sheet_path.read_text())
        judge = data.get("judge") or sheet_path.parent.name
        entries = data.get("entries")
        if not isinstance(entries, list):
            raise ValueError(f"Expected entries list in {sheet_path}")

        v1 = c2[c2["judge"] == judge].copy()
        if v1.empty:
            raise ValueError(f"No canonical v1 C2 rows found for judge {judge}")
        preview = v1.copy()
        key_map = load_key_map(root, judge)
        deltas: list[float] = []

        for entry in entries:
            blind_id = entry.get("blind_id")
            prompt_id = entry.get("prompt_id")
            if not blind_id or not prompt_id:
                raise ValueError(f"v2 entry missing blind_id or prompt_id in {sheet_path}: {entry}")
            key = key_map.get(blind_id)
            author = entry.get("author_hidden") or entry.get("author") or (key or {}).get("author")
            if not author:
                raise ValueError(
                    f"Cannot determine author for judge={judge}, blind_id={blind_id}; "
                    "provide author_hidden/author or a matching C2 key entry"
                )
            if key is not None:
                if key.get("prompt_id") != prompt_id:
                    raise ValueError(
                        f"Prompt mismatch for {judge} {blind_id}: sheet {prompt_id}, key {key.get('prompt_id')}"
                    )
                if author != key.get("author"):
                    raise ValueError(
                        f"Author mismatch for {judge} {blind_id}: sheet/key {author} vs {key.get('author')}"
                    )
                if key.get("paraphraser") != "kimi-k2.6":
                    # Full-sheet previews may include non-Kimi rows in the future; for now this script
                    # summarizes whatever the sheet supplies, but the current v2 issue is Kimi slots.
                    pass

            mask = (preview["author"] == author) & (preview["prompt_id"] == prompt_id)
            matches = int(mask.sum())
            if matches != 1:
                raise ValueError(
                    f"Expected exactly one v1 C2 row for judge={judge}, author={author}, "
                    f"prompt_id={prompt_id}, blind_id={blind_id}; found {matches}"
                )

            old_comp = float(preview.loc[mask, "composite"].iloc[0])
            new_comp = entry_composite(entry)
            for dim in DIMS:
                preview.loc[mask, dim] = float(entry[dim])
            preview.loc[mask, "composite"] = new_comp
            deltas.append(new_comp - old_comp)

        v1_gap = self_gap(v1)
        v2_gap = self_gap(preview)
        rows.append(
            {
                "judge": judge,
                "v2_entries": len(entries),
                "mapped_entries": len(deltas),
                "v1_gap": v1_gap,
                "v2_preview_gap": v2_gap,
                "delta": v2_gap - v1_gap,
                "mean_replaced_composite_delta": sum(deltas) / len(deltas),
                "min_replaced_composite_delta": min(deltas),
                "max_replaced_composite_delta": max(deltas),
            }
        )

    return pd.DataFrame(rows).sort_values("judge")


def write_markdown(df: pd.DataFrame, path: Path) -> None:
    display = df.copy()
    for col in [
        "v1_gap",
        "v2_preview_gap",
        "delta",
        "mean_replaced_composite_delta",
        "min_replaced_composite_delta",
        "max_replaced_composite_delta",
    ]:
        display[col] = display[col].map(lambda x: f"{0.0 if abs(x) < 5e-13 else x:+.3f}")

    lines = [
        "# C2-v2 cross-judge preliminary preview",
        "",
        "This file is generated by `experiments/replication-wave/summarize_c2_v2_previews.py`.",
        "",
        "These are **direct preliminary C2-v2 previews**, not replacements for the canonical v1 C2 rows in `results/long_scores.csv`. For each judge, the script starts from that judge's canonical v1 C2 rows and replaces only the entries present in the shared `data/c2_v2_scores/*/C2_v2.json` preview sheet.",
        "",
        "| judge | v2 entries | mapped | v1 gap | v2 preview gap | Δ gap | mean replaced Δ | min replaced Δ | max replaced Δ |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in display.iterrows():
        lines.append(
            f"| {row['judge']} | {row['v2_entries']} | {row['mapped_entries']} | "
            f"{row['v1_gap']} | {row['v2_preview_gap']} | {row['delta']} | "
            f"{row['mean_replaced_composite_delta']} | {row['min_replaced_composite_delta']} | "
            f"{row['max_replaced_composite_delta']} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "- Claude Opus 4.7 and GPT-5.5 currently provide 10-entry previews for the Kimi-paraphraser slots affected by the v1/v2 corpus change.",
            "- Gemini 3.1 Pro currently provides a 40-entry direct/full preview sheet; the resulting self-gap is unchanged relative to v1 in this summary.",
            "- A coordinated D408 packet-regenerated rerun is still needed before any v2 rows should replace or supplement canonical C2 analyses.",
            "",
        ]
    )
    path.write_text("\n".join(lines))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="replication-wave directory")
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=DEFAULT_ROOT / "results" / "C2_v2_cross_judge_preview.csv",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=DEFAULT_ROOT / "results" / "C2_v2_cross_judge_preview.md",
    )
    args = parser.parse_args()

    df = summarize(args.root)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.output_csv, index=False)
    write_markdown(df, args.output_md)
    print(f"wrote {args.output_csv}")
    print(f"wrote {args.output_md}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
