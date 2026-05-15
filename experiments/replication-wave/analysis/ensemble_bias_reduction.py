import csv
import itertools
import random
import os
from pathlib import Path

# Seed for reproducibility
random.seed(42)

REPO = Path.home() / "research-2026-05"
CSV_IN = REPO / "experiments" / "replication-wave" / "results" / "long_scores.csv"
RESULTS_DIR = REPO / "experiments" / "replication-wave" / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

B_BOOT = 2000

JUDGES = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
AUTHORS = JUDGES  # same set
DIMS = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]

def read_data():
    rows = []
    with open(CSV_IN, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r.get("condition", "").strip().lower() != "c1":
                continue
            # strip \r from keys/values due to Windows line endings
            r = {k.strip("\r"): v.strip("\r") for k, v in r.items()}
            r["composite"] = sum(float(r[d]) for d in DIMS) / len(DIMS)
            rows.append(r)
    return rows

def compute_bias_for_panel(panel, data):
    """
    panel: tuple of judge names (the judges IN the panel)
    Returns: dict with keys:
      - overall_bias = mean(composite | author in panel) - mean(composite | author not in panel)
      - self_mean = mean(composite | author in panel)
      - peer_mean = mean(composite | author not in panel)
      - n_self, n_peer
    """
    panel_set = set(panel)
    self_scores = []
    peer_scores = []
    for r in data:
        if r["judge"] not in panel_set:
            continue
        if r["author"] in panel_set:
            self_scores.append(float(r["composite"]))
        else:
            peer_scores.append(float(r["composite"]))
    if not self_scores or not peer_scores:
        return None
    self_mean = sum(self_scores) / len(self_scores)
    peer_mean = sum(peer_scores) / len(peer_scores)
    return {
        "overall_bias": self_mean - peer_mean,
        "self_mean": self_mean,
        "peer_mean": peer_mean,
        "n_self": len(self_scores),
        "n_peer": len(peer_scores),
    }

def compute_k4_self_influence(data):
    """
    For the full 4-judge panel, compute self-influence:
      mean(full_panel_mean - leave_author_out_mean)
    Each response has 4 ratings (one per judge). Full mean = mean of 4.
    Leave-author-out mean = mean of the 3 judges who are NOT the author.
    """
    # Group by (prompt_id, author) -> list of (judge, composite)
    groups = {}
    for r in data:
        key = (r["prompt_id"], r["author"])
        groups.setdefault(key, []).append((r["judge"], float(r["composite"])))
    diffs = []
    for key, vals in groups.items():
        if len(vals) != 4:
            continue
        prompt_id, author = key
        full_mean = sum(v for _, v in vals) / 4
        # leave out the author's own rating
        others = [v for j, v in vals if j != author]
        if len(others) == 3:
            leave_mean = sum(others) / 3
            diffs.append(full_mean - leave_mean)
    if not diffs:
        return None
    return sum(diffs) / len(diffs)

def bootstrap_panels(data, B=2000):
    """
    Response-level bootstrap: resample the set of unique responses with replacement.
    A response is identified by (prompt_id, author).
    We keep all 4 judge rows for each sampled response.
    """
    # Unique responses
    unique = {}
    for r in data:
        key = (r["prompt_id"], r["author"])
        unique.setdefault(key, []).append(r)
    keys = list(unique.keys())
    n = len(keys)
    # Precompute panel stats for each bootstrap sample
    # k=1,2,3 panels
    panels_k = {}
    for k in [1, 2, 3]:
        panels_k[k] = list(itertools.combinations(JUDGES, k))
    # Storage: k -> list of panel biases per bootstrap
    boot_stats = {k: {tuple(p): [] for p in panels_k[k]} for k in [1, 2, 3]}
    boot_k4 = []
    for _ in range(B):
        # Resample responses
        sampled_keys = [random.choice(keys) for _ in range(n)]
        boot_data = []
        for key in sampled_keys:
            boot_data.extend(unique[key])
        for k in [1, 2, 3]:
            for panel in panels_k[k]:
                res = compute_bias_for_panel(panel, boot_data)
                if res:
                    boot_stats[k][tuple(panel)].append(res["overall_bias"])
        k4 = compute_k4_self_influence(boot_data)
        if k4 is not None:
            boot_k4.append(k4)
    return boot_stats, boot_k4

def ci(vals, alpha=0.05):
    if not vals:
        return (float('nan'), float('nan'))
    sorted_vals = sorted(vals)
    n = len(sorted_vals)
    lo_idx = int(alpha / 2 * n)
    hi_idx = int((1 - alpha / 2) * n)
    # ensure bounds
    lo_idx = max(0, lo_idx)
    hi_idx = min(n - 1, hi_idx)
    return (sorted_vals[lo_idx], sorted_vals[hi_idx])

def main():
    data = read_data()
    print(f"Loaded {len(data)} C1 rows")
    # Verify structure
    groups = {}
    for r in data:
        key = (r["prompt_id"], r["author"])
        groups.setdefault(key, [])
        groups[key].append(r["judge"])
    print(f"Unique responses: {len(groups)}")
    # Point estimates
    panels_k = {}
    for k in [1, 2, 3]:
        panels_k[k] = list(itertools.combinations(JUDGES, k))
    print("\n=== Point Estimates ===")
    results_rows = []
    for k in [1, 2, 3]:
        biases = []
        for panel in panels_k[k]:
            res = compute_bias_for_panel(panel, data)
            if res:
                biases.append(res["overall_bias"])
                print(f"k={k} panel={panel} bias={res['overall_bias']:+.4f} "
                      f"self_mean={res['self_mean']:.4f} peer_mean={res['peer_mean']:.4f} "
                      f"n_self={res['n_self']} n_peer={res['n_peer']}")
                results_rows.append({
                    "panel_size": k,
                    "panel": " + ".join(panel),
                    "bias": round(res["overall_bias"], 4),
                    "self_mean": round(res["self_mean"], 4),
                    "peer_mean": round(res["peer_mean"], 4),
                    "n_self": res["n_self"],
                    "n_peer": res["n_peer"],
                    "ci_lower": "",
                    "ci_upper": "",
                })
        if biases:
            print(f"k={k} mean bias across panels: {sum(biases)/len(biases):+.4f}")
    k4 = compute_k4_self_influence(data)
    print(f"\nk=4 self-influence (full - leave-out): {k4:+.4f}")
    results_rows.append({
        "panel_size": 4,
        "panel": "All 4",
        "bias": round(k4, 4),
        "self_mean": "",
        "peer_mean": "",
        "n_self": "",
        "n_peer": "",
        "ci_lower": "",
        "ci_upper": "",
    })

    print(f"\n=== Bootstrap (B={B_BOOT}) ===")
    boot_stats, boot_k4 = bootstrap_panels(data, B=B_BOOT)
    for k in [1, 2, 3]:
        for panel in panels_k[k]:
            vals = boot_stats[k][tuple(panel)]
            if vals:
                lo, hi = ci(vals)
                print(f"k={k} panel={panel} bias CI: [{lo:+.4f}, {hi:+.4f}]")
                # update the corresponding row
                for row in results_rows:
                    if row["panel_size"] == k and row["panel"] == " + ".join(panel):
                        row["ci_lower"] = round(lo, 4)
                        row["ci_upper"] = round(hi, 4)
    if boot_k4:
        lo4, hi4 = ci(boot_k4)
        print(f"k=4 self-influence CI: [{lo4:+.4f}, {hi4:+.4f}]")
        for row in results_rows:
            if row["panel_size"] == 4:
                row["ci_lower"] = round(lo4, 4)
                row["ci_upper"] = round(hi4, 4)

    # Also compute mean bias per k with CI
    print("\n=== Mean Bias per Panel Size ===")
    summary_rows = []
    for k in [1, 2, 3]:
        panel_biases = []
        for panel in panels_k[k]:
            res = compute_bias_for_panel(panel, data)
            if res:
                panel_biases.append(res["overall_bias"])
        # Bootstrap for mean bias: average across panels for each bootstrap
        mean_boot = []
        for b in range(B_BOOT):
            vals = []
            for panel in panels_k[k]:
                bb = boot_stats[k][tuple(panel)]
                if len(bb) > b:
                    vals.append(bb[b])
            if vals:
                mean_boot.append(sum(vals) / len(vals))
        if panel_biases and mean_boot:
            mean_point = sum(panel_biases) / len(panel_biases)
            lo, hi = ci(mean_boot)
            print(f"k={k} mean bias = {mean_point:+.4f} [{lo:+.4f}, {hi:+.4f}]")
            summary_rows.append({
                "panel_size": k,
                "mean_bias": round(mean_point, 4),
                "ci_lower": round(lo, 4),
                "ci_upper": round(hi, 4),
                "n_panels": len(panel_biases),
            })
    if boot_k4:
        mean_point = k4
        lo, hi = ci(boot_k4)
        print(f"k=4 self-influence = {mean_point:+.4f} [{lo:+.4f}, {hi:+.4f}]")
        summary_rows.append({
            "panel_size": 4,
            "mean_bias": round(mean_point, 4),
            "ci_lower": round(lo, 4),
            "ci_upper": round(hi, 4),
            "n_panels": 1,
        })

    # Write CSV
    csv_path = RESULTS_DIR / "ensemble_bias_reduction.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "panel_size", "panel", "bias", "self_mean", "peer_mean",
            "n_self", "n_peer", "ci_lower", "ci_upper"
        ])
        writer.writeheader()
        writer.writerows(results_rows)
    print(f"\nWrote {csv_path}")

    summary_csv = RESULTS_DIR / "ensemble_bias_reduction_summary.csv"
    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "panel_size", "mean_bias", "ci_lower", "ci_upper", "n_panels"
        ])
        writer.writeheader()
        writer.writerows(summary_rows)
    print(f"Wrote {summary_csv}")

    # Write Markdown
    md_path = RESULTS_DIR / "ensemble_bias_reduction.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Ensemble Bias Reduction Analysis\n\n")
        f.write("**Condition:** C1 (blind baseline, replication wave)\n\n")
        f.write("**Method:** For panel sizes k=1,2,3, enumerate all C(4,k) judge panels. "
                 "For each panel, *self* = responses where the author is a member of the panel; "
                 "*peer* = responses where the author is NOT a member. "
                 "Bias = mean(composite | self) − mean(composite | peer). "
                 "For k=4, self-influence = mean(full-panel mean − leave-author-out mean). "
                 "Bootstrap B=2000 with response-level resampling.\n\n")
        f.write("## Per-Panel Results\n\n")
        f.write("| Panel Size | Panel | Bias | Self Mean | Peer Mean | n_self | n_peer | 95% CI |\n")
        f.write("|-----------|-------|------|-----------|-----------|--------|--------|--------|\n")
        for row in results_rows:
            ci_str = f"[{row['ci_lower']}, {row['ci_upper']}]" if row.get("ci_lower") != "" else "—"
            f.write(f"| {row['panel_size']} | {row['panel']} | {row['bias']:+.4f} | "
                    f"{row['self_mean'] if row['self_mean'] != '' else '—'} | "
                    f"{row['peer_mean'] if row['peer_mean'] != '' else '—'} | "
                    f"{row['n_self'] if row['n_self'] != '' else '—'} | "
                    f"{row['n_peer'] if row['n_peer'] != '' else '—'} | {ci_str} |\n")
        f.write("\n## Summary by Panel Size\n\n")
        f.write("| Panel Size | Mean Bias | 95% CI | n_panels |\n")
        f.write("|-----------|-----------|--------|----------|\n")
        for row in summary_rows:
            f.write(f"| {row['panel_size']} | {row['mean_bias']:+.4f} | "
                    f"[{row['ci_lower']}, {row['ci_upper']}] | {row['n_panels']} |\n")
        f.write("\n## Interpretation\n\n")
        f.write("- **k=1 (single judge):** Each judge rating their own work vs peers. "
                 "This is the raw individual self-preference.\n")
        f.write("- **k=2 and k=3:** As the panel grows, the self-author is diluted among peers. "
                 "If self-preference is purely individual and uncorrelated, the panel bias should shrink. "
                 "If it persists, it suggests shared in-group favoritism.\n")
        f.write("- **k=4 (full panel):** Self-influence measures how much the author's own rating "
                 "raises the panel consensus. Even a full panel retains a residual self-bias "
                 "because the author is still one of the raters.\n")
        f.write("- **Dilution check:** Bias should decline monotonically with k if self-preference is idiosyncratic.\n")
    print(f"Wrote {md_path}")
    print("\nDone.")

if __name__ == "__main__":
    main()
