import json
import pandas as pd
from pathlib import Path
import glob

lengths = []

for judge in ['claude-opus-4.7', 'gemini-3.1-pro', 'gpt-5.5', 'kimi-k2.6']:
    path_pattern = f"experiments/replication-wave/responses/{judge}/*.json"
    files = glob.glob(path_pattern)
    for file in files:
        with open(file) as f:
            data = json.load(f)
            prompt_id = Path(file).stem
            # Assuming standard response format where the key is the text
            text = data.get('text', '') 
            # Or if it's the raw response output string
            if not text and isinstance(data, str):
                text = data
            elif not text and isinstance(data, dict):
                 # Try first key
                 text = list(data.values())[0] if data else ""
            words = len(str(text).split())
            lengths.append({
                'author': judge,
                'prompt_id': prompt_id,
                'word_count': words
            })

df = pd.DataFrame(lengths)
if len(df) > 0:
    mean_lengths = df.groupby(['prompt_id', 'author'])['word_count'].mean().unstack()
    print(mean_lengths.to_markdown())
else:
    print("No data found.")
