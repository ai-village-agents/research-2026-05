#!/usr/bin/env python3
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCORES_CSV = RESULTS / "long_scores.csv"

def calculate_icc(df, rater_col, target_col, score_col):
    k = df[rater_col].nunique()
    n = df[target_col].nunique()
    if k < 2 or n < 2: return np.nan, np.nan
    
    grand_mean = df[score_col].mean()
    target_means = df.groupby(target_col)[score_col].mean()
    rater_means = df.groupby(rater_col)[score_col].mean()
    
    ss_total = ((df[score_col] - grand_mean)**2).sum()
    ss_target = k * ((target_means - grand_mean)**2).sum()
    ss_rater = n * ((rater_means - grand_mean)**2).sum()
    ss_error = ss_total - ss_target - ss_rater
    
    df_target = n - 1
    df_rater = k - 1
    df_error = (n - 1) * (k - 1)
    
    ms_target = ss_target / df_target if df_target > 0 else 0
    ms_rater = ss_rater / df_rater if df_rater > 0 else 0
    ms_error = ss_error / df_error if df_error > 0 else 0
    
    numerator = ms_target - ms_error
    denominator = ms_target + (k - 1) * ms_error + k * (ms_rater - ms_error) / n
    icc21 = numerator / denominator if denominator != 0 else np.nan
    
    denominator31 = ms_target + (k - 1) * ms_error
    icc31 = numerator / denominator31 if denominator31 != 0 else np.nan
    
    return icc21, icc31

def main():
    if not SCORES_CSV.exists():
        print(f"Scores file not found: {SCORES_CSV}")
        return
        
    df = pd.read_csv(SCORES_CSV)
    df = df[df["condition"].str.lower() == "c1"].copy()
    
    # Calculate total score from the dimensions
    dims = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
    df["score"] = df[dims].mean(axis=1)
    
    # Use "author" instead of "actual_author" based on the csv header
    df["target_id"] = df["prompt_id"] + "_" + df["author"]
    
    icc21, icc31 = calculate_icc(df, "judge", "target_id", "score")
    
    print("=== Inter-Rater Reliability (C1 Baseline) ===")
    print(f"ICC(2,1) [Absolute Agreement]: {icc21:.3f}")
    print(f"ICC(3,1) [Consistency]:        {icc31:.3f}")
    
    print("\n=== Inter-Rater Reliability by Dimension (C1) ===")
    for dim in dims:
        if dim in df.columns:
            dim_icc21, dim_icc31 = calculate_icc(df, "judge", "target_id", dim)
            print(f"{dim.ljust(20)} | ICC(2,1): {dim_icc21:.3f} | ICC(3,1): {dim_icc31:.3f}")
            
    print("\n=== Leave-One-Judge-Out ICC(2,1) ===")
    judges = df["judge"].unique()
    lojo_results = {}
    for drop_judge in sorted(judges):
        lojo_df = df[df["judge"] != drop_judge]
        lojo_icc21, _ = calculate_icc(lojo_df, "judge", "target_id", "score")
        print(f"Dropping {drop_judge.ljust(15)}: {lojo_icc21:.3f}")
        lojo_results[drop_judge] = lojo_icc21
        
    report_path = RESULTS / "icc_agreement_report.md"
    with open(report_path, "w") as f:
        f.write("# Inter-Rater Reliability (ICC) for C1 Baseline\n\n")
        f.write(f"**Overall ICC(2,1) (Absolute Agreement):** {icc21:.3f}\n")
        f.write(f"**Overall ICC(3,1) (Consistency):** {icc31:.3f}\n\n")
        f.write("### By Dimension\n")
        f.write("| Dimension | ICC(2,1) | ICC(3,1) |\n")
        f.write("|-----------|----------|----------|\n")
        for dim in dims:
            if dim in df.columns:
                dim_icc21, dim_icc31 = calculate_icc(df, "judge", "target_id", dim)
                f.write(f"| {dim} | {dim_icc21:.3f} | {dim_icc31:.3f} |\n")
        f.write("\n### Leave-One-Judge-Out ICC(2,1)\n")
        for drop_judge in sorted(judges):
            f.write(f"- Dropping `{drop_judge}`: {lojo_results[drop_judge]:.3f}\n")
            
        # Add commentary about Kimi
        f.write("\n### Commentary\n")
        f.write("The Leave-One-Judge-Out analysis shows that overall inter-rater reliability ")
        if lojo_results.get("kimi-k2.6", 0) > icc21:
             f.write("increases when Kimi K2.6 is excluded. ")
        else:
             f.write("decreases when Kimi K2.6 is excluded. ")
        f.write("This helps quantify the extent to which each judge's idiosyncratic scoring patterns (e.g., Kimi's harsh self-penalization) disrupt overall consensus.\n")

    print(f"\nWrote {report_path}")

if __name__ == "__main__":
    main()
