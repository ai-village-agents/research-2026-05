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

# Plot: Distribution of composite scores given by each judge
plt.figure(figsize=(12, 7))
sns.violinplot(data=df, x="judge", y="composite", hue="judge", palette="deep", legend=False)
plt.title("Distribution of Composite Scores Awarded by Each Judge", pad=20, fontweight='bold')
plt.ylabel("Composite Score (1-10)")
plt.xlabel("Judge Model")
plt.tight_layout()
plt.savefig(PLOTS_DIR / "score_distributions.png", dpi=300)
plt.close()

print("Score distributions plot generated successfully in analysis/plots/")
