"""Leave-one-prompt-out (LOPO) jackknife robustness check for master claims.

For each of the master inferential claims, drop one prompt at a time (10 total)
and recompute the point estimate. This isolates prompt-level fragility:
- LOPO range (max - min across 10 jackknife estimates)
- Max signed swing from full-sample estimate
- Worst-case prompt: which single prompt, if removed, moves the estimate furthest
- Sign-flip check: does any single prompt's removal flip the sign of the effect?

Complements the multiplicity correction (which guards against false positives across
the 16-claim family) with a robustness check that guards against single-prompt artifacts.
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path("/tmp/research-2026-05/experiments/replication-wave")
RESULTS = ROOT / "results"

long_scores = pd.read_csv(RESULTS / "long_scores.csv")
dim_cols = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
long_scores["composite"] = long_scores[dim_cols].mean(axis=1)
c1 = long_scores[long_scores["condition"] == "c1"].copy()
paired = pd.read_csv(RESULTS / "paired_label_swap.csv")
fr = pd.read_csv(RESULTS / "floor_raising_test.csv")

PROMPTS = sorted(c1["prompt_id"].unique().tolist())
assert len(PROMPTS) == 10, len(PROMPTS)


def c1_gap(judges_kept, drop_prompt=None):
    sub = c1[c1["judge"].isin(judges_kept)].copy()
    if drop_prompt is not None:
        sub = sub[sub["prompt_id"] != drop_prompt]
    sub["is_self"] = sub["judge"] == sub["author"]
    gaps = []
    for (j, p), g in sub.groupby(["judge", "prompt_id"]):
        if g["is_self"].any() and (~g["is_self"]).any():
            gaps.append(g[g["is_self"]]["composite"].mean() - g[~g["is_self"]]["composite"].mean())
    return float(np.mean(gaps)) if gaps else float("nan")


def causal_self_effect(judge, drop_prompt=None):
    """Mean over response_hash of (self-labeled composite - other-labeled composite) for this judge."""
    sub = paired[paired["judge"] == judge].copy()
    if drop_prompt is not None:
        sub = sub[sub["prompt_id"] != drop_prompt]
    if len(sub) == 0:
        return float("nan")
    # For each response_hash, find the row where displayed_label == judge (self) vs != judge (other mean)
    # judge field looks like "claude-opus-4.7", displayed_label looks like "claude" (short)
    short = {"claude-opus-4.7": "claude-opus-4.7", "gemini-3.1-pro": "gemini-3.1-pro",
             "gpt-5.5": "gpt-5.5", "kimi-k2.6": "kimi-k2.6"}[judge]
    deltas = []
    for h, g in sub.groupby("response_hash"):
        self_rows = g[g["displayed_label"] == short]
        other_rows = g[g["displayed_label"] != short]
        if len(self_rows) > 0 and len(other_rows) > 0:
            deltas.append(self_rows["composite"].mean() - other_rows["composite"].mean())
    return float(np.mean(deltas)) if deltas else float("nan")


def causal_label_contrast(judge, displayed_label_short, drop_prompt=None):
    """Per-response residual after subtracting response mean across displayed labels.
    Returns mean over responses of (composite under this label - composite under other labels)."""
    sub = paired[paired["judge"] == judge].copy()
    if drop_prompt is not None:
        sub = sub[sub["prompt_id"] != drop_prompt]
    deltas = []
    for h, g in sub.groupby("response_hash"):
        target = g[g["displayed_label"] == displayed_label_short]
        other = g[g["displayed_label"] != displayed_label_short]
        if len(target) > 0 and len(other) > 0:
            deltas.append(target["composite"].mean() - other["composite"].mean())
    return float(np.mean(deltas)) if deltas else float("nan")


def floor_spearman(judge_short, drop_prompt=None):
    sub = fr[fr["judge"] == judge_short].copy()
    if drop_prompt is not None:
        sub = sub[sub["prompt_id"] != drop_prompt]
    if len(sub) < 4:
        return float("nan")
    return float(sub[["other_composite", "delta"]].corr(method="spearman").iloc[0, 1])


# -------- DEFINE CLAIMS --------
def define_claims():
    claims = []
    for judge, label in [("claude-opus-4.7", "Claude 4J Observational Baseline (C1)"),
                         ("gemini-3.1-pro", "Gemini 4J Observational Baseline (C1)"),
                         ("gpt-5.5", "GPT 4J Observational Baseline (C1)"),
                         ("kimi-k2.6", "Kimi 4J Observational Baseline (C1)")]:
        claims.append((label, "Observational (C1)",
                       lambda dp, j=judge: c1_gap([j], drop_prompt=dp)))
    claims.append(("Pooled 4J Observational Baseline (C1)", "Observational (C1)",
                   lambda dp: c1_gap(["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"], drop_prompt=dp)))
    claims.append(("Pooled 3J Observational Baseline (C1)", "Observational (C1)",
                   lambda dp: c1_gap(["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5"], drop_prompt=dp)))
    for judge, short, label in [("claude-opus-4.7", "claude-opus-4.7", "Causal Label-Swap: Claude Self-Effect"),
                                ("gemini-3.1-pro", "gemini-3.1-pro", "Causal Label-Swap: Gemini Self-Effect"),
                                ("gpt-5.5", "gpt-5.5", "Causal Label-Swap: GPT Self-Effect"),
                                ("kimi-k2.6", "kimi-k2.6", "Causal Label-Swap: Kimi Self-Effect")]:
        claims.append((label, "Causal RCT",
                       lambda dp, j=judge, s=short: causal_label_contrast(j, s, drop_prompt=dp)))
    claims.append(("Causal Label-Swap: Gemini anti-Kimi", "Causal RCT",
                   lambda dp: causal_label_contrast("gemini-3.1-pro", "kimi-k2.6", drop_prompt=dp)))
    claims.append(("Causal Label-Swap: Kimi pro-Claude", "Causal RCT",
                   lambda dp: causal_label_contrast("kimi-k2.6", "claude-opus-4.7", drop_prompt=dp)))
    claims.append(("Causal Label-Swap: Claude pro-Claude", "Causal RCT",
                   lambda dp: causal_label_contrast("claude-opus-4.7", "claude-opus-4.7", drop_prompt=dp)))
    claims.append(("Floor-Raiser Mechanism (Gemini)", "Mechanism",
                   lambda dp: floor_spearman("gemini", drop_prompt=dp)))
    return claims


claims = define_claims()
rows = []
for name, family, fn in claims:
    full_est = fn(None)
    lopo_ests = []
    for p in PROMPTS:
        lopo_ests.append(fn(p))
    arr = np.array(lopo_ests, dtype=float)
    lopo_min = float(np.nanmin(arr))
    lopo_max = float(np.nanmax(arr))
    lopo_range = lopo_max - lopo_min
    deltas = arr - full_est
    max_swing_idx = int(np.nanargmax(np.abs(deltas)))
    max_swing_prompt = PROMPTS[max_swing_idx]
    max_swing = float(deltas[max_swing_idx])
    sign_full = np.sign(full_est) if full_est != 0 else 0
    sign_flip = bool(np.any(np.sign(arr[~np.isnan(arr)]) * sign_full < 0)) if sign_full != 0 else False
    rows.append(dict(claim=name, family=family, full_est=full_est,
                     lopo_min=lopo_min, lopo_max=lopo_max, lopo_range=lopo_range,
                     max_swing_prompt=max_swing_prompt, max_swing=max_swing,
                     sign_flip=sign_flip))

df = pd.DataFrame(rows)
out_csv = RESULTS / "master_claims_lopo_robustness.csv"
df.to_csv(out_csv, index=False)
print(df.to_string(index=False))
print("\nWrote", out_csv)
