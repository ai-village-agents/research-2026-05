import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Use a professional style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_context("talk")

REPO_ROOT = Path(__file__).resolve().parent.parent
PLOTS_DIR = REPO_ROOT / "analysis" / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# Load data dynamically like in run_analysis.py
judgments_dir = REPO_ROOT / "data" / "judgments"
all_scores = []

if judgments_dir.exists():
    for judge_dir in judgments_dir.iterdir():
        if not judge_dir.is_dir():
            continue
        s_file = judge_dir / "long_scores.csv"
        if s_file.exists():
            all_scores.append(pd.read_csv(s_file))

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

# Calculate self-preference gap per judge per condition
summary = df.groupby(["judge", "condition", "author_is_self"])["composite"].mean().unstack().reset_index()
summary.columns = ["judge", "condition", "mean_other", "mean_self"]
summary["gap"] = summary["mean_self"] - summary["mean_other"]

plt.figure(figsize=(12, 7))
ax = sns.barplot(data=summary, x="judge", y="gap", hue="condition", palette="Set2")
plt.title("Effect of Mitigation Strategies on Self-Preference Gap", pad=20, fontweight='bold')
plt.ylabel("Gap in Composite Score (Self - Other)")
plt.xlabel("Judge Model")
plt.axhline(0, color='black', linestyle='--', linewidth=1.5)

# Add legend with better labels
handles, labels = ax.get_legend_handles_labels()
new_labels = []
for label in labels:
    if label == "c1": new_labels.append("C1 (Baseline)")
    elif label == "c2": new_labels.append("C2 (Paraphrased)")
    elif label == "c3": new_labels.append("C3 (Bias-Warned)")
    else: new_labels.append(label)
plt.legend(handles, new_labels, title="Condition", loc='upper right')

plt.tight_layout()
plt.savefig(PLOTS_DIR / "condition_effects_gap.png", dpi=300)
plt.close()

print("Condition effects plot generated successfully in analysis/plots/")
