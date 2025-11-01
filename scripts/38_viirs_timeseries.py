# scripts/38_viirs_timeseries.py
"""
Aggregate VIIRS night light data (2014–2023) to build a time series
for each Territorial Authority (TA) and plot trends.
"""

import pandas as pd
import matplotlib.pyplot as plt
import pathlib

# ---- paths ----
DATA_DIR = pathlib.Path("data_raw/viirs_yearly")
OUT_DIR = pathlib.Path("data_proc")
OUT_DIR.mkdir(exist_ok=True)

# Expect CSVs like viirs_ta_annual_2014_with_names.csv ... 2023 ...
files = sorted(DATA_DIR.glob("viirs_ta_annual_*_with_names.csv"))
if not files:
    raise FileNotFoundError("No annual files found in data_raw/viirs_yearly/")

dfs = []
for f in files:
    year = int(f.stem.split("_")[3])
    df = pd.read_csv(f)
    df["year"] = year
    dfs.append(df)

df_all = pd.concat(dfs, ignore_index=True)
df_all.to_csv(OUT_DIR / "viirs_ta_timeseries_2014_2023.csv", index=False)
print(f"✅ Combined {len(files)} years → data_proc/viirs_ta_timeseries_2014_2023.csv")

# ---- summary ----
mean_by_year = (
    df_all.groupby(["year", "ta_name"])["radiance_mean"].mean().reset_index()
)

# ---- top 6 TAs overall ----
top6 = (
    df_all.groupby("ta_name")["radiance_mean"].mean()
    .sort_values(ascending=False)
    .head(6)
    .index.tolist()
)

# ---- plot small multiples ----
fig, axes = plt.subplots(2, 3, figsize=(14, 7), sharex=True, sharey=True)
axes = axes.flatten()

for ax, name in zip(axes, top6):
    sub = mean_by_year[mean_by_year.ta_name == name]
    ax.plot(sub["year"], sub["radiance_mean"], marker="o", lw=2)
    ax.set_title(name, fontsize=11)
    ax.grid(alpha=0.3)

fig.suptitle("VIIRS Night-time Radiance Trends (2014–2023)", fontsize=14)
fig.text(0.5, 0.04, "Year", ha="center")
fig.text(0.04, 0.5, "Mean radiance (nW/cm²·sr)", va="center", rotation="vertical")
fig.tight_layout(rect=[0.03, 0.05, 1, 0.95])

out_png = OUT_DIR / "viirs_timeseries_top6.png"
plt.savefig(out_png, dpi=200)
print(f"📈 Saved → {out_png}")