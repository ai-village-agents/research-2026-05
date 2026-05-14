#!/usr/bin/env python3
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

def main():
    # Load C1 score data
    scores = pd.read_csv(RESULTS / "long_scores.csv")
    c1_scores = scores[scores["condition"].str.upper() == "C1"].copy()
    
    dims = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
    c1_scores["total_score"] = c1_scores[dims].sum(axis=1)
    
    # Calculate self vs peer score gap per prompt category
    c1_scores["is_self"] = c1_scores["judge"] == c1_scores["author"]
    
    agg = c1_scores.groupby(["category", "judge", "is_self"])["total_score"].mean().reset_index()
    
    pivoted = agg.pivot_table(
        index=["category", "judge"], 
        columns="is_self", 
        values="total_score"
    ).reset_index()
    
    if False in pivoted.columns and True in pivoted.columns:
        pivoted["self_pref_gap"] = pivoted[True] - pivoted[False]
    else:
        print("Missing self categories")
        return
        
    pivoted.to_csv(RESULTS / "prompt_category_bias.csv", index=False)
    
    # Also calculate the overall gap by category (pooling judges)
    overall_agg = c1_scores.groupby(["category", "is_self"])["total_score"].mean().reset_index()
    overall_pivoted = overall_agg.pivot_table(
        index="category", 
        columns="is_self", 
        values="total_score"
    ).reset_index()
    overall_pivoted["pooled_self_pref_gap"] = overall_pivoted[True] - overall_pivoted[False]
    
    # Write report
    report = ["# Self-Preference Gap by Prompt Category", ""]
    report.append("Does the nature of the prompt influence the severity of self-preference bias?")
    report.append("")
    report.append("## Pooled 4-Judge Gap by Category")
    report.append("")
    report.append("| Category | Mean Score (Self) | Mean Score (Peer) | Pooled Gap |")
    report.append("|---|---|---|---|")
    
    for _, row in overall_pivoted.iterrows():
        cat = row["category"]
        self_score = row.get(True, np.nan)
        peer_score = row.get(False, np.nan)
        gap = row.get("pooled_self_pref_gap", np.nan)
        
        self_str = f"{self_score:.2f}" if pd.notna(self_score) else "N/A"
        peer_str = f"{peer_score:.2f}" if pd.notna(peer_score) else "N/A"
        gap_str = f"{gap:+.2f}" if pd.notna(gap) else "N/A"
        
        report.append(f"| {cat} | {self_str} | {peer_str} | {gap_str} |")
        
    report.append("")
    report.append("## Per-Judge Gap by Category")
    report.append("")
    report.append("| Category | Judge | Mean Score (Self) | Mean Score (Peer) | Gap |")
    report.append("|---|---|---|---|---|")
    
    for _, row in pivoted.iterrows():
        cat = row["category"]
        judge = row["judge"]
        self_score = row.get(True, np.nan)
        peer_score = row.get(False, np.nan)
        gap = row.get("self_pref_gap", np.nan)
        
        self_str = f"{self_score:.2f}" if pd.notna(self_score) else "N/A"
        peer_str = f"{peer_score:.2f}" if pd.notna(peer_score) else "N/A"
        gap_str = f"{gap:+.2f}" if pd.notna(gap) else "N/A"
        
        report.append(f"| {cat} | {judge} | {self_str} | {peer_str} | {gap_str} |")
        
    (RESULTS / "prompt_category_bias.md").write_text("\n".join(report))
    print("Wrote prompt category bias analysis.")

if __name__ == "__main__":
    main()
