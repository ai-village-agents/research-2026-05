import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Use a professional style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("talk")

REPO_ROOT = Path(__file__).resolve().parent.parent
SCORES_PATH = REPO_ROOT / "results" / "long_scores.csv"
PLOTS_DIR = REPO_ROOT / "analysis" / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# Load data dynamically like in run_analysis.py
judgments_dir = REPO_ROOT / "data" / "judgments"
all_scores = []
all_recognitions = []

if judgments_dir.exists():
    for judge_dir in judgments_dir.iterdir():
        if not judge_dir.is_dir():
            continue
        s_file = judge_dir / "long_scores.csv"
        r_file = judge_dir / "long_recognition.csv"
        if s_file.exists():
            all_scores.append(pd.read_csv(s_file))
        if r_file.exists():
            all_recognitions.append(pd.read_csv(r_file))

if all_scores:
    df = pd.concat(all_scores, ignore_index=True)
else:
    print("No data found")
    exit(0)

# Calculate composite scores
subscales = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
df["composite"] = df[subscales].mean(axis=1)
df["author_is_self"] = (df["judge"] == df["author"]).astype(int)
df["condition"] = df["condition"].astype(str).str.lower()

# Plot 1: Self-Preference Gap in C1
c1_data = df[df["condition"] == "c1"].copy()
c1_summary = c1_data.groupby(["judge", "author_is_self"])["composite"].mean().unstack()
c1_summary.columns = ["Other", "Self"]
c1_summary["Gap"] = c1_summary["Self"] - c1_summary["Other"]
c1_plot_data = c1_summary.reset_index()

plt.figure(figsize=(10, 6))
ax = sns.barplot(data=c1_plot_data, x="judge", y="Gap", hue="judge", palette="viridis", legend=False)
plt.title("Self-Preference Gap in Baseline Blind Eval (C1)", pad=20, fontweight='bold')
plt.ylabel("Gap in Composite Score (Self - Other)")
plt.xlabel("Judge Model")
plt.axhline(0, color='black', linestyle='--', linewidth=1.5)

# Add value labels on top of bars
for i, v in enumerate(c1_plot_data["Gap"]):
    ax.text(i, v + (0.05 if v > 0 else -0.1), f"{v:+.3f}", ha='center', va='bottom' if v > 0 else 'top', fontweight='bold')

plt.tight_layout()
plt.savefig(PLOTS_DIR / "c1_self_preference_gap.png", dpi=300)
plt.close()

# Plot 2: Accuracy of Self-Recognition (C4)
if all_recognitions:
    recog_df = pd.concat(all_recognitions, ignore_index=True)
    recog_df["correct"] = (recog_df["true_author"] == recog_df["predicted_author"]).astype(int)
    
    # Calculate accuracy per judge
    acc_summary = recog_df.groupby("judge")["correct"].mean().reset_index()
    acc_summary.rename(columns={"correct": "Accuracy"}, inplace=True)
    
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(data=acc_summary, x="judge", y="Accuracy", hue="judge", palette="mako", legend=False)
    plt.title("Self-Recognition Accuracy (C4)", pad=20, fontweight='bold')
    plt.ylabel("Accuracy")
    plt.xlabel("Judge Model")
    plt.axhline(0.25, color='red', linestyle='--', linewidth=2, label="Chance Level (25%)")
    plt.legend(loc='upper right')
    plt.ylim(0, 1.05)
    
    # Add percentage labels
    for i, v in enumerate(acc_summary["Accuracy"]):
        ax.text(i, v + 0.02, f"{v:.1%}", ha='center', va='bottom', fontweight='bold')
        
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / "c4_recognition_accuracy.png", dpi=300)
    plt.close()

print("Plots generated successfully in analysis/plots/")
