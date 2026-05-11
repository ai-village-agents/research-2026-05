import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def main():
    judgments_dir = "data/judgments"
    score_files = glob.glob(os.path.join(judgments_dir, "*", "long_scores.csv"))
    recog_files = glob.glob(os.path.join(judgments_dir, "*", "long_recognition.csv"))

    if not recog_files:
        print("No recognition files found.")
        return

    scores_dfs = []
    for f in score_files:
        try:
            df = pd.read_csv(f)
            scores_dfs.append(df)
        except Exception as e:
            pass
    if not scores_dfs:
        return
    scores_df = pd.concat(scores_dfs, ignore_index=True)
    
    # Calculate overall score
    score_cols = ['correctness', 'completeness', 'clarity', 'creativity', 'constraint_adherence']
    scores_df['overall_score'] = scores_df[score_cols].mean(axis=1)
    
    c4_dfs = []
    for f in recog_files:
        try:
            df = pd.read_csv(f)
            c4_dfs.append(df)
        except Exception as e:
            pass
    c4_df = pd.concat(c4_dfs, ignore_index=True)

    # In scores_df it's 'author', in c4_df it's 'true_author'
    c4_df = c4_df.rename(columns={'true_author': 'author'})

    # Merge scores with C4 predictions
    merged = pd.merge(
        scores_df,
        c4_df[['judge', 'author', 'prompt_id', 'predicted_author', 'confidence']],
        on=['judge', 'author', 'prompt_id'],
        how='inner'
    )
    
    merged['predicted_self'] = (merged['predicted_author'] == merged['judge']).astype(int)
    merged['author_is_self'] = (merged['author'] == merged['judge']).astype(int)

    # Calculate mean score for each (confidence, predicted_self) bucket
    summary = merged.groupby(['confidence', 'predicted_self'])['overall_score'].agg(['mean', 'count']).reset_index()
    summary = summary.sort_values(by=['confidence', 'predicted_self'], ascending=[False, False])
    
    # Let's save the markdown
    md_str = "# Confidence Stratification Analysis\n\n"
    md_str += "This table shows the mean overall score given to a response, broken down by the judge's confidence in their authorship prediction (1-5) and whether they predicted they were the author (1) or not (0). Pooled across C1, C2, and C3.\n\n"
    md_str += "| Confidence | Predicted Self | Mean Score | N |\n"
    md_str += "|---|---|---|---|\n"
    for _, row in summary.iterrows():
        md_str += f"| {int(row['confidence'])} | {int(row['predicted_self'])} | {row['mean']:.2f} | {int(row['count'])} |\n"
        
    os.makedirs('results', exist_ok=True)
    with open('results/confidence_stratification.md', 'w') as f:
        f.write(md_str)
        
    print("Saved markdown to results/confidence_stratification.md")

    # Plot
    fig, ax = plt.subplots(figsize=(8, 6))
    
    conf_levels = sorted(merged['confidence'].dropna().unique())
    
    pred_self_0 = []
    pred_self_1 = []
    
    for conf in conf_levels:
        m0 = summary[(summary['confidence'] == conf) & (summary['predicted_self'] == 0)]['mean']
        m1 = summary[(summary['confidence'] == conf) & (summary['predicted_self'] == 1)]['mean']
        
        pred_self_0.append(m0.values[0] if len(m0) > 0 else np.nan)
        pred_self_1.append(m1.values[0] if len(m1) > 0 else np.nan)
        
    x = np.arange(len(conf_levels))
    width = 0.35

    ax.bar(x - width/2, pred_self_0, width, label='Predicted Other (0)', color='lightcoral')
    ax.bar(x + width/2, pred_self_1, width, label='Predicted Self (1)', color='cornflowerblue')

    ax.set_ylabel('Mean Overall Score')
    ax.set_title('Score by Prediction Confidence and Predicted Self (Pooled C1-C3)')
    ax.set_xticks(x)
    ax.set_xticklabels([f"Conf {int(c)}" for c in conf_levels])
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    os.makedirs('analysis/plots', exist_ok=True)
    plt.savefig('analysis/plots/confidence_stratification.png', dpi=300)
    print("Saved plot to analysis/plots/confidence_stratification.png")

if __name__ == '__main__':
    main()
