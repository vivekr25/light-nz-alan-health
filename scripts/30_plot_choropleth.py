import json
import pandas as pd
import plotly.express as px

# 1) Load data
df = pd.read_csv("data_proc/viirs_ta_annual_2021_with_names.csv")

# 2) Load TA GeoJSON
with open("data_raw/ta2025.geojson", "r") as f:
    gj = json.load(f)

# IMPORTANT: match the GeoJSON property that holds the TA code.
# From your DBF, the code field is TA2025_V1_. Many exporters keep that name.
feature_key = "properties.TA2025_V1_"

# 3) Make sure types match
df["ta_code"] = pd.to_numeric(df["ta_code"], errors="coerce")

# 4) Choropleth
fig = px.choropleth_mapbox(
    df,
    geojson=gj,
    featureidkey=feature_key,   # GeoJSON key
    locations="ta_code",        # column in df
    color="radiance_mean",
    hover_name="ta_name",
    color_continuous_scale="viridis",
    mapbox_style="carto-positron",
    zoom=4.7, center={"lat": -41.3, "lon": 174.7},
    opacity=0.75,
    title="NZ night-time brightness by Territorial Authority (VIIRS 2021)"
)
fig.show()