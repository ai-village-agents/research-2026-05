#!/usr/bin/env python3
"""Generate data for a radar/spider chart comparing C1, C2, and C3 gaps.

This script calculates the per-dimension self-preference gaps for each
condition (C1, C2, C3) and formats them into a CSV suitable for plotting
a radar chart in the final blog post or presentation.
"""

import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCORES_CSV = RESULTS / "long_scores.csv"

def main():
    if not SCORES_CSV.exists():
        print(f"Scores file not found: {SCORES_CSV}")
        return
        
    df = pd.read_csv(SCORES_CSV)
    
    # We care about C1, C2, and C3
    df = df[df["condition"].str.lower().isin(["c1", "c2", "c3"])].copy()
    
    dims = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
    
    rows = []
    
    for judge in df["judge"].unique():
        judge_df = df[df["judge"] == judge]
        
        for cond in ["c1", "c2", "c3"]:
            cond_df = judge_df[judge_df["condition"].str.lower() == cond]
            
            if cond_df.empty:
                continue
                
            self_df = cond_df[cond_df["author"] == judge]
            other_df = cond_df[cond_df["author"] != judge]
            
            row = {
                "judge": judge,
                "condition": cond.upper()
            }
            
            for dim in dims:
                self_mean = self_df[dim].mean() if not self_df.empty else np.nan
                other_mean = other_df[dim].mean() if not other_df.empty else np.nan
                row[dim + "_gap"] = self_mean - other_mean
                
            rows.append(row)
            
    radar_df = pd.DataFrame(rows)
    output_path = RESULTS / "radar_chart_data.csv"
    radar_df.to_csv(output_path, index=False)
    
    print(f"Wrote radar chart data to {output_path}")
    print("\nSample Data:")
    print(radar_df.head())

if __name__ == "__main__":
    main()
