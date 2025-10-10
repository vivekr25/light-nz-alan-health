# scripts/31_single_map_toggle.py
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.io as pio
from plotly.subplots import make_subplots

# ----------------- data -----------------
df = pd.read_csv("data_proc/viirs_ta_annual_2021_with_names.csv")
df["ta_code_str"] = (
    pd.to_numeric(df["ta_code"], errors="coerce")
      .astype("Int64").astype(str).str.zfill(3)
)

with open("data_raw/ta2025_ms_5pct.geojson") as f:
    gj = json.load(f)

# quantile bands (relative view)
bands = ["Very low", "Low", "Medium", "High", "Very high"]
df["radiance_band"] = pd.qcut(df["radiance_mean"], 5, labels=bands)
df["band_idx"] = df["radiance_band"].cat.codes  # 0..4

# --- fast centroids (bbox midpoints to avoid heavy deps) ---
code_to_centroid = {}
def _walk(c, xs, ys):
    if isinstance(c, (list, tuple)) and c:
        if isinstance(c[0], (float, int)):
            xs.append(c[0]); ys.append(c[1])
        else:
            for q in c: _walk(q, xs, ys)

for feat in gj["features"]:
    code = str(feat["properties"]["TA2025_V1_"]).zfill(3)
    xs, ys = [], []
    _walk(feat["geometry"]["coordinates"], xs, ys)
    if xs and ys:
        lon = (min(xs) + max(xs)) / 2
        lat = (min(ys) + max(ys)) / 2
        code_to_centroid[code] = (lat, lon)

labels_df = pd.DataFrame(
    [{"ta_name": r.ta_name, "lat": code_to_centroid[r.ta_code_str][0],
      "lon": code_to_centroid[r.ta_code_str][1]}
     for _, r in df.iterrows() if r.ta_code_str in code_to_centroid]
)

# ----------------- traces -----------------
# 5 fixed colors sampled from Viridis to keep the legend stable
cat_src = px.colors.sequential.Viridis
cat_colors = [cat_src[int(i*(len(cat_src)-1)/4)] for i in range(5)]

# Relative (quantiles) — numeric + custom colorbar labels
rel_fig = px.choropleth_mapbox(
    df, geojson=gj, featureidkey="properties.TA2025_V1_", locations="ta_code_str",
    color="band_idx", color_continuous_scale=cat_colors, hover_name="ta_name",
)
rel_tr = rel_fig.data[0]
rel_tr.update(
    marker_line_color="black", marker_line_width=0.4,
    hovertemplate="<b>%{hovertext}</b><br>"
                  "Band: %{customdata[0]}<br>"
                  "Mean radiance: %{customdata[1]:.3f} nW/cm²·sr",
    customdata=df[["radiance_band","radiance_mean"]],
    coloraxis="coloraxis",  # important: bind to coloraxis
    name="Quantile bands"
)

# Absolute (continuous radiance) — uses coloraxis2
abs_fig = px.choropleth_mapbox(
    df, geojson=gj, featureidkey="properties.TA2025_V1_", locations="ta_code_str",
    color="radiance_mean", color_continuous_scale="Viridis", hover_name="ta_name",
)
abs_tr = abs_fig.data[0]
abs_tr.update(
    marker_line_color="black", marker_line_width=0.4,
    hovertemplate="<b>%{hovertext}</b><br>"
                  "Mean radiance: %{z:.3f} nW/cm²·sr",
    coloraxis="coloraxis2",
    name="Absolute radiance"
)

# ----------------- figure -----------------
fig = make_subplots(rows=1, cols=1, specs=[[{"type": "mapbox"}]])
fig.add_trace(rel_tr)          # index 0
fig.add_trace(abs_tr)          # index 1 (we’ll start hidden)
fig.data[1].visible = False

# labels on top
fig.add_scattermapbox(
    lat=labels_df["lat"], lon=labels_df["lon"], text=labels_df["ta_name"],
    mode="text", hoverinfo="skip", showlegend=False, name="",
    textfont=dict(size=10, color="#1e1e1e")
)

center = {"lat": -41.3, "lon": 174.7}
fig.update_layout(
    title=dict(
        text="NZ night-time brightness by TA (VIIRS 2021)",
        x=0.5, xanchor="center", y=0.98, yanchor="top"
    ),
    mapbox_style="carto-positron",
    mapbox=dict(center=center, zoom=4.9),
    margin=dict(l=10, r=10, t=110, b=50),   # extra space for title + buttons
    legend_title_text="",
    # categorical color axis (for quantile bands)
    coloraxis=dict(
        cmin=-0.5, cmax=4.5,
        colorscale=[[i/4, c] for i, c in enumerate(cat_colors)],
        colorbar=dict(
            title="Brightness band",
            tickmode="array", tickvals=[0,1,2,3,4], ticktext=bands,
        ),
    ),
    # continuous color axis (for absolute radiance)
    coloraxis2=dict(
        colorscale="Viridis",
        colorbar=dict(title="Mean radiance (nW/cm²·sr)")
    ),
)

# --- buttons: move to top-right so they never cover the title ---
fig.update_layout(
    updatemenus=[dict(
        type="buttons", direction="right",
        x=1.0, xanchor="right", y=1.13, yanchor="top",  # top-right
        pad=dict(t=6, r=6, l=6, b=6),
        buttons=[
            dict(label="Relative (quantiles)",
                 method="update",
                 args=[{"visible": [True, False, True]}]),
            dict(label="Absolute (radiance)",
                 method="update",
                 args=[{"visible": [False, True, True]}]),
        ],
        showactive=True
    )]
)

# subtle global typography + colorbar title styling
fig.update_layout(
    title_font=dict(size=20, color="#1a1a1a", family="Arial"),
    font=dict(family="Arial", size=12, color="#2f2f2f"),
    coloraxis_colorbar=dict(title_side="right", title_font=dict(size=14)),
    coloraxis2_colorbar=dict(title_side="right", title_font=dict(size=14)),
)

# footer (appears in both HTML and PNG)
fig.add_annotation(
    text="Data: NASA VIIRS Night Lights • Map: Stats NZ TA 2025",
    showarrow=False, xref="paper", yref="paper",
    x=0, y=0, xanchor="left", yanchor="bottom",
    font=dict(size=12, color="gray")
)

# ----------------- outputs -----------------
Path("data_proc").mkdir(parents=True, exist_ok=True)

# Interactive HTML
out_html = "data_proc/ta_single_map_toggle.html"
pio.write_html(fig, file=out_html, include_plotlyjs="cdn", full_html=True)
print(f"✅ Saved → {out_html}")

# Static PNG (solid background avoids blank tiles)
fig_png = pio.from_json(pio.to_json(fig))
fig_png.update_layout(mapbox_style="white-bg")
out_png = "data_proc/ta_brightness_map_1600.png"
pio.write_image(fig_png, out_png, width=1600, height=900, scale=2, engine="kaleido")
print(f"🖼️ Saved → {out_png}")