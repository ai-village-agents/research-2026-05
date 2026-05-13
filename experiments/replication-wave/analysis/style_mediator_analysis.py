import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import ols
import re
import os
import json

# Load the data
scores_path = 'experiments/replication-wave/results/long_scores.csv'
recognition_path = 'experiments/replication-wave/results/long_recognition.csv'
responses_base_dir = 'experiments/replication-wave/responses'

scores_df = pd.read_csv(scores_path)
recog_df = pd.read_csv(recognition_path)
recog_df = recog_df.rename(columns={'true_author': 'author'})

# Filter to C1 condition
c1_scores = scores_df[scores_df['condition'] == 'c1']

# Merge with recognition predictions
merged = pd.merge(c1_scores, recog_df, on=['judge', 'prompt_id', 'author'], how='left')

# Load responses
response_data = []
for author in os.listdir(responses_base_dir):
    author_dir = os.path.join(responses_base_dir, author)
    if os.path.isdir(author_dir):
        for filename in os.listdir(author_dir):
            if filename.endswith('.json'):
                # Strip "prompt-" prefix and ".json" suffix
                prompt_id = filename[7:-5]
                with open(os.path.join(author_dir, filename), 'r') as f:
                    data = json.load(f)
                    text = data.get('response', '')
                response_data.append({'author': author, 'prompt_id': prompt_id, 'response_text': text})

resp_df = pd.DataFrame(response_data)

# Merge with responses to calculate style features
full_data = pd.merge(merged, resp_df, on=['prompt_id', 'author'], how='inner')

# Create binary actual_self and predicted_self columns
full_data['actual_self'] = (full_data['judge'] == full_data['author']).astype(int)
full_data['predicted_self'] = (full_data['judge'] == full_data['predicted_author']).astype(int)

# --- Compute Stylometric Features ---
def extract_features(text):
    if pd.isna(text):
        return pd.Series({'sentence_length': 0, 'lexical_diversity': 0, 'list_density': 0, 'char_length': 0})
    
    # Character length
    char_length = len(text)
    
    # Sentence length (rough approximation using punctuation)
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 0]
    num_sentences = len(sentences)
    words = text.split()
    num_words = len(words)
    avg_sentence_length = num_words / num_sentences if num_sentences > 0 else 0
    
    # Lexical diversity (Type-Token Ratio)
    unique_words = set([w.lower() for w in words])
    lexical_diversity = len(unique_words) / num_words if num_words > 0 else 0
    
    # List density (count of -, *, 1., 2., etc. per word)
    list_items = len(re.findall(r'^[\s]*[-*•]\s|^[\s]*\d+\.\s', text, flags=re.MULTILINE))
    list_density = list_items / num_words if num_words > 0 else 0

    return pd.Series({
        'sentence_length': avg_sentence_length,
        'lexical_diversity': lexical_diversity,
        'list_density': list_density,
        'char_length': char_length
    })

print("Extracting stylometric features...")
style_features = full_data['response_text'].apply(extract_features)
full_data = pd.concat([full_data, style_features], axis=1)

# Standardize the features
for col in ['sentence_length', 'lexical_diversity', 'list_density', 'char_length']:
    full_data[col] = (full_data[col] - full_data[col].mean()) / full_data[col].std()

# Combine mean5
full_data['mean5'] = full_data[['correctness', 'completeness', 'clarity', 'creativity', 'constraint_adherence']].mean(axis=1)

# --- Run the Analysis ---
# Base model: Quality predicted by actual authorship and perceived authorship
print("\n--- Base Model: Quality ~ actual_self + predicted_self + judge FE + prompt FE ---")
formula_base = 'mean5 ~ actual_self + predicted_self + C(judge) + C(prompt_id)'
model_base = ols(formula_base, data=full_data).fit(cov_type='cluster', cov_kwds={'groups': full_data['prompt_id']})
print(model_base.summary().tables[1])

# Model with predicted label: Quality predicted by predicted label and actual label
print("\n--- Model 2: Quality ~ C(predicted_author) + C(author) + judge FE + prompt FE ---")
formula_labels = 'mean5 ~ C(predicted_author, Treatment(reference="kimi-k2.6")) + C(author, Treatment(reference="kimi-k2.6")) + C(judge) + C(prompt_id)'
model_labels = ols(formula_labels, data=full_data).fit(cov_type='cluster', cov_kwds={'groups': full_data['prompt_id']})
print(model_labels.summary().tables[1])

# Model adding stylometric features to the predicted label model
print("\n--- Model 3: Quality ~ C(predicted_author) + C(author) + Style + judge FE + prompt FE ---")
formula_style = 'mean5 ~ C(predicted_author, Treatment(reference="kimi-k2.6")) + C(author, Treatment(reference="kimi-k2.6")) + sentence_length + lexical_diversity + list_density + char_length + C(judge) + C(prompt_id)'
model_style = ols(formula_style, data=full_data).fit(cov_type='cluster', cov_kwds={'groups': full_data['prompt_id']})
print(model_style.summary().tables[1])

print("\nAnalysis complete.")
