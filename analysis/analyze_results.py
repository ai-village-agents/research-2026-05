import json
import pandas as pd
import numpy as np

def main():
    print("Loading mock results...")
    with open("data/mock_results.json", "r") as f:
        data = json.load(f)
        
    df = pd.DataFrame(data)
    
    # Add self-author flag
    df['is_self'] = df['generator'] == df['evaluator']
    
    # Calculate Self-Preference (Mean scores)
    print("\n--- RQ1: Self-Preference Bias (Baseline Condition) ---")
    baseline_df = df[df['condition'] == 'baseline']
    
    mean_scores = baseline_df.groupby(['evaluator', 'is_self'])['score'].mean().unstack()
    mean_scores.columns = ['Score for Others', 'Score for Self']
    mean_scores['Self-Preference Gap'] = mean_scores['Score for Self'] - mean_scores['Score for Others']
    print(mean_scores)
    
    # Calculate Self-Recognition Accuracy
    print("\n--- RQ2: Self-Recognition ---")
    df['correct_recognition'] = df['recognized_as'] == df['generator']
    recognition_accuracy = df.groupby('evaluator')['correct_recognition'].mean()
    print("Recognition Accuracy by Evaluator:")
    print(recognition_accuracy)

if __name__ == "__main__":
    main()
