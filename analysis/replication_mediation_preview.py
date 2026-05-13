import pandas as pd
import statsmodels.formula.api as smf
from pathlib import Path

base_dir = Path.home() / "research-2026-05"

# Load data
scores = pd.read_csv(base_dir / "experiments" / "replication-wave" / "results" / "long_scores.csv")
recog = pd.read_csv(base_dir / "experiments" / "replication-wave" / "results" / "long_recognition.csv")

# rename true_author to author in recog to match scores
recog = recog.rename(columns={"true_author": "author"})

# Merging with how="inner" drops Kimi's C1/C2/C3 scores since they don't exist yet,
# but gives us the 3-judge overlapping subset.
df = pd.merge(scores, recog, on=["prompt_id", "judge", "author"], how="inner")

df["is_self"] = (df["author"] == df["judge"]).astype(int)
df["predicted_self"] = (df["predicted_author"] == df["judge"]).astype(int)

# Create a composite score
subscales = ["correctness", "completeness", "clarity", "creativity", "constraint_adherence"]
df["mean_score"] = df[subscales].mean(axis=1)

print("--- Baron-Kenny Mediation Analysis (Replication Wave Preview) ---")
print(f"Total N (all conditions) = {len(df)}")

# Filter to just C1 for the basic mediation analysis.
# Note that condition is lowercase in long_scores.csv
df_c1 = df[df["condition"] == "c1"].copy()
print(f"C1 N = {len(df_c1)}")

# 1. Total Effect (X -> Y)
total_model = smf.ols("mean_score ~ is_self + C(prompt_id) + C(judge)", data=df_c1).fit()
c_path = total_model.params["is_self"]
print(f"\n1. Total Effect (c path): {c_path:.3f} (p={total_model.pvalues['is_self']:.3f})")

# 2. X -> M
xm_model = smf.ols("predicted_self ~ is_self + C(prompt_id) + C(judge)", data=df_c1).fit()
a_path = xm_model.params["is_self"]
print(f"2. X -> M (a path): {a_path:.3f} (p={xm_model.pvalues['is_self']:.3f})")

# 3. X + M -> Y
direct_model = smf.ols("mean_score ~ is_self + predicted_self + C(prompt_id) + C(judge)", data=df_c1).fit()
b_path = direct_model.params["predicted_self"]
c_prime_path = direct_model.params["is_self"]
print(f"3. M -> Y given X (b path): {b_path:.3f} (p={direct_model.pvalues['predicted_self']:.3f})")
print(f"   Direct Effect (c' path): {c_prime_path:.3f} (p={direct_model.pvalues['is_self']:.3f})")

indirect_effect = a_path * b_path
proportion_mediated = indirect_effect / c_path if c_path != 0 else 0

print(f"\nIndirect Effect (a*b): {indirect_effect:.3f}")
print(f"Proportion Mediated: {proportion_mediated:.1%}")

# Let's save this to a file
with open(base_dir / "analysis" / "replication_mediation_preview.md", "w") as f:
    f.write("# Replication Wave Mediation Analysis Preview\n\n")
    f.write("This is a preliminary Baron-Kenny mediation analysis on the replication wave C1 data.\n\n")
    f.write(f"Total N = {len(df_c1)}\n\n")
    f.write("### Paths:\n")
    f.write(f"- Total Effect (c path): {c_path:.3f}\n")
    f.write(f"- X -> M (a path): {a_path:.3f}\n")
    f.write(f"- M -> Y given X (b path): {b_path:.3f}\n")
    f.write(f"- Direct Effect (c' path): {c_prime_path:.3f}\n\n")
    f.write(f"**Indirect Effect (a*b):** {indirect_effect:.3f}\n")
    f.write(f"**Proportion Mediated:** {proportion_mediated:.1%}\n")

