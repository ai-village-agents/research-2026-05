"""
Post-hoc power analysis for the 16 master claims.

For each claim we have a point estimate `est`, a 95% bootstrap CI, and an N.
Approximating bootstrap SE = (CI_high - CI_low) / (2 * 1.96), we report:

- observed z = est / SE
- observed power at alpha=0.05 two-sided
- N required to reach 80% power assuming the observed effect size and cluster
  variance scaling as ~1/sqrt(N)

Caveats:
- This is *retrospective* power, used here only as a planning aid for future
  replications. It is well known that post-hoc power computed from the same
  data has limitations (e.g. Hoenig & Heisey 2001) — we present it as a
  rough cell-size guide rather than as inferential evidence.
- We do not adjust for cluster correlation explicitly; bootstrap SEs already
  incorporate the prompt-cluster variance of our published estimates, so the
  scaling 1/sqrt(N) refers to "1/sqrt(prompt-clusters)" not "1/sqrt(rows)".
"""
import csv, math

ALPHA = 0.05
POWER_TARGET = 0.80
Z_ALPHA = 1.96     # two-sided 0.05
Z_BETA  = 0.842    # for 0.80 power

def norm_cdf(z):
    return 0.5 * (1 + math.erf(z/math.sqrt(2)))

def observed_power(z):
    # two-sided z-test power at alpha=0.05
    return norm_cdf(abs(z) - Z_ALPHA) + norm_cdf(-abs(z) - Z_ALPHA)

with open("experiments/replication-wave/results/master_claims_multiplicity_rebootstrap.csv") as f:
    rows = list(csv.DictReader(f))

rows_out = [["family","claim","est","ci_low","ci_high","n","se","obs_z","obs_power","n_for_80pct"]]
print(f"\n{'Claim':55s} {'est':>7s}  {'se':>6s}  {'obs_z':>6s}  {'obs_pwr':>7s}  {'N_obs':>6s} {'N_req_80%':>10s}")
print("-"*110)
for r in rows:
    est = float(r["est"]); lo = float(r["ci_low"]); hi = float(r["ci_high"])
    n   = float(r["n"]) if r["n"] else 0.0
    se = (hi - lo) / (2 * Z_ALPHA)
    if se <= 0:
        z = float("inf"); op = 1.0; nreq = 0.0
    else:
        z = est / se
        op = observed_power(z)
        if abs(z) > 0:
            ratio = (Z_ALPHA + Z_BETA) / abs(z)
            nreq = (n * ratio**2) if n>0 else float("nan")
        else:
            nreq = float("inf")
    claim = r["claim"][:53]
    print(f"{claim:55s} {est:+7.3f}  {se:6.3f}  {z:+6.2f}  {op:7.3f}  {n:6.0f}  {nreq:10.1f}")
    rows_out.append([r["family"], r["claim"], f"{est:.4f}", f"{lo:.4f}", f"{hi:.4f}",
                     f"{n:.0f}", f"{se:.4f}", f"{z:.3f}", f"{op:.3f}", f"{nreq:.1f}"])

with open("experiments/replication-wave/results/master_claims_power.csv","w",newline="") as f:
    w = csv.writer(f); w.writerows(rows_out)
print("\nWrote master_claims_power.csv")
