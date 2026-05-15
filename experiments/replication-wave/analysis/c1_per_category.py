"""
Per-category C1 self-preference breakdown (10 categories × 4 judges).

Question: Does the C1 observational self-preference bias concentrate in
particular task types, or is it diffuse across categories?

Method:
- For each (judge, prompt) in c1, compute self_score - mean(other 3 authors).
- Since each category has exactly 1 prompt, this gives 4×10 point matrix.
- Cluster-bootstrap over prompts (B=4000) to get per-judge means with 95% CI
  and per-category-collapsed-across-judges means with 95% CI.
- Also report sign agreement and concentration index across categories.
"""
import csv, json, math, random
from collections import defaultdict
random.seed(11_15_409)

DIMS = ["correctness","completeness","clarity","creativity","constraint_adherence"]
JUDGES = ["claude-opus-4.7","gemini-3.1-pro","gpt-5.5","kimi-k2.6"]

rows=[]
with open("experiments/replication-wave/results/long_scores.csv") as f:
    for r in csv.DictReader(f):
        rows.append(r)

# Build composite per (judge, author, prompt, category, condition)
def comp(r):
    return sum(int(r[d]) for d in DIMS)/5.0

# Filter to c1
c1 = [r for r in rows if r["condition"]=="c1"]

# For each (judge, prompt) collect 4-author scores
cells = defaultdict(dict)   # (judge,prompt) -> author -> composite
cat_of = {}
for r in c1:
    j=r["judge"]; a=r["author"]; p=r["prompt_id"]; c=r["category"]
    cells[(j,p)][a]=comp(r)
    cat_of[p]=c

# Per (judge, prompt) compute self-pref = score(self) - mean(others)
sp = {}  # (judge, prompt) -> sp
for (j,p), d in cells.items():
    if j in d and len(d)==4:
        others=[v for a,v in d.items() if a!=j]
        sp[(j,p)] = d[j] - sum(others)/len(others)

# 4×10 matrix
prompts = sorted({p for (_,p) in sp.keys()})
print("prompts:", prompts)
M = {(j,p): sp.get((j,p), None) for j in JUDGES for p in prompts}

# Cluster-bootstrap over prompts: per-judge mean across 10 cats
B=4000
boot_judge = {j: [] for j in JUDGES}
boot_cat   = {p: [] for p in prompts}  # mean across 4 judges per cat
for b in range(B):
    sample = [random.choice(prompts) for _ in range(len(prompts))]
    for j in JUDGES:
        vals=[M[(j,p)] for p in sample if M[(j,p)] is not None]
        if vals: boot_judge[j].append(sum(vals)/len(vals))
    for p in prompts:
        vals=[M[(j,p)] for j in JUDGES if M[(j,p)] is not None]
        if vals: boot_cat[p].append(sum(vals)/len(vals))

def ci(xs):
    xs=sorted(xs)
    n=len(xs)
    return xs[int(0.025*n)], xs[int(0.975*n)]

# Per-judge means + CI
judge_summary = {}
for j in JUDGES:
    vals=[M[(j,p)] for p in prompts if M[(j,p)] is not None]
    mean=sum(vals)/len(vals)
    lo,hi=ci(boot_judge[j])
    judge_summary[j]={"mean":mean,"ci":[lo,hi],"n":len(vals)}

# Per-category mean across 4 judges + CI
cat_summary = {}
for p in prompts:
    vals=[M[(j,p)] for j in JUDGES if M[(j,p)] is not None]
    mean=sum(vals)/len(vals)
    lo,hi=ci(boot_cat[p])
    cat_summary[p]={"category":cat_of[p],"mean":mean,"ci":[lo,hi],"n":len(vals)}

# Sign agreement: in how many categories do all 4 judges agree on sign?
def sign(x): return 1 if x>0 else (-1 if x<0 else 0)
agree4=0; agree3=0
for p in prompts:
    signs=[sign(M[(j,p)]) for j in JUDGES]
    nonzero=[s for s in signs if s!=0]
    if len(set(nonzero))<=1: 
        if len(nonzero)>=3: agree4 += 1  # all (nonzero) agree
    elif sum(1 for s in nonzero if s==max(set(nonzero), key=nonzero.count)) >= 3:
        agree3 += 1

# Concentration: Gini-like across categories per judge
def gini_abs(vals):
    vals=sorted(abs(v) for v in vals)
    n=len(vals); s=sum(vals)
    if s==0: return 0.0
    cum=0; gini=0
    for i,v in enumerate(vals,1):
        cum+=v
        gini += (2*i-n-1)*v
    return gini/(n*s)

judge_conc = {j: gini_abs([M[(j,p)] for p in prompts if M[(j,p)] is not None]) for j in JUDGES}

# Save full table
short = {"claude-opus-4.7":"Claude","gemini-3.1-pro":"Gemini","gpt-5.5":"GPT","kimi-k2.6":"Kimi"}
header=["category","prompt_id"]+[short[j] for j in JUDGES]+["mean_4J","mean_4J_ci_low","mean_4J_ci_high"]
out_rows=[header]
for p in prompts:
    cs=cat_summary[p]
    row=[cs["category"],p]
    for j in JUDGES:
        v=M[(j,p)]
        row.append(f"{v:+.3f}" if v is not None else "")
    row += [f"{cs['mean']:+.3f}", f"{cs['ci'][0]:+.3f}", f"{cs['ci'][1]:+.3f}"]
    out_rows.append(row)
# Add per-judge means row
last=["overall (mean across 10 cats)",""]
for j in JUDGES:
    s=judge_summary[j]
    last.append(f"{s['mean']:+.3f} [{s['ci'][0]:+.3f},{s['ci'][1]:+.3f}]")
last += ["","",""]
out_rows.append(last)

out_csv=[header]
for p in prompts:
    cs=cat_summary[p]
    row=[cs["category"],p]
    for j in JUDGES:
        v=M[(j,p)]
        row.append(f"{v:.4f}" if v is not None else "")
    row += [f"{cs['mean']:.4f}", f"{cs['ci'][0]:.4f}", f"{cs['ci'][1]:.4f}"]
    out_csv.append(row)
out_csv.append(["per_judge_mean_4J_collapsed","",
                f"{judge_summary[JUDGES[0]]['mean']:.4f}",
                f"{judge_summary[JUDGES[1]]['mean']:.4f}",
                f"{judge_summary[JUDGES[2]]['mean']:.4f}",
                f"{judge_summary[JUDGES[3]]['mean']:.4f}", "","",""])

# Print summary
print("\n=== per-judge C1 self-pref (across 10 categories) ===")
for j in JUDGES:
    s=judge_summary[j]
    print(f"  {short[j]:8s}: {s['mean']:+.3f} [{s['ci'][0]:+.3f}, {s['ci'][1]:+.3f}]  (Gini |x| concentration = {judge_conc[j]:.3f})")

print("\n=== per-category mean (across 4 judges) ===")
for p in sorted(prompts, key=lambda p: cat_summary[p]['mean'], reverse=True):
    cs=cat_summary[p]
    print(f"  {cs['category']:12s}: {cs['mean']:+.3f} [{cs['ci'][0]:+.3f}, {cs['ci'][1]:+.3f}]  (judges: " 
          + ", ".join(f"{short[j]}={M[(j,p)]:+.2f}" for j in JUDGES) + ")")

# Save CSV
with open("experiments/replication-wave/results/master_c1_per_category.csv","w",newline="") as f:
    w=csv.writer(f); w.writerows(out_csv)

# Save JSON
with open("experiments/replication-wave/results/master_c1_per_category.json","w") as f:
    json.dump({"judges":judge_summary,"categories":cat_summary,
               "gini_concentration":judge_conc,
               "matrix":{f"{j}|{p}": M[(j,p)] for (j,p) in M}},f,indent=2)

print("\nWrote master_c1_per_category.{csv,json}")
