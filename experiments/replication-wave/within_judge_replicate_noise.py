"""
Compute within-judge replicate noise floor from the D408 label-swap data.

For each (judge, original_response) cell, the label-swap experiment provides
4 scored replicates that differ ONLY in the displayed author label. Since
the displayed-label ATE is ≈ 0 (see results/label_swap_analysis.md), the SD
across those 4 replicates is a clean estimate of within-judge sampling noise,
independent of any between-judge signal.

Outputs a Markdown table plus pooled statistics. Run after analyze_label_swap.py
has populated label_swap_long.csv.
"""
import csv
import statistics
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).parent
LONG = HERE / 'results' / 'label_swap_long.csv'

def main():
    rows = list(csv.DictReader(open(LONG)))
    cells = defaultdict(list)
    for r in rows:
        cells[(r['judge'], r['original_blind_id'])].append(float(r['composite_score']))
    # Sanity check: every cell has 4 reps
    sizes = [len(v) for v in cells.values()]
    assert min(sizes) == max(sizes) == 4, f"Unexpected cell sizes: {set(sizes)}"

    print(f"# Within-judge replicate noise floor (D408 label-swap data)\n")
    print(f"Loaded {len(rows)} scored rows; {len(cells)} (judge, response) cells, all 4-rep.\n")
    print(f"## Per-judge SD distribution across 4 displayed-label replicates\n")
    print(f"| judge | n_cells | mean SD | median SD | min SD | max SD | n cells w/ SD=0 | n cells w/ SD<0.1 |")
    print(f"|---|---:|---:|---:|---:|---:|---:|---:|")
    all_sds = []
    for judge in sorted(set(r['judge'] for r in rows)):
        sds = [statistics.stdev(v) for k, v in cells.items() if k[0] == judge]
        all_sds.extend(sds)
        zero = sum(1 for s in sds if s == 0)
        near = sum(1 for s in sds if s < 0.1)
        print(f"| {judge} | {len(sds)} | {statistics.mean(sds):.3f} | "
              f"{statistics.median(sds):.3f} | {min(sds):.3f} | {max(sds):.3f} | "
              f"{zero}/{len(sds)} | {near}/{len(sds)} |")
    print(f"\nPooled mean within-judge SD: **{statistics.mean(all_sds):.3f}** composite points "
          f"(median {statistics.median(all_sds):.3f}, n={len(all_sds)} cells).")

if __name__ == '__main__':
    main()
