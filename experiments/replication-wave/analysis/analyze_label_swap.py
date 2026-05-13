import json
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from glob import glob
import os

# Set paths
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
score_sheets_dir = os.path.join(base_dir, 'score_sheets', 'label_swap')
keys_dir = os.path.join(base_dir, 'data', 'label_swap_keys')

def load_data():
    all_data = []
    
    # Load keys
    keys = {}
    for judge_dir in glob(os.path.join(keys_dir, '*')):
        for key_file in glob(os.path.join(judge_dir, '*_key.json')):
            with open(key_file, 'r') as f:
                data = json.load(f)
                for item in data:
                    keys[item['session_blind_id']] = item
            
    # Load scored sessions
    for judge_dir in glob(os.path.join(score_sheets_dir, '*')):
        judge = os.path.basename(judge_dir)
        for session_file in glob(os.path.join(judge_dir, '*_scored.json')):
            with open(session_file, 'r') as f:
                data = json.load(f)
                session = data['session']
                
                for entry in data['entries']:
                    blind_id = entry['blind_id']
                    if blind_id not in keys:
                        print(f"Warning: Key not found for {blind_id}")
                        continue
                        
                    true_author = keys[blind_id]['actual_author']
                    displayed_label = entry['displayed_label']
                    
                    # Calculate composite score
                    scores = [
                        entry.get('correctness', np.nan),
                        entry.get('completeness', np.nan),
                        entry.get('clarity', np.nan),
                        entry.get('creativity', np.nan),
                        entry.get('constraint_adherence', np.nan)
                    ]
                    composite = np.nanmean(scores)
                    
                    all_data.append({
                        'judge': judge,
                        'prompt_id': entry['prompt_id'],
                        'blind_id': blind_id,
                        'true_author': true_author,
                        'displayed_label': displayed_label,
                        'composite_score': composite,
                        'is_true_self': judge == true_author,
                        'is_displayed_self': judge == displayed_label,
                        'is_displayed_kimi': displayed_label == 'kimi-k2.6'
                    })
                    
    return pd.DataFrame(all_data)

def analyze():
    df = load_data()
    print(f"Loaded {len(df)} scored entries.")
    
    if len(df) == 0:
        print("No data loaded yet.")
        return
        
    print("\n--- Summary Statistics ---")
    print(df.groupby('judge').size().to_string(name=False))
    
    print("\n--- Effect of Displayed Label (Overall) ---")
    model = smf.ols('composite_score ~ C(displayed_label, Treatment(reference="claude-opus-4.7"))', data=df).fit()
    print(model.summary().tables[1])
    
    print("\n--- The Predicted-Kimi Penalty (Causal RCT) ---")
    model_kimi = smf.ols('composite_score ~ is_displayed_kimi', data=df).fit()
    print(model_kimi.summary().tables[1])
    
    print("\n--- Interaction: Actual vs Displayed Self-Preference ---")
    model_inter = smf.ols('composite_score ~ is_true_self * is_displayed_self', data=df).fit()
    print(model_inter.summary().tables[1])

if __name__ == '__main__':
    analyze()
