import pandas as pd
import plotly.express as px
import plotly.io as pio
from pathlib import Path

IN_XLS = "data_raw/lawa_air-quality-download-data_2016-2024.xlsx"

print("Loading LAWA data …")
xls = pd.ExcelFile(IN_XLS, engine="openpyxl")
# pick the “Monitoring dataset” sheet (or the first sheet if renamed)
sheet = [s for s in xls.sheet_names if "monitor" in s.lower() or "dataset" in s.lower()]
sheet = sheet[0] if sheet else xls.sheet_names[0]
df = xls.parse(sheet)

# Tidy columns
df = df.rename(columns={
    "Region": "region",
    "Indicator": "indicator",
    "Sample Date": "sample_date",
    "Concentration (ug/m3)": "value",
    "Latitude": "lat",
    "Longitude": "lon",
})

# Keep 2023 rows for PM10 / PM2.5 and valid coords
df["sample_date"] = pd.to_datetime(df["sample_date"], errors="coerce")
df = df[df["sample_date"].dt.year == 2023]
df = df[df["indicator"].isin(["PM10", "PM2.5"])]
df = df.dropna(subset=["region", "lat", "lon", "value"])

# Region stats (mean value per indicator) + simple region centroid from site coords
centroids = df.groupby("region", as_index=False)[["lat", "lon"]].mean()
vals = df.pivot_table(index=["region"], columns="indicator", values="value", aggfunc="mean").reset_index()
g = pd.merge(vals, centroids, on="region", how="left")

# Fill if one of the pollutants is missing
for col in ["PM10", "PM2.5"]:
    if col not in g:
        g[col] = pd.NA

# Build map
size_col = "PM2.5"
g["size"] = g[size_col].fillna(g[size_col].median() if g[size_col].notna().any() else 5) * 4

fig = px.scatter_mapbox(
    g, lat="lat", lon="lon",
    size="size",
    color="PM2.5",
    color_continuous_scale="Viridis",
    hover_name="region",
    hover_data={"PM10":":.1f", "PM2.5":":.1f", "lat":False, "lon":False, "size":False},
    zoom=4.3, height=720
)
fig.update_layout(
    mapbox_style="open-street-map",
    margin=dict(l=10,r=10,t=60,b=10),
    title=dict(text="NZ air quality (2023) — PM2.5 by region (bubble size & colour)", x=0.5),
    coloraxis_colorbar=dict(title="PM2.5 (µg/m³)")
)

# Save
Path("docs").mkdir(exist_ok=True)
out_html = "docs/air_pm_map_2023.html"
pio.write_html(fig, out_html, include_plotlyjs="cdn", full_html=True)
print(f"✅ Wrote {out_html}")

# Optional PNG (requires kaleido)
try:
    pio.write_image(fig, "docs/air_pm_map_2023.png", width=1400, height=800, scale=2, engine="kaleido")
    print("🖼️ Wrote docs/air_pm_map_2023.png")
except Exception as e:
    print("ℹ️ PNG export skipped:", e)
