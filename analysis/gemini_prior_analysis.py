import json
import os
import pandas as pd
import numpy as np
import re

def extract_features(text):
    """Extract structural and stylistic features from text."""
    words = text.split()
    word_count = len(words)
    
    code_blocks = len(re.findall(r'```', text)) // 2
    has_code = 1 if code_blocks > 0 else 0
    
    lists = len(re.findall(r'^\s*[-*+]\s+', text, re.MULTILINE))
    has_lists = 1 if lists > 0 else 0
    
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    avg_sentence_length = sum(len(s.split()) for s in sentences) / max(1, len(sentences))
    
    return {
        'word_count': word_count,
        'code_blocks': code_blocks,
        'has_code': has_code,
        'lists': lists,
        'has_lists': has_lists,
        'avg_sentence_length': avg_sentence_length
    }

def build_feature_matrix():
    rec_path = "data/judgments/gemini-3.1-pro/long_recognition.csv"
    if not os.path.exists(rec_path):
        print(f"{rec_path} not found.")
        return None
        
    df = pd.read_csv(rec_path)
    df['predicted_self'] = (df['predicted_author'] == 'gemini-3.1-pro').astype(int)
    
    features_list = []
    base_responses_dir = "experiments/evaluator-bias/responses"
    
    for _, row in df.iterrows():
        author = row['true_author']
        prompt_id = row['prompt_id']
        
        filepath = os.path.join(base_responses_dir, author, f"prompt-{prompt_id}.json")
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                text = data.get('response', '')
                
                feats = extract_features(text)
                feats['predicted_self'] = row['predicted_self']
                feats['author'] = author
                feats['prompt_id'] = prompt_id
                feats['predicted_author'] = row['predicted_author']
                features_list.append(feats)
    
    feature_df = pd.DataFrame(features_list)
    return feature_df

if __name__ == "__main__":
    df = build_feature_matrix()
    if df is not None and len(df) > 0:
        print("=== MEAN FEATURES BY PREDICTED SELF ===")
        print(df.groupby('predicted_self').mean(numeric_only=True))
        
        print("\n=== MEAN FEATURES BY TRUE AUTHOR ===")
        print(df.groupby('author').mean(numeric_only=True))
        
        print("\n=== CORRELATIONS WITH PREDICTED_SELF ===")
        numeric_cols = ['word_count', 'code_blocks', 'lists', 'avg_sentence_length']
        for col in numeric_cols:
            corr = df['predicted_self'].corr(df[col])
            print(f"{col}: {corr:.3f}")
        
        print("\n=== RAW COUNTS OF PREDICTIONS ===")
        print(df['predicted_self'].value_counts())
        print("\n=== THE 14 INSTANCES NOT PREDICTED AS SELF ===")
        not_self = df[df['predicted_self'] == 0]
        print(not_self[['author', 'prompt_id', 'predicted_author', 'word_count']])
