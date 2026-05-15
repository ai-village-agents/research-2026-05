import pandas as pd
import numpy as np

claims = [
    {"Claim": "Pooled 3J Observational Baseline (C1)", "Estimate": "+1.460", "Type": "Bootstrap CI", "Result": "Significant", "Section": "Observational"},
    {"Claim": "Pooled 4J Observational Baseline (C1)", "Estimate": "+0.378", "Type": "Bootstrap CI", "Result": "Null", "Section": "Observational"},
    {"Claim": "Claude 4J Observational Baseline (C1)", "Estimate": "+2.433", "Type": "Bootstrap CI", "Result": "Significant", "Section": "Observational"},
    {"Claim": "Gemini 4J Observational Baseline (C1)", "Estimate": "+0.627", "Type": "Bootstrap CI", "Result": "Significant", "Section": "Observational"},
    {"Claim": "GPT 4J Observational Baseline (C1)", "Estimate": "+1.327", "Type": "Bootstrap CI", "Result": "Significant", "Section": "Observational"},
    {"Claim": "Kimi 4J Observational Baseline (C1)", "Estimate": "-2.873", "Type": "Bootstrap CI", "Result": "Significant", "Section": "Observational"},
    
    {"Claim": "Mediation: Actual Authorship", "Estimate": "-0.349", "Type": "Regression β CI", "Result": "Null", "Section": "Mechanism"},
    {"Claim": "Mediation: Perceived Authorship", "Estimate": "+1.532", "Type": "Regression β CI", "Result": "Significant", "Section": "Mechanism"},
    {"Claim": "Floor-Raiser Mechanism (Gemini)", "Estimate": "ρ = -0.834", "Type": "Spearman", "Result": "Significant", "Section": "Mechanism"},
    
    {"Claim": "Causal Label-Swap: Claude Self-Effect", "Estimate": "+0.120", "Type": "Bootstrap CI", "Result": "Null", "Section": "Causal RCT"},
    {"Claim": "Causal Label-Swap: Gemini Self-Effect", "Estimate": "+0.293", "Type": "Bootstrap CI", "Result": "Significant", "Section": "Causal RCT"},
    {"Claim": "Causal Label-Swap: GPT Self-Effect", "Estimate": "0.000", "Type": "Exact", "Result": "Null", "Section": "Causal RCT"},
    {"Claim": "Causal Label-Swap: Kimi Self-Effect", "Estimate": "+0.007", "Type": "Bootstrap CI", "Result": "Null", "Section": "Causal RCT"},
    {"Claim": "Causal Label-Swap: Gemini anti-Kimi", "Estimate": "-0.245", "Type": "Bootstrap CI", "Result": "Significant", "Section": "Causal RCT"},
    {"Claim": "Causal Label-Swap: Claude pro-Claude", "Estimate": "+0.120", "Type": "Bootstrap CI", "Result": "Null", "Section": "Causal RCT"},
    {"Claim": "Causal Label-Swap: Kimi pro-Claude", "Estimate": "+0.300", "Type": "Bootstrap CI", "Result": "Null", "Section": "Causal RCT"},
    
]

df = pd.DataFrame(claims)

output_md = """# Master Claims Multiplicity Summary

This document aggregates all formal claims made in the v1.3.0 release that rely on Confidence Intervals, P-values, or explicit statistical testing. 

"""

for section in df['Section'].unique():
    output_md += f"\n### {section}\n\n"
    output_md += df[df['Section'] == section][['Claim', 'Estimate', 'Type', 'Result']].to_markdown(index=False) + "\n"

with open("/home/computeruse/research-2026-05/experiments/replication-wave/results/master_claims_summary.md", "w") as f:
    f.write(output_md)

print("Created master_claims_summary.md")
