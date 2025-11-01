# scripts/54_plot_small_multiples_by_region.py
import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

IN = "data_proc/obesity_vs_brightness_by_region.csv"
OUT = "data_proc/obesity_vs_brightness_small_multiples.png"

# ---------- load & tidy ----------
df = pd.read_csv(IN)

# Keep the four Health NZ regions; drop the national 'All' rollup if present
df = df[df["health_region"].ne("All")].copy()

# Ensure consistent region ordering left->right, top->bottom
region_order = ["Te Tai Tokerau", "Te Ikaroa", "Te Manawa Taki", "Te Waipounamu"]
# If any are missing, fall back to whatever exists (preserving the known order first)
present = [r for r in region_order if r in df["health_region"].unique()]
for r in df["health_region"].unique():
    if r not in present:
        present.append(r)
df["health_region"] = pd.Categorical(df["health_region"], present, ordered=True)

# Ethnicity order & marker style
eth_order = ["Asian", "European/Other", "Māori", "Pacific"]
df["ethnicity"] = pd.Categorical(df["ethnicity"], eth_order, ordered=True)
markers = {"Asian":"o", "European/Other":"s", "Māori":"^", "Pacific":"D"}

# Axis ranges (pad a little so labels fit)
xpad = 0.1
ypad = 0.01
xmin = df["radiance_mean"].min() - xpad
xmax = df["radiance_mean"].max() + xpad
ymin = df["obesity_rate"].min() - ypad
ymax = df["obesity_rate"].max() + ypad

# ---------- plot ----------
fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True, sharey=True)
axes = axes.flatten()

for ax, region in zip(axes, present):
    sub = df[df["health_region"] == region].copy()
    if sub.empty:
        ax.set_visible(False)
        continue

    for eth in eth_order:
        s = sub[sub["ethnicity"] == eth]
        if s.empty:
            continue
        ax.scatter(
            s["radiance_mean"], s["obesity_rate"],
            label=eth, marker=markers.get(eth, "o"), s=90, alpha=0.9
        )
        # add a light label next to each point
        for _, r in s.iterrows():
            ax.text(
                r["radiance_mean"] + 0.02, r["obesity_rate"] + 0.001, eth,
                fontsize=9
            )

    ax.set_title(region, fontsize=12, pad=6)
    ax.grid(alpha=0.2, linewidth=0.6)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

# Common axes/legend/suptitle
for ax in axes[2:]:
    ax.set_xlabel("Mean night-time brightness (nW/cm²·sr)")
for ax in axes[::2]:
    ax.set_ylabel("Obesity rate (proportion of adults)")

# Single legend (outside top-right)
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, title="Ethnicity", loc="upper center", ncol=4, frameon=False, bbox_to_anchor=(0.5, 1.02))
fig.suptitle("Obesity vs Night-time Brightness by Ethnicity — Small Multiples by Health NZ Region (2020/21)", y=1.06, fontsize=14)
fig.tight_layout(rect=[0, 0, 1, 0.98])

Path("data_proc").mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=200)
print(f"✅ Saved → {OUT}")