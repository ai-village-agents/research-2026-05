#!/usr/bin/env python3
"""Per-dimension floor-raising test.

Extends `floor_raising_test.py` from per-response composite to per-dimension.
The label-swap test gives ~20 paired responses per judge; at the dimension
level this becomes ~100 paired (response, dimension) cells per judge,
substantially increasing power for the floor-raising test.

For each native judge J, for each of the ~20 label-swap responses, for each
of the 5 rubric dimensions d in {correctness, completeness, clarity,
creativity, constraint_adherence}:
- delta_d = score_d(self-displayed) − score_d(other-displayed)
- baseline_d = score_d(other-displayed)

We then ask: does delta_d correlate negatively with baseline_d, pooled
across (response, dim)? And does the correlation differ across dimensions?
Subjective dimensions (creativity, completeness) might show stronger
floor-raising than objective ones (correctness, constraint adherence).

Outputs:
- results/floor_raising_per_dim.csv: per-(judge,pid,author,dim) row
- results/floor_raising_per_dim.md: pooled and per-dim ρ table
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

JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
SHORT = {"claude-opus-4.7": "claude", "gemini-3.1-pro": "gemini", "gpt-5.5": "gpt", "kimi-k2.6": "kimi"}
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
RNG = np.random.default_rng(0xF1010)
B = 2000

def md5_10(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:10]

text_to_author = {}
for ad in RESP.iterdir():
    if not ad.is_dir(): continue
    for fp in ad.glob("prompt-repl-*.json"):
        obj = json.loads(fp.read_text())
        t = obj.get("response", obj.get("response_text", ""))
        if t:
            text_to_author[md5_10(t)] = (ad.name, obj.get("prompt_id", fp.stem.replace("prompt-", "")))

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
                    bid_to_pa[bid] = (ah[1], ah[0])

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
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    if len(a) < 2 or np.std(a) == 0 or np.std(b) == 0: return float("nan")
    return float(np.corrcoef(a, b)[0, 1])

def boot_ci_cluster(a, b, fn, clusters, B=2000):
    """Cluster bootstrap by cluster id (= pid) to respect within-response correlations."""
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    cids = np.asarray(clusters)
    uniq = list(set(clusters))
    cmap = {c: np.where(cids == c)[0] for c in uniq}
    vals = []
    for _ in range(B):
        chosen = RNG.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([cmap[c] for c in chosen])
        if np.std(a[idx]) == 0 or np.std(b[idx]) == 0:
            continue
        vals.append(fn(a[idx].tolist(), b[idx].tolist()))
    if not vals: return float("nan"), float("nan")
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))

# Build per-(judge, pid, displayed) -> dim values
per_judge_rows = {j: [] for j in JUDGES}
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
            dim_vals = {dn: float(e[dn]) for dn in DIMS}
            by_pa[pa].append((e.get("displayed_label", ""), dim_vals))
    for pa, ents in by_pa.items():
        if len(ents) != 2: continue
        labels = [x[0] for x in ents]
        if judge in labels:
            self_e = next(x for x in ents if x[0] == judge)
            other_e = next(x for x in ents if x[0] != judge)
            for dn in DIMS:
                per_judge_rows[judge].append({
                    "pid": pa[0], "author": pa[1], "dim": dn,
                    "self": self_e[1][dn], "other": other_e[1][dn],
                    "delta": self_e[1][dn] - other_e[1][dn],
                    "baseline": other_e[1][dn],
                })

csv_p = OUT / "floor_raising_per_dim.csv"
with csv_p.open("w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["judge","prompt_id","actual_author","dim","self","other","delta","baseline"])
    for j in JUDGES:
        for r in per_judge_rows[j]:
            w.writerow([SHORT[j], r["pid"], r["author"], r["dim"], r["self"], r["other"], f"{r['delta']:+.0f}", f"{r['baseline']:.0f}"])

md = []
md.append("# Per-dimension floor-raising test\n")
md.append("Generated by `analysis/floor_raising_per_dim.py`. Extends `floor_raising_test.md` from per-response composite (~20 paired responses per judge) to per-dimension (~100 paired (response, dim) cells per judge). For each native judge, for each of the 5 rubric dimensions d, we compute Δ_d = score_d(self-displayed) − score_d(other-displayed) and baseline_d = score_d(other-displayed). The pooled (across dim and response) Spearman ρ uses cluster-bootstrap by prompt_id (B=2000) to respect the within-response correlation structure.\n")
md.append("\n## Pooled (response × dim) test\n")
md.append("| Judge | n cells | mean Δ | Pearson r | Spearman ρ | 95% CI on ρ |")
md.append("|---|---:|---:|---:|---:|---|")
for j in JUDGES:
    rows = per_judge_rows[j]
    if not rows: continue
    d_ = [r["delta"] for r in rows]
    b_ = [r["baseline"] for r in rows]
    if np.std(d_) == 0:
        md.append(f"| {SHORT[j]} | {len(rows)} | {np.mean(d_):+.3f} | (Δ all 0) | — | — |")
        continue
    r_ = pearson(d_, b_); sp_ = spearman(d_, b_)
    lo, hi = boot_ci_cluster(d_, b_, spearman, [r["pid"] for r in rows], B=B)
    ci = "—" if np.isnan(lo) else f"[{lo:.3f}, {hi:.3f}]"
    md.append(f"| {SHORT[j]} | {len(rows)} | {np.mean(d_):+.3f} | {r_:+.3f} | {sp_:+.3f} | {ci} |")

md.append("\n## Per-dimension breakdown\n")
md.append("Spearman ρ(Δ_d, baseline_d) within each rubric dimension, n=20 cells per judge per dim:\n")
md.append("| Judge | correctness | completeness | clarity | creativity | constraint_adherence |")
md.append("|---|---:|---:|---:|---:|---:|")
for j in JUDGES:
    rows = per_judge_rows[j]
    if not rows or all(r["delta"] == 0 for r in rows):
        continue
    cells = []
    for dn in DIMS:
        sub = [r for r in rows if r["dim"] == dn]
        d_ = [r["delta"] for r in sub]
        b_ = [r["baseline"] for r in sub]
        if np.std(d_) == 0:
            cells.append("(Δ=0)")
        else:
            cells.append(f"{spearman(d_, b_):+.3f}")
    md.append(f"| {SHORT[j]} | " + " | ".join(cells) + " |")

md.append("\n## Mean Δ per dimension\n")
md.append("Mean self-label uplift per dimension (positive = self-displayed scored higher on that dim, on average):\n")
md.append("| Judge | correctness | completeness | clarity | creativity | constraint_adherence |")
md.append("|---|---:|---:|---:|---:|---:|")
for j in JUDGES:
    rows = per_judge_rows[j]
    if not rows: continue
    cells = []
    for dn in DIMS:
        sub = [r for r in rows if r["dim"] == dn]
        cells.append(f"{np.mean([r['delta'] for r in sub]):+.3f}")
    md.append(f"| {SHORT[j]} | " + " | ".join(cells) + " |")

md.append("\n## Interpretation\n")
md.append(
    "At the per-cell level (five rubric dimensions × 20 paired responses per judge), Claude and Gemini "
    "again show the clean floor-raising signature: self-label uplift is negatively related to baseline "
    "quality across all rubric dimensions. GPT-5.5 remains label-invariant. Kimi K2.6 is included now, "
    "but its average displayed-self effect is near zero and dimension-specific estimates are noisy/wide; "
    "do not treat Kimi as a fourth strong floor-raising replicate.\n\n"
    "The strongest statement remains model-family heterogeneity rather than universality: the floor-raising "
    "mechanism is clear for Claude/Gemini, absent for GPT, and inconclusive/near-zero for Kimi."
)
(OUT / "floor_raising_per_dim.md").write_text("\n".join(md) + "\n")
print("Wrote", csv_p)
print("Wrote", OUT / "floor_raising_per_dim.md")
