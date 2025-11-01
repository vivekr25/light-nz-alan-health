# scripts/41_plot_timeseries.py
# Make time-series charts + small multiples + city vs district comparison.

from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

IN = Path("data_proc/viirs_ta_timeseries_2014_2023.csv")
OUT_DIR = Path("data_proc")
OUT_DIR.mkdir(parents=True, exist_ok=True)

if not IN.exists():
    raise SystemExit(f"Missing input: {IN}. Run scripts/40_concat_years.py first.")

df = pd.read_csv(IN)

# --- hygiene / types ---
df["viirs_year"] = pd.to_numeric(df["viirs_year"], errors="coerce").astype(int)
df["radiance_mean"] = pd.to_numeric(df["radiance_mean"], errors="coerce")

# If you currently only have 1 year, the script still runs; plots will be simple.
years_avail = sorted(df["viirs_year"].unique())
print("Years available:", years_avail)

# -------------------------------
# 1) National trend (mean + median)
# -------------------------------
nat = df.groupby("viirs_year")["radiance_mean"].agg(mean="mean", median="median").reset_index()

plt.figure(figsize=(8,4.5), dpi=150)
plt.plot(nat["viirs_year"], nat["mean"], marker="o", label="Mean")
plt.plot(nat["viirs_year"], nat["median"], marker="o", label="Median")
plt.title("NZ night-time radiance — national trend (VIIRS annual)")
plt.xlabel("Year")
plt.ylabel("Mean radiance (nW/cm²·sr)")
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
(OUT_DIR/"timeseries_national.png").unlink(missing_ok=True)
plt.savefig(OUT_DIR/"timeseries_national.png")
plt.close()
print("🖼  wrote data_proc/timeseries_national.png")

# ---------------------------------------------------
# 2) Small multiples: top 12 (by latest year available)
# ---------------------------------------------------
latest_year = df["viirs_year"].max()
latest = df[df["viirs_year"] == latest_year].dropna(subset=["radiance_mean"])
if latest.empty:
    print("No rows for latest year; skipping small multiples.")
else:
    top12 = latest.nlargest(12, "radiance_mean")[["ta_code", "ta_name"]].drop_duplicates()
    sel = df.merge(top12, on=["ta_code","ta_name"], how="inner").sort_values(["ta_name","viirs_year"])
    names = top12["ta_name"].tolist()

    n = len(names)
    cols = 4
    rows = (n + cols - 1) // cols if n else 1

    fig, axes = plt.subplots(rows, cols, figsize=(14, 8), dpi=150, sharex=True, sharey=True)
    axes = axes.flat if hasattr(axes, "flat") else [axes]

    for i, name in enumerate(names):
        sub = sel[sel["ta_name"] == name]
        ax = axes[i]
        ax.plot(sub["viirs_year"], sub["radiance_mean"], marker="o")
        ax.set_title(name, fontsize=9)
        ax.grid(alpha=0.2)
        if i // cols == rows - 1:
            ax.set_xlabel("Year")
        if i % cols == 0:
            ax.set_ylabel("Mean radiance")

    # clear leftover axes if any
    for j in range(len(names), rows*cols):
        axes[j].axis("off")

    fig.suptitle(f"Top 12 TAs by radiance in {latest_year} — small multiples", y=1.02, fontsize=12)
    plt.tight_layout()
    (OUT_DIR/"timeseries_small_multiples_top12.png").unlink(missing_ok=True)
    plt.savefig(OUT_DIR/"timeseries_small_multiples_top12.png", bbox_inches="tight")
    plt.close()
    print("🖼  wrote data_proc/timeseries_small_multiples_top12.png")

# ----------------------------------------------------------
# 3) City vs District comparison (distribution in latest year)
# ----------------------------------------------------------
one = df[df["viirs_year"] == latest_year].copy()
if one.empty:
    print("No rows for latest year; skipping City vs District boxplot.")
else:
    # Simple heuristic: names ending with ' City' are cities, others are districts
    one["ta_type"] = one["ta_name"].str.endswith(" City").map({True:"City", False:"District"})

    data_city = one.loc[one["ta_type"]=="City", "radiance_mean"].dropna()
    data_dist = one.loc[one["ta_type"]=="District", "radiance_mean"].dropna()

    if len(data_city) and len(data_dist):
        plt.figure(figsize=(7,4.5), dpi=150)
        plt.boxplot([data_city, data_dist], labels=["City", "District"], showfliers=False)
        plt.title(f"City vs District radiance distribution ({latest_year})")
        plt.ylabel("Mean radiance (nW/cm²·sr)")
        plt.grid(axis="y", alpha=0.3)
        plt.tight_layout()
        (OUT_DIR/"city_vs_district_boxplot.png").unlink(missing_ok=True)
        plt.savefig(OUT_DIR/"city_vs_district_boxplot.png")
        plt.close()
        print("🖼  wrote data_proc/city_vs_district_boxplot.png")

        # quick console summary
        print(f"\nSummary {latest_year}:")
        print("  Cities   — n = {:2d}, median = {:.3f}".format(len(data_city), data_city.median()))
        print("  Districts— n = {:2d}, median = {:.3f}".format(len(data_dist), data_dist.median()))
    else:
        print("Not enough City/District rows to make a boxplot; skipping.")