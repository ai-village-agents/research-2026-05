#!/usr/bin/env python3
"""Packet order / position diagnostic for the replication-wave score sheets.

This script reconstructs prompt-group order and within-prompt response position from
public score-sheet templates. It maps response text back to source authors from the
response/paraphrase files, not from hidden packet key files.

The diagnostic is descriptive only: prompt-group position is largely confounded with
prompt identity because packets present the ten prompts in a fixed suite order.
Within-prompt response position is less confounded with prompt identity, but still
not a pre-registered randomized experiment.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
CONDS = ["C1", "C2", "C3"]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def response_author_map() -> dict[tuple[str, str], str]:
    """Return (prompt_id, sha(response_text)) -> original author."""
    out: dict[tuple[str, str], str] = {}

    for path in sorted((ROOT / "responses").glob("*/*.json")):
        author = path.parent.name
        prompt_id = path.name.removeprefix("prompt-").removesuffix(".json")
        text = json.loads(path.read_text())["response"]
        key = (prompt_id, sha(text))
        if key in out and out[key] != author:
            raise SystemExit(f"response-text collision for {prompt_id}: {out[key]} vs {author}")
        out[key] = author

    for path in sorted((ROOT / "paraphrased_responses").glob("*/*.json")):
        data = json.loads(path.read_text())
        author = data["original_author"]
        prompt_id = data["prompt_id"]
        text = data["paraphrased_response"]
        key = (prompt_id, sha(text))
        if key in out and out[key] != author:
            raise SystemExit(f"paraphrase-text collision for {prompt_id}: {out[key]} vs {author}")
        out[key] = author

    if len(out) != 80:
        raise SystemExit(f"expected 80 source texts (40 originals + 40 paraphrases), got {len(out)}")
    return out


def build_order_table(author_by_text: dict[tuple[str, str], str]) -> pd.DataFrame:
    rows = []
    for judge in JUDGES:
        for cond in CONDS:
            path = ROOT / "score_sheets" / judge / f"{cond}.json"
            data = json.loads(path.read_text())
            entries = data["entries"]
            if len(entries) != 40:
                raise SystemExit(f"{path} has {len(entries)} entries, expected 40")
            last_prompt = None
            group_position = 0
            response_position = 0
            for entry_index, entry in enumerate(entries, start=1):
                prompt_id = entry["prompt_id"]
                if prompt_id != last_prompt:
                    group_position += 1
                    response_position = 1
                    last_prompt = prompt_id
                else:
                    response_position += 1
                if response_position > 4:
                    raise SystemExit(f"{path} prompt {prompt_id} has >4 consecutive responses")
                key = (prompt_id, sha(entry["response_text"]))
                try:
                    author = author_by_text[key]
                except KeyError as exc:
                    raise SystemExit(f"could not map {path} {prompt_id} {entry['blind_id']} to author") from exc
                rows.append(
                    {
                        "judge": judge,
                        "condition": cond.lower(),
                        "prompt_id": prompt_id,
                        "author": author,
                        "entry_index": entry_index,
                        "group_position": group_position,
                        "response_position": response_position,
                        "blind_id": entry["blind_id"],
                    }
                )
            if group_position != 10:
                raise SystemExit(f"{path} has {group_position} prompt groups, expected 10")
    df = pd.DataFrame(rows)
    if len(df) != 480:
        raise SystemExit(f"expected 480 order rows, got {len(df)}")
    return df


def slope_by_position(df: pd.DataFrame, pos_col: str) -> pd.DataFrame:
    rows = []
    for (judge, condition), g in df.groupby(["judge", "condition"], sort=True):
        means = g.groupby(pos_col)["composite"].mean().sort_index()
        first = float(means.iloc[0])
        last = float(means.iloc[-1])
        rows.append(
            {
                "judge": judge,
                "condition": condition,
                "position_type": pos_col,
                "first_mean": first,
                "last_mean": last,
                "last_minus_first": last - first,
                "n": int(len(g)),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    author_by_text = response_author_map()
    order = build_order_table(author_by_text)

    scores = pd.read_csv(ROOT / "results" / "long_scores.csv")
    scores["composite"] = scores[DIMS].mean(axis=1)
    merged = scores.merge(
        order,
        on=["judge", "condition", "prompt_id", "author"],
        how="inner",
        validate="one_to_one",
    )
    if len(merged) != 480:
        raise SystemExit(f"expected 480 merged score/order rows, got {len(merged)}")

    # Descriptive means by packet positions.
    # Also compute an additive residual that removes (condition, prompt, author)
    # item quality and (condition, judge) scale/severity. This is still
    # exploratory, but it is a better smoke test than raw means because response
    # positions are not perfectly balanced by author.
    item_mean = merged.groupby(["condition", "prompt_id", "author"])["composite"].transform("mean")
    judge_cond_mean = merged.groupby(["condition", "judge"])["composite"].transform("mean")
    cond_mean = merged.groupby("condition")["composite"].transform("mean")
    merged["item_judge_adjusted_residual"] = merged["composite"] - item_mean - judge_cond_mean + cond_mean

    by_group = (
        merged.groupby(["condition", "group_position"], as_index=False)
        .agg(mean_composite=("composite", "mean"), mean_adjusted_residual=("item_judge_adjusted_residual", "mean"), n=("composite", "size"))
    )
    by_response_pos = (
        merged.groupby(["condition", "response_position"], as_index=False)
        .agg(mean_composite=("composite", "mean"), mean_adjusted_residual=("item_judge_adjusted_residual", "mean"), n=("composite", "size"))
    )
    by_response_pos_judge = (
        merged.groupby(["judge", "condition", "response_position"], as_index=False)
        .agg(mean_composite=("composite", "mean"), mean_adjusted_residual=("item_judge_adjusted_residual", "mean"), n=("composite", "size"))
    )
    author_balance = (
        order.groupby(["response_position", "author"], as_index=False)
        .size()
        .pivot(index="response_position", columns="author", values="size")
        .fillna(0)
        .astype(int)
    )
    slopes = pd.concat(
        [slope_by_position(merged, "group_position"), slope_by_position(merged, "response_position")],
        ignore_index=True,
    )

    out_dir = ROOT / "results"
    by_group.to_csv(out_dir / "packet_order_by_prompt_position.csv", index=False, float_format="%.3f")
    by_response_pos.to_csv(out_dir / "packet_order_by_response_position.csv", index=False, float_format="%.3f")
    by_response_pos_judge.to_csv(out_dir / "packet_order_by_response_position_judge.csv", index=False, float_format="%.3f")
    author_balance.to_csv(out_dir / "packet_order_author_balance.csv")
    slopes.to_csv(out_dir / "packet_order_slopes.csv", index=False, float_format="%.3f")

    response_pivot = by_response_pos.pivot(index="response_position", columns="condition", values="mean_composite")
    response_resid_pivot = by_response_pos.pivot(index="response_position", columns="condition", values="mean_adjusted_residual")
    group_pivot = by_group.pivot(index="group_position", columns="condition", values="mean_composite")
    slope_resp = slopes[slopes["position_type"] == "response_position"].copy()
    slope_group = slopes[slopes["position_type"] == "group_position"].copy()

    max_abs_resp = slope_resp.iloc[slope_resp["last_minus_first"].abs().argmax()]
    max_abs_group = slope_group.iloc[slope_group["last_minus_first"].abs().argmax()]

    lines = []
    lines.append("# Packet order / position diagnostic")
    lines.append("")
    lines.append("Generated by `analysis/packet_order_diagnostic.py`. Source: public score-sheet templates joined to `results/long_scores.csv`; response authors are recovered by exact response-text matching against committed response/paraphrase files, not by reading packet key files.")
    lines.append("")
    lines.append("**Scope/caveat.** This is descriptive only. Prompt-group position is strongly confounded with prompt identity because the 10 prompts are presented in the suite order. Within-prompt response position is a more direct check for possible order/fatigue effects, but it was not a pre-registered randomized intervention and should not be treated as causal.")
    lines.append("")
    lines.append(f"Merged rows: **{len(merged)}** = 4 judges × 3 conditions × 10 prompts × 4 responses.")
    lines.append("")
    lines.append("## Author balance by within-prompt response position")
    lines.append("")
    lines.append("Counts are across all judges × conditions × prompts. Imbalance here is why raw response-position means should not be overinterpreted.")
    lines.append("")
    lines.append(author_balance.to_markdown())
    lines.append("")
    lines.append("## Raw mean composite by within-prompt response position")
    lines.append("")
    lines.append(response_pivot.to_markdown(floatfmt=".3f"))
    lines.append("")
    lines.append("## Item- and judge-adjusted residual by within-prompt response position")
    lines.append("")
    lines.append("Residual = score − mean(condition,prompt,author) − mean(condition,judge) + mean(condition). Values near zero suggest no gross within-prompt position artifact after removing item quality and judge scale.")
    lines.append("")
    lines.append(response_resid_pivot.to_markdown(floatfmt="+.3f"))
    lines.append("")
    lines.append("## Mean composite by prompt-group position")
    lines.append("")
    lines.append(group_pivot.to_markdown(floatfmt=".3f"))
    lines.append("")
    lines.append("## First-to-last descriptive slopes")
    lines.append("")
    lines.append("Largest within-prompt response-position shift by judge/condition: "
                 f"{max_abs_resp['judge']} {max_abs_resp['condition']} "
                 f"position 4 minus position 1 = {max_abs_resp['last_minus_first']:+.3f}.")
    lines.append("")
    lines.append("Largest prompt-group shift by judge/condition: "
                 f"{max_abs_group['judge']} {max_abs_group['condition']} "
                 f"group 10 minus group 1 = {max_abs_group['last_minus_first']:+.3f} "
                 "(confounded with prompt identity).")
    lines.append("")
    lines.append(slopes.to_markdown(index=False, floatfmt=".3f"))
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("The raw within-prompt response-position means move around, but response positions are not perfectly author-balanced. The item- and judge-adjusted residual table is therefore the safer smoke test: it asks whether a row was high or low relative to the same condition/prompt/author item and the judge's condition-level scoring scale. These adjusted residuals are small compared with the multi-point author-quality and self-gap effects, so this diagnostic does not suggest a gross packet-position artifact. Prompt-group trends remain harder to interpret because early and late groups are different prompts, not repeated equivalent items.")
    lines.append("")
    (out_dir / "packet_order_diagnostic.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out_dir / 'packet_order_diagnostic.md'}")


if __name__ == "__main__":
    main()
