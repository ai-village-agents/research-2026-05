#!/usr/bin/env python3
"""Within-author floor-raising test.

Follow-up to `floor_raising_test.py`. The headline floor-raising result is
that per-response self-label uplift Δ correlates strongly negatively with the
non-self (baseline) composite. A natural skeptical reading is that the
correlation could be entirely driven by between-author quality differences:
Kimi-authored content has the lowest baseline AND happens to get the largest
self-label uplift, so the "floor-raising" story might be a re-description of
"anti-Kimi label penalty" (Gemini case) or "ceiling effect on already-high
responses" (Claude case).

To separate these, we residualize both Δ and baseline on actual_author
(subtract the per-author mean) and ask whether the negative correlation
survives within-author. If it does, the mechanism is genuinely about the
specific response's quality, not just about author identity. If it
disappears, the floor-raising claim collapses to an author-level effect.

We also compute (for completeness) a between-author component: replace each
response's Δ and baseline with the author-group means. The decomposition
total_cov = within_cov + between_cov holds approximately.

Outputs:
- results/floor_raising_within_author.csv: per-response (judge, pid, author,
  delta, baseline, delta_within, baseline_within, delta_between, baseline_between)
- results/floor_raising_within_author.md: summary table comparing total,
  within-author, and between-author Pearson/Spearman correlations.
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

JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5"]
JUDGE_SHORT = {"claude-opus-4.7": "claude", "gemini-3.1-pro": "gemini", "gpt-5.5": "gpt"}
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
RNG = np.random.default_rng(0xF1008)
B = 2000

def md5_10(s: str) -> str:
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
    if len(a) < 2: return float("nan")
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    if np.std(a) == 0 or np.std(b) == 0: return float("nan")
    return float(np.corrcoef(a, b)[0, 1])

def boot_ci(a, b, fn, B=2000):
    a = np.asarray(a, dtype=float); b = np.asarray(b, dtype=float)
    n = len(a)
    vals = []
    for _ in range(B):
        idx = RNG.integers(0, n, n)
        if np.std(a[idx]) == 0 or np.std(b[idx]) == 0:
            continue
        vals.append(fn(a[idx].tolist(), b[idx].tolist()))
    if not vals: return float("nan"), float("nan")
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))

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
            })

def residualize(rows, key, by="author"):
    grp = defaultdict(list)
    for r in rows: grp[r[by]].append(r[key])
    means = {a: float(np.mean(v)) for a, v in grp.items()}
    return [r[key] - means[r[by]] for r in rows], [means[r[by]] for r in rows]

csv_p = OUT / "floor_raising_within_author.csv"
with csv_p.open("w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["judge", "prompt_id", "actual_author", "delta", "baseline", "delta_within", "baseline_within", "delta_between", "baseline_between"])
    for j in JUDGES:
        pairs = per_judge_pairs[j]
        if not pairs: continue
        dw, db = residualize(pairs, "delta")
        bw, bb = residualize(pairs, "other_comp")
        for i, p in enumerate(pairs):
            w.writerow([JUDGE_SHORT[j], p["pid"], p["author"], f"{p['delta']:.3f}", f"{p['other_comp']:.3f}", f"{dw[i]:.3f}", f"{bw[i]:.3f}", f"{db[i]:.3f}", f"{bb[i]:.3f}"])

md = []
md.append("# Within-author floor-raising test\n")
md.append("Generated by `analysis/floor_raising_within_author.py`. Follow-up to `floor_raising_test.md`. The headline floor-raising result (Δ correlates strongly negatively with non-self baseline composite) could in principle be entirely between-author: Kimi-authored content has the lowest baseline AND happens to attract the largest uplift, so the negative correlation might just re-encode an anti-Kimi (or pro-author-K) label preference. To separate these, we residualize both Δ and baseline on `actual_author` (subtract the per-author mean), then re-compute correlations on the within-author residuals. We also compute between-author correlations on the author-group means.\n")
md.append("\n## Decomposition table\n")
md.append("| Judge | n | total r | within r | between r | total ρ | within ρ | between ρ | within ρ 95% CI |")
md.append("|---|---:|---:|---:|---:|---:|---:|---:|---|")
for j in JUDGES:
    pairs = per_judge_pairs[j]
    if not pairs: continue
    if all(p["delta"] == 0 for p in pairs):
        continue
    d_ = [p["delta"] for p in pairs]
    b_ = [p["other_comp"] for p in pairs]
    dw, db = residualize(pairs, "delta")
    bw, bb = residualize(pairs, "other_comp")
    r_tot = pearson(d_, b_); sp_tot = spearman(d_, b_)
    r_w = pearson(dw, bw); sp_w = spearman(dw, bw)
    r_b = pearson(db, bb); sp_b = spearman(db, bb)
    lo, hi = boot_ci(dw, bw, spearman, B=B)
    cell_ci = "—" if np.isnan(lo) else f"[{lo:.3f}, {hi:.3f}]"
    md.append(f"| {JUDGE_SHORT[j]} | {len(pairs)} | {r_tot:+.3f} | {r_w:+.3f} | {r_b:+.3f} | {sp_tot:+.3f} | {sp_w:+.3f} | {sp_b:+.3f} | {cell_ci} |")

md.append("\n## Per-author component\n")
md.append("Author-mean Δ and author-mean baseline (the 'between' component):\n")
md.append("| Judge | Author | n | mean Δ | mean baseline |")
md.append("|---|---|---:|---:|---:|")
for j in JUDGES:
    pairs = per_judge_pairs[j]
    if not pairs or all(p["delta"] == 0 for p in pairs): continue
    grp = defaultdict(list)
    for p in pairs: grp[p["author"]].append(p)
    for a in sorted(grp):
        ents = grp[a]
        md.append(f"| {JUDGE_SHORT[j]} | {a} | {len(ents)} | {np.mean([e['delta'] for e in ents]):+.3f} | {np.mean([e['other_comp'] for e in ents]):.3f} |")

md.append("\n## Interpretation\n")
md.append(
    "If the within-author correlation is near zero, the floor-raising effect is entirely a between-author artifact (the mechanism reduces to author-identity bias under another name). If the within-author correlation remains substantial and negative, the floor-raising mechanism is genuinely about the specific response's quality, surviving an author-identity control.\n\n"
    "Read the table by row: 'total' reproduces the headline correlation; 'within' is the same correlation after subtracting per-author means; 'between' uses only the author-group means (4 points). Sample sizes are small (n≈20 per judge total, n≈4-7 per author), so the within-author CI is wide, but the point estimate direction is informative.\n"
)
(OUT / "floor_raising_within_author.md").write_text("\n".join(md) + "\n")
print("Wrote", csv_p)
print("Wrote", OUT / "floor_raising_within_author.md")
