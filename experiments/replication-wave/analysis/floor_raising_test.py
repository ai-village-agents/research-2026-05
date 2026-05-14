#!/usr/bin/env python3
"""Floor-raising test: does self-label uplift Δ correlate negatively with
the response's non-self (baseline) composite?

Hypothesis (originally suggested by Gemini's per-actual-author pattern in
paired_self_response_level.md, where the largest self-uplift fell on the
lowest-baseline author, Kimi): the displayed-author SELF label functions
asymmetrically as a 'floor-raiser' — it adds the most uplift to responses
that the judge would otherwise rate lowest, and little or nothing to
already-strong responses.

For each native judge, for each of the ~20 responses shown once under the
judge's own label and once under a non-self label, we compute:
- delta = composite(self-displayed) − composite(non-self-displayed)
- baseline = composite(non-self-displayed)

We then report Pearson r and Spearman ρ between delta and baseline, and the
mean baseline among uplifted (Δ>0) vs non-uplifted (Δ≤0) responses, plus a
bootstrap 95% CI on the Spearman ρ (B=2000) for each judge with non-zero Δ.

Outputs:
- results/floor_raising_test.csv: per-response (judge, pid, author, delta, baseline)
- results/floor_raising_test.md: summary table + interpretation
"""
from __future__ import annotations
import json, hashlib, csv, pathlib
import numpy as np
from collections import defaultdict

REPO = pathlib.Path(__file__).resolve().parents[3]
RW = REPO / "experiments" / "replication-wave"
SCORES = RW / "score_sheets" / "label_swap"
RESP = RW / "responses"
PACKETS = RW / "data" / "label_swap_packets"
OUT = RW / "results"
OUT.mkdir(parents=True, exist_ok=True)

JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
JUDGE_SHORT = {"claude-opus-4.7": "claude", "gemini-3.1-pro": "gemini", "gpt-5.5": "gpt", "kimi-k2.6": "kimi"}
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
RNG = np.random.default_rng(0xF1007)
B = 2000

def md5_10(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:10]

# text MD5 -> (author, pid)
text_to_author = {}
for ad in RESP.iterdir():
    if not ad.is_dir(): continue
    for fp in ad.glob("prompt-repl-*.json"):
        obj = json.loads(fp.read_text())
        t = obj.get("response", obj.get("response_text", ""))
        if t:
            text_to_author[md5_10(t)] = (ad.name, obj.get("prompt_id", fp.stem.replace("prompt-", "")))

# blind_id -> (pid, author)
bid_to_pa = {}
for jd in PACKETS.iterdir():
    if not jd.is_dir(): continue
    for fp in jd.glob("session_*.json"):
        d = json.loads(fp.read_text())
        entries = d.get("entries", []) if isinstance(d, dict) else d
        for e in entries:
            bid = e.get("blind_id")
            t = e.get("response_text", "")
            if bid and t:
                ah = text_to_author.get(md5_10(t))
                if ah:
                    bid_to_pa[bid] = (ah[1], ah[0])  # (pid, author)

def ranks(x):
    n = len(x)
    o = sorted(range(n), key=lambda i: x[i])
    r = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and x[o[j + 1]] == x[o[i]]:
            j += 1
        avg = (i + j) / 2.0 + 1
        for k in range(i, j + 1):
            r[o[k]] = avg
        i = j + 1
    return r

def spearman(a, b):
    if len(a) < 2: return float("nan")
    ra, rb = ranks(a), ranks(b)
    if np.std(ra) == 0 or np.std(rb) == 0: return float("nan")
    return float(np.corrcoef(ra, rb)[0, 1])

def pearson(a, b):
    if len(a) < 2: return float("nan")
    if np.std(a) == 0 or np.std(b) == 0: return float("nan")
    return float(np.corrcoef(a, b)[0, 1])

def boot_spearman_ci(deltas, others, B=2000):
    n = len(deltas)
    deltas = np.array(deltas); others = np.array(others)
    rhos = []
    for _ in range(B):
        idx = RNG.integers(0, n, n)
        d = deltas[idx]; o = others[idx]
        if np.std(d) == 0 or np.std(o) == 0:
            continue
        rhos.append(spearman(d.tolist(), o.tolist()))
    rhos = np.array(rhos)
    if len(rhos) == 0:
        return float("nan"), float("nan")
    return float(np.percentile(rhos, 2.5)), float(np.percentile(rhos, 97.5))

per_judge_pairs = {j: [] for j in JUDGES}
for judge in JUDGES:
    by_pa = defaultdict(list)
    for s in [1, 2]:
        fp = SCORES / judge / f"session_{s}_scored.json"
        if not fp.exists(): continue
        d = json.loads(fp.read_text())
        entries = d.get("entries", []) if isinstance(d, dict) else d
        if isinstance(d, dict) and d.get("scoring_method") != "native_in_context":
            continue
        for e in entries:
            bid = e.get("blind_id", "")
            pa = bid_to_pa.get(bid)
            if not pa: continue
            comp = float(np.mean([float(e[k]) for k in DIMS]))
            by_pa[pa].append((e.get("displayed_label", ""), comp))
    for pa, ents in by_pa.items():
        if len(ents) != 2: continue
        labels = [x[0] for x in ents]
        if judge in labels:
            self_e = next(x for x in ents if x[0] == judge)
            other_e = next(x for x in ents if x[0] != judge)
            per_judge_pairs[judge].append({
                "pid": pa[0], "author": pa[1],
                "delta": self_e[1] - other_e[1],
                "other_comp": other_e[1],
                "self_comp": self_e[1],
            })

# Write CSV
csv_p = OUT / "floor_raising_test.csv"
with csv_p.open("w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["judge", "prompt_id", "actual_author", "displayed_other", "self_composite", "other_composite", "delta"])
    for j in JUDGES:
        for p in per_judge_pairs[j]:
            w.writerow([JUDGE_SHORT[j], p["pid"], p["author"], "", f"{p['self_comp']:.3f}", f"{p['other_comp']:.3f}", f"{p['delta']:.3f}"])

md = []
md.append("# Floor-raising test: self-label uplift vs baseline rating\n")
md.append("Generated by `analysis/floor_raising_test.py`. For each native judge, for the ~20 responses shown once under the judge's own label and once under a non-self label (label-swap S1+S2), we test whether the per-response self-label uplift Δ = composite(self-displayed) − composite(other-displayed) correlates negatively with the response's baseline (non-self) composite. A strong negative correlation indicates that the self-label is doing the most work on responses the judge would otherwise rate lowest — i.e. it 'raises the floor' rather than 'raising the ceiling'.\n")
md.append("\n## Summary\n")
md.append("| Judge | n | Pearson r(Δ, base) | Spearman ρ(Δ, base) | 95% CI on ρ | mean base when Δ>0 | mean base when Δ≤0 |")
md.append("|---|---:|---:|---:|---|---:|---:|")
for j in JUDGES:
    pairs = per_judge_pairs[j]
    if not pairs: continue
    d_ = [p["delta"] for p in pairs]
    b_ = [p["other_comp"] for p in pairs]
    n = len(pairs)
    if np.std(d_) == 0:
        r_ = float("nan"); sp_ = float("nan"); lo, hi = float("nan"), float("nan")
    else:
        r_ = pearson(d_, b_)
        sp_ = spearman(d_, b_)
        lo, hi = boot_spearman_ci(d_, b_, B=B)
    pos = [p["other_comp"] for p in pairs if p["delta"] > 0]
    nonpos = [p["other_comp"] for p in pairs if p["delta"] <= 0]
    mp = float(np.mean(pos)) if pos else float("nan")
    mn = float(np.mean(nonpos)) if nonpos else float("nan")
    cell_ci = "—" if np.isnan(lo) else f"[{lo:.3f}, {hi:.3f}]"
    md.append(f"| {JUDGE_SHORT[j]} | {n} | {r_:.3f} | {sp_:.3f} | {cell_ci} | {mp:.3f} (n={len(pos)}) | {mn:.3f} (n={len(nonpos)}) |")

md.append("\n## Per-quintile uplift (claude + gemini)\n")
md.append("Split each judge's 20 paired baselines into quintiles (4 responses each) and report mean Δ per quintile (Q1 = lowest baseline, Q5 = highest):\n")
md.append("| Judge | Q1 mean Δ | Q2 | Q3 | Q4 | Q5 |")
md.append("|---|---:|---:|---:|---:|---:|")
for j in JUDGES:
    pairs = per_judge_pairs[j]
    if not pairs or all(p["delta"] == 0 for p in pairs):
        continue
    sorted_p = sorted(pairs, key=lambda x: x["other_comp"])
    n = len(sorted_p)
    # 5 quintiles of equal size
    q_size = n // 5
    qmeans = []
    for k in range(5):
        chunk = sorted_p[k*q_size:(k+1)*q_size]
        qmeans.append(float(np.mean([p["delta"] for p in chunk])) if chunk else float("nan"))
    md.append(f"| {JUDGE_SHORT[j]} | {qmeans[0]:+.3f} | {qmeans[1]:+.3f} | {qmeans[2]:+.3f} | {qmeans[3]:+.3f} | {qmeans[4]:+.3f} |")

md.append("\n## Interpretation\n")
md.append(
    "Claude and Gemini remain the clear floor-raising cases: their displayed-self uplift is largest "
    "on responses with lower non-self baselines (Claude ρ≈−0.67; Gemini ρ≈−0.83). GPT-5.5 is "
    "label-invariant in this slice (all Δ=0), so correlation is undefined. Kimi K2.6 is now complete; "
    "its displayed-self mean is near zero and much noisier, so any floor-raising pattern should be read as "
    "exploratory rather than a headline effect.\n\n"
    "Substantively, Kimi's completion strengthens the main conclusion: displayed self-label effects are "
    "heterogeneous across model families. Gemini shows the strongest causal displayed-self boost, Claude a "
    "smaller/non-robust one, GPT is exactly invariant here, and Kimi is near zero with wide uncertainty."
)

(OUT / "floor_raising_test.md").write_text("\n".join(md) + "\n")
print("\n".join(md))
