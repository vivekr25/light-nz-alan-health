# scripts/30_plot_choropleth.py
import json
import pandas as pd
import plotly.express as px
import plotly.io as pio
from shapely.geometry import shape

# 1) Load data and make TA code strings like '001','011',...
df = pd.read_csv("data_proc/viirs_ta_annual_2021_with_names.csv")
df["ta_code_str"] = (
    pd.to_numeric(df["ta_code"], errors="coerce")
      .astype("Int64").astype(str).str.zfill(3)
)

# 2) Load small GeoJSON (fast in browser)
with open("data_raw/ta2025_ms_5pct.geojson") as f:
    gj = json.load(f)

# 3) Make 5 quantile bands for strong visual contrast
bands = ["Very low", "Low", "Medium", "High", "Very high"]
df["radiance_band"] = pd.qcut(df["radiance_mean"], 5, labels=bands)

# 4) Choropleth over a clean basemap (no token needed)
fig = px.choropleth_mapbox(
    df,
    geojson=gj,
    featureidkey="properties.TA2025_V1_",  # field in GeoJSON
    locations="ta_code_str",               # field in df
    color="radiance_band",                 # discrete legend
    hover_name="ta_name",
    hover_data={"radiance_mean": False},   # we’ll format our own hover
    color_discrete_sequence=px.colors.sequential.Viridis,
    mapbox_style="carto-positron",
    center={"lat": -41.3, "lon": 174.7},
    zoom=4.9,
    opacity=0.78,
    title="NZ night-time brightness by Territorial Authority (VIIRS 2021)"
)

# Thin outlines and tidy legend order
fig.update_traces(marker_line_color="black", marker_line_width=0.4)
fig.update_layout(
    legend_title_text="Brightness band",
    legend_traceorder="normal"
)

# Custom hover for polygons (TA name, band, value to 3 d.p.)
fig.update_traces(
    hovertemplate=(
        "<b>%{hovertext}</b><br>"
        "Band: %{customdata[0]}<br>"
        "Mean radiance: %{customdata[1]:.3f} nW/cm²·sr"
    ),
    # pass band + value in customdata for the template
    customdata=df[["radiance_band", "radiance_mean"]]
)

# 5) Compute true geometric centroids for label placement (shapely)
code_to_centroid = {}
for feat in gj["features"]:
    code = str(feat["properties"]["TA2025_V1_"]).zfill(3)
    geom = shape(feat["geometry"])
    lon, lat = geom.centroid.x, geom.centroid.y
    code_to_centroid[code] = (lat, lon)

labels = []
for _, r in df.iterrows():
    code = r["ta_code_str"]
    if code in code_to_centroid:
        lat, lon = code_to_centroid[code]
        labels.append({"ta_name": r["ta_name"], "lat": lat, "lon": lon})
labels_df = pd.DataFrame(labels)

# 6) Add labels ABOVE polygons, with no hover and no legend
fig.add_scattermapbox(
    lat=labels_df["lat"],
    lon=labels_df["lon"],
    text=labels_df["ta_name"],
    mode="text",
    textfont=dict(size=10, color="#1e1e1e"),
    textposition="middle center",
    hoverinfo="skip",   # ← no lat/lon popup
    showlegend=False,
    name=""             # ← no “trace 5”
)
# 7) Save interactive HTML (CDN keeps file small)
fig.update_layout(
    title=dict(
        text="NZ night-time brightness by Territorial Authority (VIIRS 2021)",
        x=0.5, xanchor="center"
    ),
    annotations=[
        dict(
            text="Data: NASA VIIRS Night Lights • Map: Stats NZ TA 2025",
            showarrow=False,
            xref="paper", yref="paper",
            x=0, y=0,               # bottom-left corner
            xanchor="left", yanchor="bottom",
            font=dict(size=12, color="gray")
        )
    ],
    margin=dict(l=10, r=10, t=50, b=40)
)
pio.write_html(
    fig,
    file="data_proc/ta_brightness_map.html",
    include_plotlyjs="cdn",
    full_html=True
)
print("✅ Saved → data_proc/ta_brightness_map.html")