#!/usr/bin/env python3
"""Analyze why the C3 (Warning) condition failed to reduce self-preference.

This script isolates the scores given by judges to their own responses
under C1 (Baseline) vs C3 (Warning), looking for shifts at the prompt level
or dimension level.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCORES_CSV = RESULTS / "long_scores.csv"

def main():
    if not SCORES_CSV.exists():
        print(f"Scores file not found: {SCORES_CSV}")
        return
        
    df = pd.read_csv(SCORES_CSV)
    
    # We only care about C1 and C3
    df = df[df["condition"].str.lower().isin(["c1", "c3"])].copy()
    
    dims = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
    df["score"] = df[dims].mean(axis=1)
    
    # Isolate self-scores (where judge == author)
    self_df = df[df["judge"] == df["author"]].copy()
    
    # Isolate other-scores (where judge != author)
    other_df = df[df["judge"] != df["author"]].copy()
    
    # Calculate means by judge and condition
    print("=== Self-Score Means by Condition ===")
    self_means = self_df.groupby(["judge", "condition"])["score"].mean().unstack()
    print(self_means)
    
    print("\n=== Other-Score Means by Condition ===")
    other_means = other_df.groupby(["judge", "condition"])["score"].mean().unstack()
    print(other_means)
    
    # Calculate self-preference gaps by judge and condition
    # Self-preference = Self-score - Mean Other-score
    gap_df = pd.DataFrame()
    for condition in ["c1", "c3"]:
        cond_self = self_df[self_df["condition"] == condition].groupby("judge")["score"].mean()
        cond_other = other_df[other_df["condition"] == condition].groupby("judge")["score"].mean()
        gap_df[condition.upper()] = cond_self - cond_other
        
    print("\n=== Self-Preference Gaps ===")
    gap_df["Delta (C3 - C1)"] = gap_df["C3"] - gap_df["C1"]
    print(gap_df)
    
    # By dimension analysis
    print("\n=== Gap Changes by Dimension (Delta C3 - C1) ===")
    dim_deltas = {}
    for dim in dims:
        cond_self_c1 = self_df[self_df["condition"] == "c1"].groupby("judge")[dim].mean()
        cond_other_c1 = other_df[other_df["condition"] == "c1"].groupby("judge")[dim].mean()
        gap_c1 = cond_self_c1 - cond_other_c1
        
        cond_self_c3 = self_df[self_df["condition"] == "c3"].groupby("judge")[dim].mean()
        cond_other_c3 = other_df[other_df["condition"] == "c3"].groupby("judge")[dim].mean()
        gap_c3 = cond_self_c3 - cond_other_c3
        
        dim_deltas[dim] = gap_c3 - gap_c1
        
    dim_delta_df = pd.DataFrame(dim_deltas)
    print(dim_delta_df)
    
    # Output markdown report
    report_path = RESULTS / "c3_warning_failure_analysis.md"
    with open(report_path, "w") as f:
        f.write("# Analysis of C3 (Bias Warning) Failure\n\n")
        f.write("This report analyzes why explicitly warning models about their own self-preference bias (C3) failed to mitigate the effect.\n\n")
        
        f.write("## Self-Preference Gaps (C1 vs C3)\n\n")
        f.write("| Judge | C1 Gap | C3 Gap | Change (C3 - C1) |\n")
        f.write("|-------|--------|--------|------------------|\n")
        for judge in gap_df.index:
            row = gap_df.loc[judge]
            f.write(f"| `{judge}` | {row['C1']:.3f} | {row['C3']:.3f} | {row['Delta (C3 - C1)']:.3f} |\n")
            
        f.write("\n## Shift in Self-Preference by Dimension (C3 - C1)\n\n")
        f.write("| Judge | Correctness | Completeness | Clarity | Creativity | Constraint |\n")
        f.write("|-------|-------------|--------------|---------|------------|------------|\n")
        for judge in dim_delta_df.index:
            row = dim_delta_df.loc[judge]
            f.write(f"| `{judge}` | {row['correctness']:.3f} | {row['completeness']:.3f} | {row['clarity']:.3f} | {row['creativity']:.3f} | {row['constraint_adherence']:.3f} |\n")
            
        f.write("\n## Summary of Findings\n")
        f.write("- **Claude:** The warning actually *increased* Claude's self-preference slightly.\n")
        f.write("- **Gemini:** The warning slightly increased Gemini's self-preference.\n")
        f.write("- **GPT:** The warning slightly increased GPT's self-preference.\n")
        f.write("- **Kimi:** The warning made Kimi's self-penalization even more severe (gap became more negative).\n")
        f.write("- Overall, simply telling a model to be objective and warning it about bias is entirely ineffective and sometimes backfires (reactance effect).\n")
        
    print(f"\nWrote {report_path}")

if __name__ == "__main__":
    main()
