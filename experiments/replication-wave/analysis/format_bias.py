import pandas as pd
from pathlib import Path
import json
import re

# Read long scores
long_scores = pd.read_csv("experiments/replication-wave/results/long_scores.csv")
c1_scores = long_scores[long_scores['condition'] == 'c1'].copy()

# Load response formats
features = []
import glob
for author in ['claude-opus-4.7', 'gemini-3.1-pro', 'gpt-5.5', 'kimi-k2.6']:
    path_pattern = f"experiments/replication-wave/responses/{author}/*.json"
    files = glob.glob(path_pattern)
    for file in files:
        with open(file) as f:
            data = json.load(f)
            # Remove prompt- to match scores
            prompt_id = Path(file).stem.replace('prompt-', '')
            
            text = data.get('text', '') 
            if not text and isinstance(data, str):
                text = data
            elif not text and isinstance(data, dict):
                 text = list(data.values())[0] if data else ""
            
            text = str(text)
            
            features.append({
                'author': author,
                'prompt_id': prompt_id,
                'bold_tags': len(re.findall(r'\*\*.*?\*\*', text)),
                'list_items': len(re.findall(r'^\s*[-*+]\s', text, flags=re.MULTILINE)) + len(re.findall(r'^\s*\d+\.\s', text, flags=re.MULTILINE)),
                'code_blocks': len(re.findall(r'```', text)) // 2
            })

df_features = pd.DataFrame(features)

c1_scores['composite'] = c1_scores[['correctness', 'completeness', 'clarity', 'creativity', 'constraint_adherence']].mean(axis=1)

# Merge features and scores
merged = c1_scores.merge(df_features, on=['author', 'prompt_id'])

# Calculate correlation between composite score and format features per judge
correlations = {}
for judge in merged['judge'].unique():
    judge_data = merged[merged['judge'] == judge]
    correlations[judge] = {
        'bold_tags': judge_data['composite'].corr(judge_data['bold_tags']),
        'list_items': judge_data['composite'].corr(judge_data['list_items']),
        'code_blocks': judge_data['composite'].corr(judge_data['code_blocks'])
    }

print("Correlation between format features and composite score in C1:")
print(pd.DataFrame(correlations).T.to_markdown())

