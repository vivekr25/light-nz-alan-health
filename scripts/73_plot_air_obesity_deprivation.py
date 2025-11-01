# scripts/73_plot_air_obesity_deprivation.py
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.io as pio

IN   = Path("data_proc/air_obesity_deprivation_2023.csv")
OUTD = Path("data_proc")
DOCS = Path("docs")

OUTD.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(IN)

# ---- tidy / guards ----
need = ["health_region", "ethnicity", "pm25_ugm3_2023", "obesity_rate", "nzdep_9_10_share"]
missing_cols = [c for c in need if c not in df.columns]
if missing_cols:
    raise SystemExit(f"❌ Missing columns in {IN}: {missing_cols}")

df = df.dropna(subset=["pm25_ugm3_2023", "obesity_rate", "nzdep_9_10_share"]).copy()

# Nice display columns
df["obesity_pct"] = df["obesity_rate"] * 100.0
df["dep_pct"]     = df["nzdep_9_10_share"] * 100.0

# Common labels
x_label = "PM₂.₅ annual mean (µg/m³)"
y_label = "Obesity rate (% of adults)"
c_label = "NZDep (Deciles 9–10, % of pop.)"

# ---------- (A) Overall scatter ----------
fig_all = px.scatter(
    df,
    x="pm25_ugm3_2023",
    y="obesity_pct",
    color="nzdep_9_10_share",
    color_continuous_scale="Viridis",
    hover_data={
        "health_region": True,
        "ethnicity": True,
        "pm25_ugm3_2023": ":.2f",
        "obesity_pct": ":.1f",
        "dep_pct": ":.1f",
        "nzdep_9_10_share": False,  # hide raw proportion in tooltip
    },
    symbol="health_region",
    title="Air pollution × Obesity × Deprivation (2023 • 2020/21)",
    labels={
        "pm25_ugm3_2023": x_label,
        "obesity_pct": y_label,
        "nzdep_9_10_share": c_label,
        "health_region": "Health region",
        "ethnicity": "Ethnicity",
    },
)
fig_all.update_traces(marker=dict(size=14, line=dict(width=0.6, color="rgba(0,0,0,0.35)")))
fig_all.update_coloraxes(colorbar=dict(title=c_label, ticksuffix="%"))
fig_all.update_layout(
    margin=dict(l=20, r=20, t=70, b=40),
    legend=dict(orientation="h", y=1.05, x=1.0, xanchor="right"),
)

# Save
png_all  = OUTD / "air_obesity_dep_scatter_2023.png"
html_all = DOCS / "air_obesity_dep_scatter_2023.html"
fig_all.write_image(png_all.as_posix(), width=1400, height=900, scale=2, engine="kaleido")
pio.write_html(fig_all, file=html_all.as_posix(), include_plotlyjs="cdn", full_html=True)
print(f"✅ Saved overall scatter → {png_all}")
print(f"✅ Saved interactive → {html_all}")

# ---------- (B) Small multiples by ethnicity ----------
order_eth = ["Māori", "Pacific", "Asian", "European/Other"]
df["ethnicity"] = pd.Categorical(df["ethnicity"], categories=order_eth, ordered=True)

fig_fac = px.scatter(
    df.sort_values(["ethnicity", "health_region"]),
    x="pm25_ugm3_2023",
    y="obesity_pct",
    color="nzdep_9_10_share",
    color_continuous_scale="Viridis",
    symbol="health_region",
    facet_col="ethnicity",
    facet_col_wrap=2,  # 2 columns layout
    hover_data={
        "health_region": True,
        "pm25_ugm3_2023": ":.2f",
        "obesity_pct": ":.1f",
        "dep_pct": ":.1f",
        "nzdep_9_10_share": False,
        "ethnicity": False,
    },
    title="PM₂.₅ vs Obesity — faceted by Ethnicity (colour = NZDep 9–10 share)",
    labels={
        "pm25_ugm3_2023": x_label,
        "obesity_pct": y_label,
        "nzdep_9_10_share": c_label,
        "health_region": "Health region",
    },
)
fig_fac.for_each_annotation(lambda a: a.update(text=a.text.replace("ethnicity=", "")))
fig_fac.update_traces(marker=dict(size=12, line=dict(width=0.6, color="rgba(0,0,0,0.35)")))
fig_fac.update_coloraxes(colorbar=dict(title=c_label, ticksuffix="%"))
fig_fac.update_layout(
    margin=dict(l=20, r=20, t=70, b=40),
    legend=dict(orientation="h", y=1.05, x=1.0, xanchor="right"),
)

# Save
png_fac  = OUTD / "air_obesity_dep_facets_by_ethnicity_2023.png"
html_fac = DOCS / "air_obesity_dep_facets_by_ethnicity_2023.html"
fig_fac.write_image(png_fac.as_posix(), width=1600, height=1100, scale=2, engine="kaleido")
pio.write_html(fig_fac, file=html_fac.as_posix(), include_plotlyjs="cdn", full_html=True)
print(f"✅ Saved facets → {png_fac}")
print(f"✅ Saved interactive → {html_fac}")

print("\nTip: Publish the interactive HTML via GitHub Pages (already set to /docs).")