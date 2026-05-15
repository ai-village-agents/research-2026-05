"""
Per-dimension C1 self-preference breakdown.

The rubric has 5 dimensions: correctness, completeness, clarity, creativity,
constraint_adherence. We ask: which dimensions carry the self-preference bias?

For each (judge, dim) compute self − mean(others) for each prompt in c1, then
mean across 10 prompts with cluster-bootstrap CI (B=4000).
"""
import csv, json, random
from collections import defaultdict
random.seed(11_15_409_2)

DIMS = ["correctness","completeness","clarity","creativity","constraint_adherence"]
JUDGES = ["claude-opus-4.7","gemini-3.1-pro","gpt-5.5","kimi-k2.6"]
SHORT = {"claude-opus-4.7":"Claude","gemini-3.1-pro":"Gemini","gpt-5.5":"GPT","kimi-k2.6":"Kimi"}

with open("experiments/replication-wave/results/long_scores.csv") as f:
    rows = [r for r in csv.DictReader(f) if r["condition"]=="c1"]

# (judge,prompt) -> author -> dim -> score
cells = defaultdict(lambda: defaultdict(dict))
for r in rows:
    for d in DIMS:
        cells[(r["judge"], r["prompt_id"])][r["author"]][d] = int(r[d])

# For each judge×dim×prompt: self - mean(others)
def sp(j, d, p):
    auth = cells[(j,p)]
    if len(auth) != 4 or j not in auth: return None
    self_s = auth[j][d]
    other_s = [auth[a][d] for a in auth if a != j]
    return self_s - sum(other_s)/len(other_s)

prompts = sorted({p for (_,p) in cells.keys()})

# Compute point estimates and cluster-bootstrap CIs
results = {}
B = 4000
for j in JUDGES:
    for d in DIMS:
        per_prompt = [sp(j,d,p) for p in prompts]
        per_prompt = [v for v in per_prompt if v is not None]
        mean = sum(per_prompt)/len(per_prompt)
        boots = []
        for _ in range(B):
            samp = [random.choice(per_prompt) for _ in per_prompt]
            boots.append(sum(samp)/len(samp))
        boots.sort()
        lo = boots[int(0.025*B)]; hi = boots[int(0.975*B)]
        results[(j,d)] = {"mean":mean, "lo":lo, "hi":hi}

# Print
print(f"\n{'Judge':8s}  " + "  ".join(f"{d[:12]:>13s}" for d in DIMS))
for j in JUDGES:
    print(f"{SHORT[j]:8s}  " + "  ".join(
        f"{results[(j,d)]['mean']:+5.2f}[{results[(j,d)]['lo']:+5.2f},{results[(j,d)]['hi']:+5.2f}]" for d in DIMS))

# Which dim carries the bias the most? Per-judge dim-rank
print("\n=== per-judge: which dim has the largest |self-pref|? ===")
for j in JUDGES:
    ranked = sorted(DIMS, key=lambda d: -abs(results[(j,d)]["mean"]))
    print(f"  {SHORT[j]:8s}: " + " > ".join(f"{d}({results[(j,d)]['mean']:+.2f})" for d in ranked))

# Per-dim mean across 4 judges  (signed)
print("\n=== per-dim mean across 4 judges (signed) ===")
for d in DIMS:
    vals = [results[(j,d)]["mean"] for j in JUDGES]
    print(f"  {d:24s}: mean={sum(vals)/4:+.3f}  range [{min(vals):+.2f}, {max(vals):+.2f}]")

# Save
import json
out = {}
for (j,d),v in results.items():
    out.setdefault(j,{})[d] = v
with open("experiments/replication-wave/results/master_c1_per_dimension.json","w") as f:
    json.dump(out, f, indent=2)

# CSV
with open("experiments/replication-wave/results/master_c1_per_dimension.csv","w",newline="") as f:
    w = csv.writer(f)
    w.writerow(["judge"] + DIMS)
    for j in JUDGES:
        w.writerow([SHORT[j]] + [f"{results[(j,d)]['mean']:+.4f}" for d in DIMS])
    w.writerow(["judge"] + [f"{d}_ci_low" for d in DIMS])
    for j in JUDGES:
        w.writerow([SHORT[j]] + [f"{results[(j,d)]['lo']:+.4f}" for d in DIMS])
    w.writerow(["judge"] + [f"{d}_ci_high" for d in DIMS])
    for j in JUDGES:
        w.writerow([SHORT[j]] + [f"{results[(j,d)]['hi']:+.4f}" for d in DIMS])

print("\nwrote master_c1_per_dimension.{csv,json}")
