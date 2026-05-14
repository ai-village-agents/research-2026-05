#!/usr/bin/env python3
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

def main():
    # Load recognition data
    recognition = pd.read_csv(RESULTS / "long_recognition.csv")
    
    # Load C1 score data
    scores = pd.read_csv(RESULTS / "long_scores.csv")
    c1_scores = scores[scores["condition"].str.upper() == "C1"].copy()
    
    # We need to compute total scores
    dims = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
    c1_scores["total_score"] = c1_scores[dims].sum(axis=1)
    
    # Merge recognition and scores
    merged = pd.merge(
        c1_scores, 
        recognition, 
        left_on=["judge", "author", "prompt_id"], 
        right_on=["judge", "true_author", "prompt_id"],
        how="inner"
    )
    
    # Is the predicted author the same as the judge?
    merged["perceived_self"] = (merged["predicted_author"] == merged["judge"])
    
    # Let's look at the average score given based on perceived authorship and confidence
    agg = merged.groupby(["judge", "perceived_self", "confidence"])["total_score"].mean().reset_index()
    
    # Compute self-preference gap stratified by confidence
    # We want (Score when perceived self) - (Score when perceived NOT self) for each judge and confidence level
    
    # Pivot
    pivoted = agg.pivot_table(
        index=["judge", "confidence"], 
        columns="perceived_self", 
        values="total_score"
    ).reset_index()
    
    if False in pivoted.columns and True in pivoted.columns:
        pivoted["perceived_self_gap"] = pivoted[True] - pivoted[False]
    else:
        print("Missing perceived self categories")
        print(pivoted)
        return
        
    pivoted.to_csv(RESULTS / "confidence_stratification.csv", index=False)
    
    # Write report
    report = ["# Self-Preference Stratified by Confidence", ""]
    report.append("Does a judge's self-preference scale with their confidence in authorship?")
    report.append("")
    report.append("| Judge | Confidence | Mean Score (Perceived Self) | Mean Score (Perceived Peer) | Perceived Self Gap |")
    report.append("|---|---|---|---|---|")
    
    for _, row in pivoted.iterrows():
        judge = row["judge"]
        conf = row["confidence"]
        self_score = row.get(True, np.nan)
        peer_score = row.get(False, np.nan)
        gap = row.get("perceived_self_gap", np.nan)
        
        self_str = f"{self_score:.2f}" if pd.notna(self_score) else "N/A"
        peer_str = f"{peer_score:.2f}" if pd.notna(peer_score) else "N/A"
        gap_str = f"{gap:+.2f}" if pd.notna(gap) else "N/A"
        
        report.append(f"| {judge} | {conf} | {self_str} | {peer_str} | {gap_str} |")
        
    (RESULTS / "confidence_stratification.md").write_text("\n".join(report))
    print("Wrote confidence stratification analysis.")

if __name__ == "__main__":
    main()
