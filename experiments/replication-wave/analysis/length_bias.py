#!/usr/bin/env python3
import pandas as pd
import numpy as np
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RESPONSES = ROOT / "responses"

def main():
    # Load C1 score data
    scores = pd.read_csv(RESULTS / "long_scores.csv")
    c1_scores = scores[scores["condition"].str.upper() == "C1"].copy()
    
    dims = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
    c1_scores["total_score"] = c1_scores[dims].sum(axis=1)
    
    # We need to get the length of the original responses
    authors = ["claude-opus-4.7", "gemini-3.1-pro", "gpt-5.5", "kimi-k2.6"]
    
    lengths = []
    for author in authors:
        author_dir = RESPONSES / author
        if not author_dir.exists(): continue
        for prompt_file in author_dir.glob("*.json"):
            prompt_id = prompt_file.stem
            if prompt_id.startswith("prompt-"):
                prompt_id = prompt_id[len("prompt-"):]
            data = json.loads(prompt_file.read_text())
            text = data.get("response", "")
            lengths.append({
                "author": author,
                "prompt_id": prompt_id,
                "word_count": len(text.split())
            })
            
    lengths_df = pd.DataFrame(lengths)
    
    # Merge lengths with scores
    merged = pd.merge(c1_scores, lengths_df, on=["author", "prompt_id"], how="inner")
    
    # Compute correlation between word count and total score for each judge
    correlations = []
    for judge in authors:
        judge_data = merged[merged["judge"] == judge]
        if len(judge_data) > 0:
            corr = judge_data["word_count"].corr(judge_data["total_score"])
            correlations.append({"judge": judge, "length_correlation": corr})
            
    corr_df = pd.DataFrame(correlations)
    corr_df.to_csv(RESULTS / "length_bias_correlation.csv", index=False)
    
    # Write report
    report = ["# Length Bias in Scoring", ""]
    report.append("Does a judge favor longer responses, regardless of authorship?")
    report.append("")
    report.append("| Judge | Pearson Correlation (Word Count vs Total Score) |")
    report.append("|---|---|")
    
    for _, row in corr_df.iterrows():
        judge = row["judge"]
        corr = row["length_correlation"]
        report.append(f"| {judge} | {corr:.3f} |")
        
    (RESULTS / "length_bias_report.md").write_text("\n".join(report))
    print("Wrote length bias analysis.")

if __name__ == "__main__":
    main()
