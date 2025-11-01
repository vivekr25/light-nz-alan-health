import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

IN = "data_proc/obesity_vs_brightness_by_region.csv"

df = pd.read_csv(IN)

# Drop blanks and "All" ethnicity
df = df.dropna(subset=["radiance_mean", "ethnicity", "obesity_rate"])
df = df[df["ethnicity"].ne("All")].copy()

# Check for duplicates
print("Unique regions:", df["health_region"].nunique())
print("Unique ethnicities:", df["ethnicity"].unique())
print(df.groupby("ethnicity")["radiance_mean"].describe())

# Scatter plot
plt.figure(figsize=(8, 6))
for eth in df["ethnicity"].unique():
    sub = df[df["ethnicity"] == eth]
    plt.scatter(
        sub["radiance_mean"],
        sub["obesity_rate"],
        label=eth,
        s=120,
        alpha=0.8
    )

plt.title("Obesity vs Night-time Brightness by Ethnicity (NZ, 2020/21)")
plt.xlabel("Mean Night-time Brightness (nW/cm²·sr)")
plt.ylabel("Obesity Rate (proportion of adults)")
plt.legend(title="Ethnicity")
plt.grid(alpha=0.3)
plt.tight_layout()

Path("data_proc").mkdir(exist_ok=True)
out = "data_proc/obesity_vs_brightness_scatter_fixed.png"
plt.savefig(out, dpi=300)
print(f"✅ Saved → {out}")
plt.show()