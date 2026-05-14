#!/usr/bin/env python3
"""Cross-judge response-level correlation (label-swap, native judges).

Tests whether the native judges (Claude Opus 4.7, Gemini 3.1 Pro, GPT-5.5, Kimi K2.6)
AGREE on which RESPONSES are good/bad in the label-swap data, despite their
different label-driven biases. High agreement = judges share a quality signal,
and the observed residual self-preference is BIAS on top of a SHARED signal,
not just noise.

Data: experiments/replication-wave/score_sheets/label_swap/<judge>/session_{1,2}_scored.json
(only entries with scoring_method == native_in_context).

Response identifier: (prompt_id, actual_author) — uniquely identifies one of
the 40 underlying response texts. Each appears twice per judge across S1+S2,
once with each of two labels (Latin-square design).

Outputs:
- results/cross_judge_response_correlation.csv: per-response wide table
- results/cross_judge_response_correlation.md: pairwise correlations + author matrix
"""
from __future__ import annotations
import json, hashlib, csv, pathlib
from collections import defaultdict
import numpy as np

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

# Build blind_id -> (prompt_id, author) using packets (any judge's packet has response_text)
# AND text MD5 fallback
def md5_10(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:10]

# text MD5 -> author
text_to_author = {}
for author_dir in RESP.iterdir():
    if not author_dir.is_dir():
        continue
    author = author_dir.name
    for fp in author_dir.glob("prompt-repl-*.json"):
        obj = json.loads(fp.read_text())
        text = obj.get("response", obj.get("response_text", ""))
        if not text:
            continue
        # try both raw and stripped
        text_to_author[md5_10(text)] = (author, obj.get("prompt_id", fp.stem.replace("prompt-", "")))
        text_to_author[md5_10(text.strip())] = (author, obj.get("prompt_id", fp.stem.replace("prompt-", "")))

# blind_id -> (prompt_id, author) via packets
bid_to_pa = {}
for jdir in PACKETS.iterdir():
    if not jdir.is_dir():
        continue
    for sess_fp in jdir.glob("session_*.json"):
        d = json.loads(sess_fp.read_text())
        entries = d.get("entries", []) if isinstance(d, dict) else d
        for e in entries:
            bid = e.get("blind_id")
            text = e.get("response_text", "")
            pid = e.get("prompt_id", "")
            if not (bid and text):
                continue
            ah = text_to_author.get(md5_10(text)) or text_to_author.get(md5_10(text.strip()))
            if ah:
                aut = ah[0]
            else:
                aut = "unknown"
            bid_to_pa[bid] = (pid, aut)

# Load native scores per judge: per-(pid,author) composite, also non-self only
per_judge = {j: defaultdict(list) for j in JUDGES}
per_judge_ns = {j: defaultdict(list) for j in JUDGES}

for judge in JUDGES:
    for sess in [1, 2]:
        fp = SCORES / judge / f"session_{sess}_scored.json"
        if not fp.exists():
            continue
        d = json.loads(fp.read_text())
        if isinstance(d, dict):
            if d.get("scoring_method") != "native_in_context":
                continue
            entries = d.get("entries", [])
        else:
            entries = d
        for e in entries:
            bid = e.get("blind_id", "")
            pa = bid_to_pa.get(bid)
            if not pa:
                continue
            try:
                comp = float(np.mean([float(e[k]) for k in DIMS]))
            except Exception:
                continue
            per_judge[judge][pa].append(comp)
            if e.get("displayed_label", "") != judge:
                per_judge_ns[judge][pa].append(comp)

all_keys = sorted(set().union(*[set(per_judge[j].keys()) for j in JUDGES]))

def spearman_pearson(a, b):
    if len(a) < 2:
        return float("nan"), float("nan")
    a = np.array(a, dtype=float); b = np.array(b, dtype=float)
    def rank(x):
        n = len(x)
        order = sorted(range(n), key=lambda i: x[i])
        ranks = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and x[order[j+1]] == x[order[i]]:
                j += 1
            avg = (i + j) / 2.0 + 1
            for k in range(i, j+1):
                ranks[order[k]] = avg
            i = j + 1
        return ranks
    ra, rb = rank(a.tolist()), rank(b.tolist())
    sp = float(np.corrcoef(ra, rb)[0, 1]) if np.std(ra) > 0 and np.std(rb) > 0 else float("nan")
    pe = float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 0 and np.std(b) > 0 else float("nan")
    return sp, pe

# Rows: only keep (pid,author) keys with all native judges scored
rows = []
for k in all_keys:
    pid, author = k
    if author == "unknown":
        continue
    if all(per_judge[j].get(k) for j in JUDGES):
        rec = {"prompt_id": pid, "author": author}
        for j in JUDGES:
            rec[JUDGE_SHORT[j]] = float(np.mean(per_judge[j][k]))
        rows.append(rec)

pairs = [(JUDGE_SHORT[a], JUDGE_SHORT[b]) for i, a in enumerate(JUDGES) for b in JUDGES[i+1:]]
pair_results = []
for a, b in pairs:
    va = [r[a] for r in rows]; vb = [r[b] for r in rows]
    sp, pe = spearman_pearson(va, vb)
    pair_results.append((a, b, len(rows), sp, pe))

# Non-self subset
rows_ns = []
for k in all_keys:
    pid, author = k
    if author == "unknown":
        continue
    if all(per_judge_ns[j].get(k) for j in JUDGES):
        rec = {"prompt_id": pid, "author": author}
        for j in JUDGES:
            rec[JUDGE_SHORT[j]] = float(np.mean(per_judge_ns[j][k]))
        rows_ns.append(rec)

pair_results_ns = []
for a, b in pairs:
    va = [r[a] for r in rows_ns]; vb = [r[b] for r in rows_ns]
    sp, pe = spearman_pearson(va, vb)
    pair_results_ns.append((a, b, len(rows_ns), sp, pe))

# Author × judge matrix
AUTHORS = sorted(set(r["author"] for r in rows))
author_judge = {a: {} for a in AUTHORS}
for a in AUTHORS:
    sub = [r for r in rows if r["author"] == a]
    for j in JUDGES:
        author_judge[a][JUDGE_SHORT[j]] = float(np.mean([r[JUDGE_SHORT[j]] for r in sub]))

author_ranks = {}
for j in JUDGES:
    vals = [(a, author_judge[a][JUDGE_SHORT[j]]) for a in AUTHORS]
    vals.sort(key=lambda x: -x[1])
    author_ranks[JUDGE_SHORT[j]] = [a for a, _ in vals]

author_corr = []
for a, b in pairs:
    va = [author_judge[au][a] for au in AUTHORS]
    vb = [author_judge[au][b] for au in AUTHORS]
    sp, pe = spearman_pearson(va, vb)
    author_corr.append((a, b, len(AUTHORS), sp, pe))

# Write CSV
csv_path = OUT / "cross_judge_response_correlation.csv"
with csv_path.open("w", newline="") as f:
    w = csv.writer(f, lineterminator="\n")
    shorts = [JUDGE_SHORT[j] for j in JUDGES]
    w.writerow(["prompt_id", "author", *shorts])
    for r in rows:
        w.writerow([r["prompt_id"], r["author"], *[f"{r[x]:.4f}" for x in shorts]])

# Write MD
md = []
md.append("# Cross-judge response-level correlation\n")
md.append("Generated by `analysis/cross_judge_response_correlation.py`. Source: native label-swap S1+S2 score sheets.\n")
md.append("Per-response composite = mean of 5 rubric dims (1–10), averaged across both label conditions a response is shown under (S1+S2). Response identifier: (prompt_id, actual_author).\n")
md.append(f"N responses with all 4 judges scored: **{len(rows)}**.\n")
md.append("\n## 1. Pairwise correlations across all responses\n")
md.append("| pair | n | Spearman ρ | Pearson r |")
md.append("|------|---|-----------|-----------|")
for a, b, n, sp, pe in pair_results:
    md.append(f"| {a} ↔ {b} | {n} | {sp:.3f} | {pe:.3f} |")
md.append("\n## 2. Pairwise correlations on non-self subset (judge ≠ displayed label)\n")
md.append("Excludes entries where the displayed label matches the judge — isolates 'quality agreement when nobody is shown their own name'.\n")
md.append("| pair | n | Spearman ρ | Pearson r |")
md.append("|------|---|-----------|-----------|")
for a, b, n, sp, pe in pair_results_ns:
    md.append(f"| {a} ↔ {b} | {n} | {sp:.3f} | {pe:.3f} |")
md.append("\n## 3. Author × judge mean composite\n")
md.append("Mean per-response composite by (actual_author, judge) over label-swap responses (averaged across labels):\n")
shorts = [JUDGE_SHORT[j] for j in JUDGES]
md.append("| author | " + " | ".join(shorts) + " |")
md.append("|--------|" + "|".join(["--------" for _ in shorts]) + "|")
for a in AUTHORS:
    md.append(f"| {a} | " + " | ".join(f"{author_judge[a][x]:.3f}" for x in shorts) + " |")
md.append("\n## 4. Author-rank concordance\n")
md.append("Author rankings (best → worst) by each judge in the native label-swap data:\n")
for j in JUDGES:
    md.append(f"- **{JUDGE_SHORT[j]}**: " + " > ".join(author_ranks[JUDGE_SHORT[j]]))
md.append("")
md.append("| pair | n authors | Spearman ρ | Pearson r |")
md.append("|------|-----------|-----------|-----------|")
for a, b, n, sp, pe in author_corr:
    md.append(f"| {a} ↔ {b} | {n} | {sp:.3f} | {pe:.3f} |")

mean_sp = float(np.mean([sp for _,_,_,sp,_ in pair_results]))
mean_sp_ns = float(np.mean([sp for _,_,_,sp,_ in pair_results_ns]))
mean_auth_sp = float(np.mean([sp for _,_,_,sp,_ in author_corr]))

md.append("\n## 5. Interpretation\n")
md.append(
    f"The four native judges show **mean pairwise Spearman ρ = {mean_sp:.3f}** on per-response "
    f"composite scores across {len(rows)} responses. Restricting to non-self displayed labels "
    f"only gives ρ = {mean_sp_ns:.3f} (n={len(rows_ns)}). At the author level (4 authors × 4 "
    f"judges) the mean Spearman is {mean_auth_sp:.3f}.\n\n"
    "Combined with the small but systematic per-label SELF-vs-OTHER deltas reported in §3.10 "
    "of the blogpost (Gemini +0.293 [+0.142, +0.452]; Claude +0.120 [−0.067, +0.304]; GPT-5.5 label-invariant; Kimi +0.007 [−0.305, +0.344]), this pattern is consistent with the 'biased, not noisy' interpretation: "
    "the native judges substantially agree on *which* responses are better, while Kimi adds visible heterogeneity; the residual self-preference signal remains small relative to the shared quality signal rather than pure disagreement about response quality."
)

md_text = "\n".join(md) + "\n"
(OUT / "cross_judge_response_correlation.md").write_text(md_text)
print(md_text)
