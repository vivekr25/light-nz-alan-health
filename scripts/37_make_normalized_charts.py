from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

IN = "data_proc/viirs_ta_2021_normalized.csv"
Path("data_proc").mkdir(exist_ok=True)

df = pd.read_csv(IN)

def top_bar(data: pd.DataFrame, value_col: str, title: str, out_png: str, n=15):
    t = data.sort_values(value_col, ascending=False).head(n)
    plt.figure(figsize=(10, 6))
    ax = plt.gca()
    ax.bar(t["ta_name"], t[value_col])
    ax.set_title(title)
    ax.set_ylabel(value_col.replace("_", " "))
    ax.set_xticklabels(t["ta_name"], rotation=65, ha="right")
    plt.tight_layout()
    plt.savefig(out_png, dpi=160)
    plt.close()
    print(f"🖼️ saved {out_png}")

# Absolute radiance
top_bar(
    df, "radiance_mean",
    "Top 15 TAs by mean radiance (VIIRS 2021)",
    "data_proc/top15_abs_radiance.png"
)

# Per km² (density)
if df["radiance_per_km2"].notna().any():
    top_bar(
        df, "radiance_per_km2",
        "Top 15 TAs by radiance per km² (VIIRS 2021)",
        "data_proc/top15_radiance_per_km2.png"
    )

# Per capita (only if population provided)
df_cap = df.dropna(subset=["radiance_per_capita"])
if not df_cap.empty:
    top_bar(
        df_cap, "radiance_per_capita",
        "Top 15 TAs by radiance per capita (VIIRS 2021)",
        "data_proc/top15_radiance_per_capita.png"
    )
else:
    print("ℹ️ Skipping per-capita chart (no population values yet).")

# Histogram for distribution
plt.figure(figsize=(8,5))
df["radiance_mean"].plot(kind="hist", bins=30)
plt.xlabel("Mean radiance (nW/cm²·sr)")
plt.ylabel("Count of TAs")
plt.title("Distribution of mean radiance across TAs")
plt.tight_layout()
plt.savefig("data_proc/hist_radiance_mean.png", dpi=160)
plt.close()
print("✅ saved data_proc/hist_radiance_mean.png")