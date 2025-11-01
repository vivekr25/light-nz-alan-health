# scripts/32_dual_maps.py
import json
import pandas as pd
import plotly.express as px
import plotly.io as pio
from plotly.subplots import make_subplots
from shapely.geometry import shape

# ---------- 1) Load data ----------
df = pd.read_csv("data_proc/viirs_ta_annual_2021_with_names.csv")
df["ta_code_str"] = (
    pd.to_numeric(df["ta_code"], errors="coerce").astype("Int64").astype(str).str.zfill(3)
)

with open("data_raw/ta2025_ms_5pct.geojson") as f:
    gj = json.load(f)

# ---------- 2) Quantile bands ----------
bands = ["Very low", "Low", "Medium", "High", "Very high"]
df["radiance_band"] = pd.qcut(df["radiance_mean"], 5, labels=bands)

# ---------- 3) Geometric centroids for labels ----------
code_to_centroid = {}
for feat in gj["features"]:
    code = str(feat["properties"]["TA2025_V1_"]).zfill(3)
    cent = shape(feat["geometry"]).centroid
    code_to_centroid[code] = (cent.y, cent.x)   # (lat, lon)

labels = []
for _, r in df.iterrows():
    code = r["ta_code_str"]
    if code in code_to_centroid:
        lat, lon = code_to_centroid[code]
        labels.append({"ta_name": r["ta_name"], "lat": lat, "lon": lon})
labels_df = pd.DataFrame(labels)

# ---------- 4) Make subplots (two Mapbox panes) ----------
fig = make_subplots(
    rows=1, cols=2,
    specs=[[{"type": "mapbox"}, {"type": "mapbox"}]],
    subplot_titles=("Relative (quantile bands)", "Absolute (mean radiance)")
)

# ---------- 5) LEFT: Quantile bands ----------
left = px.choropleth_mapbox(
    df, geojson=gj, featureidkey="properties.TA2025_V1_", locations="ta_code_str",
    color="radiance_band", color_discrete_sequence=px.colors.sequential.Viridis,
    hover_name="ta_name", hover_data={"radiance_mean": False}
)
# no opacity here (unsupported on this trace type)
left.update_traces(
    marker_line_color="black",
    marker_line_width=0.4,
    hovertemplate="<b>%{hovertext}</b><br>"
                  "Band: %{customdata[0]}<br>"
                  "Mean radiance: %{customdata[1]:.3f} nW/cm²·sr",
    customdata=df[["radiance_band", "radiance_mean"]],
)
for tr in left.data:
    fig.add_trace(tr, row=1, col=1)

# labels over LEFT (no hover, no legend)
fig.add_scattermapbox(
    lat=labels_df["lat"], lon=labels_df["lon"], text=labels_df["ta_name"],
    mode="text", name="", hoverinfo="skip", showlegend=False,
    textfont=dict(size=10, color="#1e1e1e"), row=1, col=1
)

# ---------- 6) RIGHT: Continuous radiance ----------
right = px.choropleth_mapbox(
    df, geojson=gj, featureidkey="properties.TA2025_V1_", locations="ta_code_str",
    color="radiance_mean", color_continuous_scale="Viridis",
    hover_name="ta_name", hover_data={"radiance_mean": ":.3f"}
)
right.update_traces(
    marker_line_color="black",
    marker_line_width=0.4,
    hovertemplate="<b>%{hovertext}</b><br>"
                  "Mean radiance: %{z:.3f} nW/cm²·sr"
)
for tr in right.data:
    fig.add_trace(tr, row=1, col=2)

# labels over RIGHT (no hover, no legend)
fig.add_scattermapbox(
    lat=labels_df["lat"], lon=labels_df["lon"], text=labels_df["ta_name"],
    mode="text", name="", hoverinfo="skip", showlegend=False,
    textfont=dict(size=10, color="#1e1e1e"), row=1, col=2
)

# ---------- 7) Shared layout (both panes) ----------
center = {"lat": -41.3, "lon": 174.7}
fig.update_layout(
    title=dict(
        text="NZ night-time brightness by Territorial Authority (VIIRS 2021)",
        x=0.5, xanchor="center"
    ),
    margin=dict(l=10, r=10, t=60, b=40),
    # same clean basemap + same camera for both subplots
    mapbox_style="carto-positron",
    mapbox=dict(center=center, zoom=4.9),
    mapbox2=dict(style="carto-positron", center=center, zoom=4.9),
    coloraxis_colorbar=dict(title="Mean radiance\n(nW/cm²·sr)")
)

# Footer annotation
fig.add_annotation(
    text="Data: NASA VIIRS Night Lights • Map: Stats NZ TA 2025",
    showarrow=False, xref="paper", yref="paper",
    x=0, y=0, xanchor="left", yanchor="bottom",
    font=dict(size=12, color="gray")
)

# ---------- 8) Save ----------
out_path = "data_proc/ta_dual_maps.html"
pio.write_html(fig, file=out_path, include_plotlyjs="cdn", full_html=True)
print(f"✅ Saved → {out_path}")