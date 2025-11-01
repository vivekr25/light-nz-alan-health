# scripts/50_load_obesity_data.py
import pandas as pd

# Load the CSV (path based on your structure)
IN = "data_raw/adult_unadjusted_topic_body_size_includes_obesity.csv"

# Read and inspect first few lines
df = pd.read_csv(IN)
print("✅ Loaded", df.shape, "rows")
print(df.columns.tolist())
print(df.head(10))

# --- Basic cleanup ---
# Strip column names of spaces and unify case
df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

# Filter for obesity-related rows (BMI ≥30, obese, etc.)
mask = df["indicator"].str.contains("obese", case=False, na=False)
df_obese = df[mask].copy()

# Keep key columns
cols = [c for c in df_obese.columns if c in ["region", "indicator", "estimate", "lower_ci", "upper_ci", "year", "sex", "ethnicity"]]
print("📊 Filtered columns:", cols)
print(df_obese[cols].head(10))

# Save intermediate cleaned dataset
out_path = "data_proc/obesity_by_region.csv"
df_obese.to_csv(out_path, index=False)
print(f"✅ Saved → {out_path}")