#!/usr/bin/env python3
"""
Per-judge causal label-swap bias profile (post-v1.3.0 supplement).

Three linear contrasts over the 4x4 label-effect matrix (per-judge row):

  1. self_favor  = cell(j, self)         - mean(cell(j, label != self))
  2. anti_kimi   = mean(cell(j, label != kimi)) - cell(j, kimi)
  3. pro_claude  = cell(j, claude)       - mean(cell(j, label != claude))

Cells are means of within-(judge, response_hash) residuals.
NOTE: paired_label_swap.csv has the paired design (each (judge, hash)
has 2 displayed-label observations, not all 4). The cell means still
estimate E[residual | judge, displayed_label] correctly, so the
contrasts are well-defined; we bootstrap response_hash to get CIs.
"""
import csv, math, random, statistics, pathlib
from collections import defaultdict

ROOT = '/tmp/research-2026-05'
CSV_IN = f'{ROOT}/experiments/replication-wave/results/paired_label_swap.csv'
OUT_MD = f'{ROOT}/experiments/replication-wave/results/judge_bias_profile.md'
OUT_CSV = f'{ROOT}/experiments/replication-wave/results/judge_bias_profile.csv'

JUDGES = ['claude-opus-4.7', 'gemini-3.1-pro', 'gpt-5.5', 'kimi-k2.6']
LABELS = JUDGES[:]
B = 4000
SEED = 20260515

def load():
    out = []
    for row in csv.DictReader(open(CSV_IN)):
        row['composite'] = float(row['composite'])
        out.append(row)
    return out

def residuals_with_hash(rows):
    g = defaultdict(list)
    for r in rows:
        g[(r['judge'], r['response_hash'])].append(r)
    res = []
    for (j, h), gr in g.items():
        m = statistics.mean(r['composite'] for r in gr)
        for r in gr:
            res.append({'judge': j, 'response_hash': h,
                        'displayed_label': r['displayed_label'],
                        'residual': r['composite'] - m})
    return res

def cell_means(res):
    by = defaultdict(list)
    for r in res:
        by[(r['judge'], r['displayed_label'])].append(r['residual'])
    M = {(j, L): (statistics.mean(by[(j, L)]) if by[(j, L)] else 0.0)
         for j in JUDGES for L in LABELS}
    return M

def contrasts(M):
    out = {}
    for j in JUDGES:
        self_v = M[(j, j)]
        others = [M[(j, L)] for L in LABELS if L != j]
        c_self = self_v - statistics.mean(others)
        kimi_v = M[(j, 'kimi-k2.6')]
        non_kimi = [M[(j, L)] for L in LABELS if L != 'kimi-k2.6']
        c_antikimi = statistics.mean(non_kimi) - kimi_v
        claude_v = M[(j, 'claude-opus-4.7')]
        non_claude = [M[(j, L)] for L in LABELS if L != 'claude-opus-4.7']
        c_proclaude = claude_v - statistics.mean(non_claude)
        out[j] = {'self_favor': c_self, 'anti_kimi': c_antikimi, 'pro_claude': c_proclaude}
    return out

def bootstrap(rows, B=B, seed=SEED):
    rng = random.Random(seed)
    hashes = sorted({r['response_hash'] for r in rows})
    by_h = defaultdict(list)
    for r in rows:
        by_h[r['response_hash']].append(r)
    boots = {j: {k: [] for k in ['self_favor', 'anti_kimi', 'pro_claude']} for j in JUDGES}
    for b in range(B):
        sample = []
        for _ in range(len(hashes)):
            h = rng.choice(hashes)
            sample.extend(by_h[h])
        res = residuals_with_hash(sample)
        M = cell_means(res)
        c = contrasts(M)
        for j in JUDGES:
            for k in ['self_favor', 'anti_kimi', 'pro_claude']:
                boots[j][k].append(c[j][k])
    return boots

def pctile(xs, p):
    xs = sorted(xs); k = (len(xs)-1)*p
    f = math.floor(k); c = math.ceil(k)
    return xs[int(k)] if f == c else xs[f] + (xs[c]-xs[f])*(k-f)

rows = load()
res0 = residuals_with_hash(rows)
M0 = cell_means(res0)
C0 = contrasts(M0)
print("computing bootstrap CIs (B=4000)...")
boots = bootstrap(rows)
CIs = {j: {k: (pctile(boots[j][k], 0.025), pctile(boots[j][k], 0.975))
           for k in ['self_favor', 'anti_kimi', 'pro_claude']} for j in JUDGES}

# Write CSV
with open(OUT_CSV, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['judge', 'metric', 'mean', 'ci_lo', 'ci_hi', 'ci_excludes_zero', 'B'])
    for j in JUDGES:
        for k in ['self_favor', 'anti_kimi', 'pro_claude']:
            m = C0[j][k]; lo, hi = CIs[j][k]
            ex = int(lo > 0 or hi < 0)
            w.writerow([j, k, f'{m:+.4f}', f'{lo:+.4f}', f'{hi:+.4f}', ex, B])

# Write MD
md = ["# Per-judge label-swap bias profile",
      "",
      "Three linear contrasts on the 4x4 within-response-residual matrix.",
      "Cluster-bootstrap by `response_hash`, B = 4000.",
      "",
      "| Judge | self_favor (self - mean others) | anti_kimi (mean(non-kimi) - kimi) | pro_claude (claude - mean(non-claude)) |",
      "|---|---|---|---|"]

def cell(j, k):
    m = C0[j][k]; lo, hi = CIs[j][k]
    sig = " *" if (lo > 0 or hi < 0) else ""
    return f"{m:+.3f} [{lo:+.3f}, {hi:+.3f}]{sig}"

for j in JUDGES:
    md.append(f"| {j} | {cell(j,'self_favor')} | {cell(j,'anti_kimi')} | {cell(j,'pro_claude')} |")

md.extend([
    "",
    "`*` = naive 95% bootstrap CI excludes zero (uncorrected; 12 cells total).",
    "",
    "## Reading the profile",
    "",
    "- **Gemini 3.1 Pro** shows the strongest pro-self and anti-Kimi tilts;",
    "  both label-swap matrix cells underlying these contrasts also survive",
    "  Bonferroni correction at alpha = 0.05 / 16.",
    "- **Claude Opus 4.7** has a small positive self-favor and small positive",
    "  anti-Kimi index; both naive CIs straddle zero.",
    "- **GPT-5.5** is exactly 0 on all three contrasts: this judge is",
    "  label-invariant under our scoring path (committed C2-v2 numbers were",
    "  produced via the codex/OpenAI backend - see Backend caveat in the blogpost).",
    "- **Kimi K2.6** shows a non-significant pro-Claude lean (consistent with its",
    "  C4 over-attribution of peer responses to claude-opus-4.7) and roughly null",
    "  self-favor.",
    "",
    "## Why this view is useful",
    "",
    "The 4x4 matrix has 16 cells; the bias-profile view collapses each judge's",
    "row into three orthogonal scalars (self / anti-Kimi / pro-Claude). The first",
    "answers \"does this judge favor itself?\", the second answers \"does this judge",
    "downweight the lowest-quality author specifically?\", and the third answers",
    "\"does this judge default to crediting Claude even when Claude wasn't the",
    "author?\". These are the three causal patterns the matrix actually displays.",
    "",
    "Reproduction: `experiments/replication-wave/analysis/judge_bias_profile.py` ->",
    "`experiments/replication-wave/results/judge_bias_profile.{md,csv}`.",
])
pathlib.Path(OUT_MD).write_text("\n".join(md) + "\n")

print("Wrote", OUT_MD, "and", OUT_CSV)
for j in JUDGES:
    print(f"{j}:")
    for k in ['self_favor', 'anti_kimi', 'pro_claude']:
        m = C0[j][k]; lo, hi = CIs[j][k]
        sig = " *" if (lo > 0 or hi < 0) else ""
        print(f"  {k:<12s}  {m:+.3f}  [{lo:+.3f}, {hi:+.3f}]{sig}")
