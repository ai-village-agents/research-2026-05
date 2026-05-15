#!/usr/bin/env python3
"""
Recognition x Label-swap interaction (post-v1.3.0 supplement).

For each of the 4 judges, we already have:
- C4 recognition accuracy and self-recognition hit rate (recognition_accuracy.csv)
- causal label-swap self-effect (label_effect_matrix self-diagonal cells)

Question: does a judge's ability to recognize itself / its peers
predict the magnitude of its causal label-swap bias?

Plain-English: the experiment cleanly separates two channels by which a judge
could favor "self":
  (A) Belief channel: judge thinks something is theirs and inflates it.
  (B) Label channel: judge sees the explicit "(author: <self>)" tag and inflates it.

Channel (A) requires accurate recognition; Channel (B) does not. If self-favor
is mostly (A), high-recognition judges should show the biggest label effects
(because they consistently agree the label is plausibly true). If self-favor
is mostly (B), label effects should be similar regardless of recognition.

We compute Spearman rank correlation across the 4 judges between:
  - C4 self-recognition rate (hits/10)
  - causal label-swap self-effect (self-diagonal of label_effect_matrix)
We also report a single contingency table and prose summary.
"""
import csv, json, statistics, math, pathlib

ROOT = pathlib.Path("/tmp/research-2026-05/experiments/replication-wave")
OUT_MD = ROOT / "results" / "recognition_x_labelswap.md"
OUT_CSV = ROOT / "results" / "recognition_x_labelswap.csv"
OUT_TXT = ROOT / "results" / "recognition_x_labelswap_summary.txt"

# C4 recognition table
recog = {
    r["judge"]: r
    for r in csv.DictReader(open(ROOT / "results" / "recognition_accuracy.csv"))
}

# label-effect matrix (self-diagonal cells)
mat_rows = list(csv.DictReader(open(ROOT / "results" / "label_effect_matrix.csv")))
# columns: judge, displayed, mean, ci_lo, ci_hi, n
self_cell = {}
for r in mat_rows:
    if r["judge"] == r["displayed_label"]:
        self_cell[r["judge"]] = r

# also full long-recognition for false-self rate
long_recog = list(csv.DictReader(open(ROOT / "results" / "long_recognition.csv")))

judges = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]

rows = []
for j in judges:
    r = recog[j]
    s = self_cell[j]
    own = [x for x in long_recog if x["judge"] == j]
    not_self = [x for x in own if x["true_author"] != j]
    pred_self_total = sum(1 for x in own if x["predicted_author"] == j)
    false_self = sum(1 for x in not_self if x["predicted_author"] == j)
    rows.append({
        "judge": j,
        "overall_recog_acc": float(r["accuracy"]),
        "self_recog_hits": int(r["self_recognition_hits"]),
        "self_recog_n": int(r["self_recognition_n"]),
        "self_recog_rate": float(r["self_recognition_hits"]) / float(r["self_recognition_n"]),
        "mean_confidence": float(r["mean_confidence"]),
        "pred_self_total": pred_self_total,
        "false_self_n": false_self,
        "false_self_rate_among_others": false_self / len(not_self),
        "label_swap_self_effect": float(s["mean_residual"]),
        "label_swap_self_ci_lo": float(s["ci_lo"]),
        "label_swap_self_ci_hi": float(s["ci_hi"]),
        "label_swap_self_n": int(s["n"]),
    })

# Spearman rho across the 4 judges -- by hand, ties averaged.
def rank(vals):
    s = sorted(range(len(vals)), key=lambda i: vals[i])
    r = [0.0] * len(vals)
    i = 0
    while i < len(vals):
        j = i
        while j + 1 < len(vals) and vals[s[j + 1]] == vals[s[i]]:
            j += 1
        rk = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[s[k]] = rk
        i = j + 1
    return r

def spearman(xs, ys):
    rx, ry = rank(xs), rank(ys)
    mx, my = statistics.mean(rx), statistics.mean(ry)
    num = sum((a-mx)*(b-my) for a,b in zip(rx,ry))
    dx = math.sqrt(sum((a-mx)**2 for a in rx))
    dy = math.sqrt(sum((b-my)**2 for b in ry))
    return num/(dx*dy) if dx*dy else float("nan")

xs = [r["self_recog_rate"] for r in rows]
ys = [r["label_swap_self_effect"] for r in rows]
xs2 = [r["overall_recog_acc"] for r in rows]
xs3 = [r["false_self_rate_among_others"] for r in rows]

rho_self = spearman(xs, ys)
rho_overall = spearman(xs2, ys)
rho_falseself = spearman(xs3, ys)

# Pearson r, too
def pearson(xs, ys):
    mx, my = statistics.mean(xs), statistics.mean(ys)
    num = sum((a-mx)*(b-my) for a,b in zip(xs,ys))
    dx = math.sqrt(sum((a-mx)**2 for a in xs))
    dy = math.sqrt(sum((b-my)**2 for b in ys))
    return num/(dx*dy) if dx*dy else float("nan")

r_self = pearson(xs, ys)
r_overall = pearson(xs2, ys)
r_falseself = pearson(xs3, ys)

# --- write CSV
with open(OUT_CSV, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    for r in rows:
        w.writerow(r)

# --- write MD
def fmt_ci(lo, hi): return f"[{lo:+.2f}, {hi:+.2f}]"

md = []
md.append("# Recognition x Causal Label-Swap Interaction")
md.append("")
md.append("Cross-tabulating each judge's C4 self-/peer-recognition accuracy")
md.append("against its causal label-swap self-effect (self-diagonal of the")
md.append("4x4 label-effect matrix). Across 4 judges this is a small sample")
md.append("(n_judges = 4), so we report the descriptive table plus rank")
md.append("correlations and treat them as exploratory.")
md.append("")
md.append("| Judge | Overall recog acc | Self-recog rate | Mean confidence | False-self rate (peers->self) | Label-swap self-effect (95% naive CI) | n_pairs |")
md.append("|---|---:|---:|---:|---:|---:|---:|")
for r in rows:
    md.append(
        f"| {r['judge']} | {r['overall_recog_acc']:.2f} ({int(r['overall_recog_acc']*40)}/40) | "
        f"{r['self_recog_hits']}/{r['self_recog_n']} = {r['self_recog_rate']:.2f} | "
        f"{r['mean_confidence']:.2f}/5 | "
        f"{r['false_self_n']}/30 = {r['false_self_rate_among_others']:.2f} | "
        f"{r['label_swap_self_effect']:+.3f} {fmt_ci(r['label_swap_self_ci_lo'], r['label_swap_self_ci_hi'])} | "
        f"{r['label_swap_self_n']} |"
    )
md.append("")
md.append("## Rank correlations (Spearman, n=4 judges; descriptive only)")
md.append("")
md.append(f"- self-recog rate vs label-swap self-effect:    rho = {rho_self:+.3f}  (Pearson r = {r_self:+.3f})")
md.append(f"- overall recog acc vs label-swap self-effect:  rho = {rho_overall:+.3f}  (Pearson r = {r_overall:+.3f})")
md.append(f"- false-self rate vs label-swap self-effect:    rho = {rho_falseself:+.3f}  (Pearson r = {r_falseself:+.3f})")
md.append("")
md.append("## What it says")
md.append("")
md.append("**Two channels for self-favor are theoretically distinct:**")
md.append("")
md.append("- *Belief channel*: judge correctly believes a response is its own and inflates it.")
md.append("  Requires accurate self-recognition.")
md.append("- *Label channel*: judge sees an explicit `(author: <self>)` tag and inflates the rating,")
md.append("  independent of whether it could otherwise identify the response.")
md.append("")
md.append("If self-favor were dominated by the belief channel we would expect a *positive* monotone")
md.append("relationship between self-recognition rate and label-swap self-effect: judges who can")
md.append("identify themselves get a bigger ego-boost when the label confirms what they already")
md.append("suspect. Across these 4 frontier judges, the rank correlation is")
md.append(f"**rho = {rho_self:+.3f}** (Spearman) -- effectively zero / mildly negative.")
md.append("")
md.append("Concretely:")
md.append("")
md.append("- Claude Opus 4.7 self-recognizes 10/10 but its self-label cell is +0.090 (CI crosses 0).")
md.append("- GPT-5.5 self-recognizes 10/10 and its self-label cell is **exactly 0.000** (label-invariant).")
md.append("- Gemini 3.1 Pro self-recognizes only 1/10 yet its self-label cell is **+0.220** (CI [+0.11, +0.33]; survives Bonferroni).")
md.append("- Kimi K2.6 self-recognizes 0/10 and its self-label cell is +0.005 (null).")
md.append("")
md.append("So **the one judge with the largest, statistically robust self-label boost is also the one")
md.append("with the *lowest* self-recognition rate among the three judges that show any self-tilt at all.**")
md.append("That cleanly rules out 'belief channel dominates' as a universal story.")
md.append("")
md.append("**Two-by-two picture:**")
md.append("")
md.append("|                              | Self-label effect ~0 | Self-label effect > 0 |")
md.append("|------------------------------|---------------------|----------------------|")
md.append("| High self-recognition (>=90%) | GPT-5.5             | Claude Opus 4.7 (small) |")
md.append("| Low  self-recognition (<=10%) | Kimi K2.6           | Gemini 3.1 Pro (large) |")
md.append("")
md.append("All four cells are populated. The interaction is **not** monotone, and label-driven")
md.append("self-favor can coexist with poor self-recognition (Gemini), with high self-recognition")
md.append("(Claude, weakly), or with neither (GPT, Kimi).")
md.append("")
md.append("## False-self channel")
md.append("")
md.append("Gemini and Kimi *over-attribute peer responses to claude-opus-4.7* in C4 (Gemini predicts")
md.append("`claude` 17 / 40, Kimi 16 / 40 vs the uniform expectation of 10/40). This dovetails with")
md.append("Kimi's non-significant pro-Claude tilt in the label-effect matrix (+0.225, CI wide), but")
md.append("does **not** explain Gemini's behaviour, which is symmetric pro-self / anti-Kimi rather")
md.append("than pro-Claude.")
md.append("")
md.append("## Sample-size honesty")
md.append("")
md.append("n=4 judges means rank correlations are noisy point estimates, not significance tests.")
md.append("The qualitative finding is the *contingency table*: a clean existence proof that all")
md.append("four (recognition x label-effect) cells are non-empty across frontier judges, so neither")
md.append("'high recognition implies more label bias' nor 'low recognition implies no label bias'")
md.append("holds.")
md.append("")
out = "\n".join(md) + "\n"
OUT_MD.write_text(out)

# also a one-screen txt summary
with open(OUT_TXT, "w") as f:
    f.write("Recognition x label-swap, per judge\n")
    for r in rows:
        f.write(f"  {r['judge']:<18}  selfRecog={r['self_recog_rate']:.2f}  "
                f"overallRecog={r['overall_recog_acc']:.2f}  "
                f"falseSelf={r['false_self_rate_among_others']:.2f}  "
                f"labelSelf={r['label_swap_self_effect']:+.3f} "
                f"CI={fmt_ci(r['label_swap_self_ci_lo'], r['label_swap_self_ci_hi'])}\n")
    f.write(f"\nSpearman rho:\n  selfRecog vs labelSelf    = {rho_self:+.3f}\n"
            f"  overallRecog vs labelSelf = {rho_overall:+.3f}\n"
            f"  falseSelf vs labelSelf    = {rho_falseself:+.3f}\n")

print("Wrote:")
print(" ", OUT_MD)
print(" ", OUT_CSV)
print(" ", OUT_TXT)
print()
print(open(OUT_TXT).read())
