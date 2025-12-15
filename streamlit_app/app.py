# streamlit_app/app.py
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# -------------------------------------------------
# App config
# -------------------------------------------------
st.set_page_config(
    page_title="Alan-NZ • Environment & Health",
    page_icon="🌌",
    layout="wide",
)

# -------------------------------------------------
# Paths (relative to repo root)
# -------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DATA_PROC = ROOT / "data_proc"
DATA_RAW = ROOT / "data_raw"
DOCS = ROOT / "docs"  # (fallbacks if you ever export figs to /docs)

# -------------------------------------------------
# Helpers
# -------------------------------------------------
@st.cache_data(show_spinner=False)
def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)

@st.cache_data(show_spinner=False)
def load_json(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)

@st.cache_data(show_spinner=False)
def load_lawa_annual(path_xlsx: Path) -> pd.DataFrame:
    """
    Load LAWA Excel and return annual means by region for a chosen year.
    Works with the 2016–2024 download you saved.
    """
    import re
    xls = pd.ExcelFile(path_xlsx, engine="openpyxl")
    sheets = xls.sheet_names
    pref = [s for s in sheets if re.search(r"(data|monitor|dataset|pm|meas|observ)", s, re.I)]
    sheet = pref[0] if pref else sheets[0]
    df = xls.parse(sheet)

    # Normalise columns
    df.columns = [c.strip() for c in df.columns]
    col_region = [c for c in df.columns if c.lower() in ("region", "regional council", "council")][0]
    col_ind = [c for c in df.columns if "indicator" in c.lower()][0]
    col_date = [c for c in df.columns if "sample date" in c.lower()][0]
    col_value = [c for c in df.columns if "concentration" in c.lower()][0]

    df[col_date] = pd.to_datetime(df[col_date], errors="coerce")
    df["year"] = df[col_date].dt.year
    df = df[df["year"].between(2016, 2100)]

    annual = (
        df.groupby([col_region, "year", col_ind], as_index=False)[col_value]
          .mean()
          .rename(columns={
              col_region: "region",
              col_ind: "indicator",
              col_value: "value_ugm3",
          })
    )
    return annual

def note_missing(path: Path, extra_text: str = ""):
    st.warning(f"Missing file: `{path.as_posix()}`. {extra_text}".strip())

def pollutant_options_from(df: pd.DataFrame) -> dict:
    """
    Return a mapping like {"PM2.5": "pm25_ugm3_2023", "PM10": "pm10_ugm3_2023"}
    by scanning dataframe columns (robust to naming).
    """
    choices = {}
    for c in df.columns:
        cl = c.lower().replace(".", "").replace("-", "_")
        if "pm25" in cl or "pm2_5" in cl:
            if "PM2.5" not in choices or ("2023" in c and "2023" not in choices.get("PM2.5", "")):
                choices["PM2.5"] = c
        if "pm10" in cl:
            if "PM10" not in choices or ("2023" in c and "2023" not in choices.get("PM10", "")):
                choices["PM10"] = c
    return choices

# -------------------------------------------------
# Sidebar
# -------------------------------------------------
st.sidebar.title("Alan-NZ")
st.sidebar.caption("Environment ↔ Health • Aotearoa")
page = st.sidebar.radio(
    "Navigate",
    ["Key insights", "Night-lights", "Air quality", "Health × Night-lights", "Equity lens: PM₂.₅ × Obesity", "About"]
)
# -------------------------------------------------
# Key insights page
# -------------------------------------------------
if page == "Key insights":
    st.title("✨ Key insights (quick read)")
    st.caption("A small set of takeaways backed by what’s in this repo. Explore details via the other tabs.")

    st.markdown(
        """
        **Executive summary**

        **1) Night-time brightness clusters sharply in major urban centres.**  
        The brightest TAs are consistently large metro areas, with a steep drop beyond them.

        **2) Air pollution varies by pollutant and region.**  
        PM₂.₅ and PM₁₀ do not always rank regions the same way, suggesting different sources and exposure dynamics.

        **3) Equity patterns matter within regions.**  
        Obesity prevalence varies by ethnicity within the same health region and often overlaps with deprivation and higher exposure context.

        *These are exploratory comparisons, not causal claims.*
        """
    )

    # ---------- Insight 1: Brightness hotspots (TA) ----------
    st.subheader("1) Where are the brightest night-time areas?")
    csv_path = DATA_PROC / "viirs_ta_annual_2021_with_names.csv"
    gj_path = DATA_RAW / "ta2025_ms_5pct.geojson"

    if not csv_path.exists():
        note_missing(csv_path, "Generate/commit viirs_ta_annual_2021_with_names.csv to data_proc/.")
    else:
        df = load_csv(csv_path).copy()

        # Make sure radiance_mean exists
        if "radiance_mean" not in df.columns:
            st.error("Expected column `radiance_mean` in VIIRS CSV but didn’t find it.")
        else:
            # Top 10 brightest TAs
            top_n = 10
            top = df.sort_values("radiance_mean", ascending=False).head(top_n)

            # Show a neat table
            cols = [c for c in ["ta_name", "ta_code", "radiance_mean"] if c in top.columns]
            st.dataframe(
                top[cols].rename(columns={"radiance_mean": "Mean radiance"}),
                use_container_width=True,
                hide_index=True
            )

            # A simple bar chart (fast and readable)
            if "ta_name" in top.columns:
                fig = px.bar(
                    top.sort_values("radiance_mean", ascending=True),
                    x="radiance_mean",
                    y="ta_name",
                    orientation="h",
                    labels={"radiance_mean": "Mean night-time brightness (radiance)", "ta_name": "Territorial Authority"},
                    title="Top 10 brightest TAs (VIIRS 2021)"
                )
                fig.update_layout(height=420, margin=dict(l=10, r=10, t=60, b=10))
                st.plotly_chart(fig, width="stretch")

    st.markdown(
        "- **Why it matters:** night-time brightness is a decent proxy for urbanisation, activity, and built environment.\n"
        "- **What to check next:** compare these areas in the **Health × Night-lights** tab."
    )

    st.divider()

    # ---------- Insight 2: PM2.5 vs PM10 regional ranking ----------
    st.subheader("2) Which regions have the highest PM₂.₅ / PM₁₀ annual means?")
    xlsx_path = DATA_RAW / "lawa_air-quality-download-data_2016-2024.xlsx"

    if not xlsx_path.exists():
        note_missing(xlsx_path, "Commit the LAWA Excel file to data_raw/.")
    else:
        annual = load_lawa_annual(xlsx_path)

        # Choose latest year available
        latest_year = int(annual["year"].max())
        st.caption(f"Using latest year available in the file: {latest_year}")

        c1, c2 = st.columns([1, 2])
        with c1:
            metric = st.radio("Pollutant", ["PM2.5", "PM10"], horizontal=True)

        pick = annual[
            annual["indicator"].str.contains(metric, case=False, regex=False)
            & (annual["year"] == latest_year)
        ].copy()

        pick = pick.sort_values("value_ugm3", ascending=False)

        # Show top 5 regions
        top5 = pick.head(5)[["region", "value_ugm3"]].rename(columns={"value_ugm3": "µg/m³"})
        st.dataframe(top5, use_container_width=True, hide_index=True)

        fig = px.bar(
            pick.head(12),
            x="region",
            y="value_ugm3",
            labels={"value_ugm3": "µg/m³", "region": "Region"},
            title=f"Top regions by {metric} (annual mean, {latest_year})"
        )
        fig.update_layout(xaxis_tickangle=-25, height=420, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig, width="stretch")

    st.markdown(
        "- **Why it matters:** long-term exposure to particulate pollution is linked with respiratory and cardiovascular risk.\n"
        "- **What to check next:** open the **Equity lens** tab to compare pollution with obesity and deprivation."
    )

    st.divider()

    # ---------- Insight 3: Equity lens headline numbers ----------
    st.subheader("3) Equity lens headline: PM₂.₅ × obesity patterns (by ethnicity within regions)")
    csv_merged = DATA_PROC / "air_obesity_by_health_region_2023.csv"

    if not csv_merged.exists():
        note_missing(csv_merged, "Run scripts/71_merge_pm25_obesity_by_health_region.py to create it.")
    else:
        eq = load_csv(csv_merged).copy()
        eq.columns = [c.strip().replace(" ", "_").lower() for c in eq.columns]

        pol_map = pollutant_options_from(eq)
        pol_col = pol_map.get("PM2.5") or next(iter(pol_map.values()), None)

        need = {"health_region", "ethnicity", "obesity_rate"}
        if pol_col is None or not need.issubset(eq.columns):
            st.error("Equity dataset is missing expected columns. Check your merge script output.")
        else:
            # Find the "highest obesity" row for each health region
            worst = (
                eq.dropna(subset=[pol_col, "obesity_rate"])
                  .sort_values(["health_region", "obesity_rate"], ascending=[True, False])
                  .groupby("health_region", as_index=False)
                  .head(1)
            )

            show_cols = ["health_region", "ethnicity", pol_col, "obesity_rate"]
            pretty = worst[show_cols].rename(columns={
                pol_col: "PM2.5 (µg/m³, 2023)",
                "obesity_rate": "Obesity rate (2020/21)"
            })

            st.dataframe(pretty, use_container_width=True, hide_index=True)

            st.markdown(
                "Use this as a **starting point** for questions like:\n"
                "- Do the highest obesity rates within a region line up with higher PM₂.₅?\n"
                "- Does deprivation (NZDep) appear to amplify both?"
            )

    st.caption("Note: These are observational comparisons, not proof of cause and effect.")

    # ---------- Data sources & interpretation ----------
    with st.expander("📚 Data sources & interpretation notes"):
        st.markdown(
            """
            **Data sources**
            - **NASA VIIRS Night Lights** — annual composites (2021)
            - **Stats NZ** — Territorial Authority boundaries (TA 2025)
            - **LAWA** — air quality monitoring data (2016–2024)
            - **Ministry of Health (NZ)** — adult obesity prevalence (2020/21)

            **Interpretation notes**
            - Visuals show **associations and patterns**, not causal relationships.
            - Analyses use **aggregated regional data** (TA or health-region level).
            - Night-time light intensity is a **proxy for built environment activity**,
              not a direct measure of individual exposure or behaviour.
            - Air-quality values are **regional annual means** and do not reflect
              individual-level exposure or mobility.
            - Data years differ slightly across sources and should be interpreted
              as broad structural patterns rather than point-in-time comparisons.
            """
        )


# -------------------------------------------------
# Night-lights page
# -------------------------------------------------
elif page == "Night-lights":
    st.title("🌃 Night-time brightness by Territorial Authority (VIIRS 2021)")

    csv_path = DATA_PROC / "viirs_ta_annual_2021_with_names.csv"
    gj_path = DATA_RAW / "ta2025_ms_5pct.geojson"

    if not csv_path.exists():
        note_missing(csv_path, "Run your choropleth script or commit the CSV.")
    elif not gj_path.exists():
        note_missing(gj_path, "Commit the TA 2025 GeoJSON to the repo.")
    else:
        df = load_csv(csv_path).copy()
        df["ta_code_str"] = (
            pd.to_numeric(df["ta_code"], errors="coerce")
            .astype("Int64").astype(str).str.zfill(3)
        )
        bands = ["Very low", "Low", "Medium", "High", "Very high"]
        df["radiance_band"] = pd.qcut(df["radiance_mean"], 5, labels=bands)

        gj = load_json(gj_path)
        tab1, tab2 = st.tabs(["Relative (quantiles)", "Absolute (radiance)"])

        with tab1:
            fig_rel = px.choropleth_mapbox(
                df, geojson=gj, featureidkey="properties.TA2025_V1_",
                locations="ta_code_str",
                color="radiance_band",
                hover_name="ta_name",
                mapbox_style="carto-positron",
                center={"lat": -41.3, "lon": 174.7}, zoom=4.9,
            )
            fig_rel.update_traces(marker_line_color="black", marker_line_width=0.4)
            fig_rel.update_layout(
                height=680,
                margin=dict(l=0, r=0, t=60, b=10),
                legend=dict(orientation="h", y=0.02, x=0.99, xanchor="right"),
                mapbox=dict(center=dict(lat=-41.2, lon=173.0), zoom=4.2),
            )
            st.plotly_chart(fig_rel, width="stretch", config={"displayModeBar": True})

        with tab2:
            fig_abs = px.choropleth_mapbox(
                df, geojson=gj, featureidkey="properties.TA2025_V1_",
                locations="ta_code_str",
                color="radiance_mean", color_continuous_scale="Viridis",
                hover_name="ta_name",
                mapbox_style="carto-positron",
                center={"lat": -41.3, "lon": 174.7}, zoom=4.9,
            )
            fig_abs.update_traces(marker_line_color="black", marker_line_width=0.4)
            fig_abs.update_layout(
                height=680,
                margin=dict(l=0, r=0, t=60, b=10),
                legend=dict(orientation="h", y=0.02, x=0.99, xanchor="right"),
                mapbox=dict(center=dict(lat=-41.2, lon=173.0), zoom=4.2),
            )
            st.plotly_chart(fig_abs, width="stretch", config={"displayModeBar": True})

    st.caption("Data: NASA VIIRS Night Lights (2021), Stats NZ TA 2025")

# -------------------------------------------------
# Air quality page
# -------------------------------------------------
elif page == "Air quality":
    st.title("🌬️ PM₂.₅ / PM₁₀ — annual means by region")

    xlsx_path = DATA_RAW / "lawa_air-quality-download-data_2016-2024.xlsx"
    if not xlsx_path.exists():
        note_missing(xlsx_path, "Download from LAWA and save to data_raw/.")
    else:
        annual = load_lawa_annual(xlsx_path)
        year = st.slider(
            "Year",
            min_value=int(annual["year"].min()),
            max_value=int(annual["year"].max()),
            value=int(annual["year"].max())
        )
        metric = st.radio("Indicator", ["PM2.5", "PM10"], horizontal=True)

        pick = annual[annual["indicator"].str.contains(metric, case=False, regex=False)].copy()
        pick = pick[pick["year"] == year].copy().sort_values("value_ugm3", ascending=False)

        st.dataframe(
            pick[["region", "value_ugm3"]].rename(columns={"value_ugm3": "µg/m³"}),
            use_container_width=True, hide_index=True
        )

        fig = px.bar(
            pick, x="region", y="value_ugm3",
            color="value_ugm3", color_continuous_scale="Viridis",
            title=f"{metric} annual mean by region — {year}",
            labels={"value_ugm3": "µg/m³", "region": "Region"},
        )
        fig.update_layout(xaxis_tickangle=-30, coloraxis_showscale=True,
                          height=520, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig, width="stretch")

        st.caption("Source: LAWA air quality monitoring (download 2016–2024).")

# -------------------------------------------------
# Health × Night-lights page
# -------------------------------------------------
elif page == "Health × Night-lights":
    st.title("⚖️ Obesity vs night-time brightness")

    merged_csv = DATA_PROC / "obesity_vs_brightness_by_region.csv"

    if merged_csv.exists():
        df = load_csv(merged_csv)
        regions = [r for r in df["health_region"].unique() if r != "All"]
        region = st.selectbox("Health region", regions, index=0)

        sub = df[df["health_region"] == region].copy()
        fig = px.scatter(
            sub, x="radiance_mean", y="obesity_rate",
            color="ethnicity", symbol="ethnicity",
            labels={
                "radiance_mean": "Mean night-time brightness (nW/cm²·sr)",
                "obesity_rate": "Obesity rate (proportion of adults)",
            },
            title=f"Obesity vs night-lights • {region} (2020/21)",
        )
        fig.update_layout(height=520, margin=dict(l=10, r=10, t=60, b=10))
        st.plotly_chart(fig, width="stretch")
    else:
        note_missing(merged_csv, "Run your merge & plotting scripts to generate it.")

    st.markdown(
        """
        **Interpretation (quick guide)**  
        • → Right = brighter night-time environment.  
        • ↑ Up = higher obesity prevalence.  
        • Compare regions to spot patterns (e.g., **Te Manawa Taki** often shows higher rates).
        """
    )

# -------------------------------------------------
# Equity lens page
# -------------------------------------------------
elif page == "Equity lens: PM₂.₅ × Obesity":
    st.title("⚖️ Equity lens — Air pollution × Obesity (2020/21 × 2023)")

    csv_merged = DATA_PROC / "air_obesity_by_health_region_2023.csv"
    if not csv_merged.exists():
        note_missing(csv_merged, "Run scripts/71_merge_pm25_obesity_by_health_region.py first.")
    else:
        df = load_csv(csv_merged).copy()

        # Clean names and sanity check
        df.columns = [c.strip().replace(" ", "_").lower() for c in df.columns]
        need = {"health_region", "ethnicity", "obesity_rate"}
        miss = need - set(df.columns)
        if miss:
            st.error(f"Missing columns in {csv_merged.name}: {sorted(miss)}")
            st.stop()

        # Pollutant choices
        pol_map = pollutant_options_from(df)  # {"PM2.5": "...", "PM10": "..."}
        if not pol_map:
            st.error("No pollutant columns found (expected pm25_ugm3_2023 and/or pm10_ugm3_2023).")
            st.stop()

        # Controls
        c1, c2, c3, c4 = st.columns([1.1, 1, 1, 1])
        with c1:
            pol_label = st.radio("Pollutant", list(pol_map.keys()), horizontal=True, index=0)
            pol_col = pol_map[pol_label]
        with c2:
            regions = sorted([r for r in df["health_region"].unique() if r != "All"])
            picked_region = st.selectbox("Focus region", regions, index=0 if regions else None)
        with c3:
            show_ci = st.checkbox("Show obesity 95% CI", value=True)
        with c4:
            size_mode = st.selectbox("NZDep display", ["As marker size", "Hide"], index=0)

        # Keep complete rows for the chosen pollutant
        df = df.dropna(subset=[pol_col, "obesity_rate"]).copy()

        # Optional size mapping from NZDep
        size_arg = None
        if "nzdep_9_10_share" in df.columns and size_mode == "As marker size":
            df["_size"] = (df["nzdep_9_10_share"].clip(0, 1) * 24) + 6
            size_arg = "_size"

        size_bump = st.slider("Point size (focused chart)", 8, 28, 16)

        # --- Small multiples across regions
        st.subheader("All regions at a glance")
        fig_wrap = px.scatter(
            df,
            x=pol_col, y="obesity_rate",
            color="ethnicity", symbol="ethnicity",
            size=size_arg, size_max=30,
            facet_col="health_region", facet_col_wrap=2,
            labels={
                pol_col: f"{pol_label} annual mean (µg/m³, 2023)",
                "obesity_rate": "Obesity rate (proportion of adults, 2020/21)"
            },
            hover_data=[c for c in ["health_region","ethnicity","nzdep_9_10_share",
                                    "obesity_rate_low","obesity_rate_high"] if c in df.columns],
        )

        if show_ci and {"obesity_rate_low", "obesity_rate_high"}.issubset(df.columns):
            df["_err_y"] = (df["obesity_rate_high"] - df["obesity_rate_low"]) / 2.0
            for tr in fig_wrap.data:
                # name like 'ethnicity=Asian, health_region=Te Ikaroa'
                name = tr.name or ""
                eth = None
                reg = None
                for p in [p.strip() for p in name.split(",")]:
                    if p.startswith("ethnicity="): eth = p.split("=", 1)[1]
                    if p.startswith("health_region="): reg = p.split("=", 1)[1]
                mask = pd.Series(True, index=df.index)
                if eth is not None: mask &= (df["ethnicity"] == eth)
                if reg is not None: mask &= (df["health_region"] == reg)
                arr = df.loc[mask, "_err_y"].values
                if len(arr): tr.error_y = dict(type="data", array=arr, visible=True)

        fig_wrap.update_traces(marker_line=dict(width=0.6, color="black"))
        fig_wrap.update_layout(margin=dict(l=10, r=10, t=60, b=10),
                               legend=dict(orientation="h", y=-0.1),
                               height=780)
        st.plotly_chart(fig_wrap, width="stretch", config={"displayModeBar": True})

        # --- Focused region
        st.subheader(f"{picked_region}: {pol_label} vs Obesity by ethnicity")
        sub = df[df["health_region"] == picked_region].copy()
        fig_one = px.scatter(
            sub,
            x=pol_col, y="obesity_rate",
            color="ethnicity", symbol="ethnicity",
            size=size_arg, size_max=34, text="ethnicity",
            labels={
                pol_col: f"{pol_label} annual mean (µg/m³, 2023)",
                "obesity_rate": "Obesity rate (proportion of adults, 2020/21)"
            },
        )
        fig_one.update_traces(marker_line=dict(width=0.8, color="black"),
                              textposition="top center")

        if show_ci and {"obesity_rate_low", "obesity_rate_high"}.issubset(sub.columns):
            sub["_err_y"] = (sub["obesity_rate_high"] - sub["obesity_rate_low"]) / 2.0
            for tr in fig_one.data:
                eth = tr.name.replace("ethnicity=", "")
                err = sub.loc[sub["ethnicity"] == eth, "_err_y"].values
                if len(err): tr.error_y = dict(type="data", array=err, visible=True)

        fig_one.update_layout(margin=dict(l=10, r=10, t=40, b=10), height=520)
        st.plotly_chart(fig_one, width="stretch")

        # Table + download
        st.caption("Data table (filtered to available rows).")
        cols_show = ["health_region", "ethnicity", pol_col, "obesity_rate",
                     "nzdep_9_10_share", "obesity_rate_low", "obesity_rate_high"]
        cols_show = [c for c in cols_show if c in df.columns]
        st.dataframe(df[cols_show].sort_values(["health_region", "ethnicity"]),
                     use_container_width=True, hide_index=True)
        st.download_button(
            "Download CSV",
            data=df[cols_show].to_csv(index=False).encode("utf-8"),
            file_name=f"equity_lens_{pol_label.replace('.','')}_2023.csv",
            mime="text/csv",
        )

        # Reading guide
        bullets = [
            "→ Right = higher **air pollution** (annual mean).",
            "↑ Up = higher **adult obesity** prevalence.",
            "Colour = **ethnicity** within each health region.",
        ]
        if size_arg:
            bullets.append("Size = **NZDep** (share living in deciles 9–10).")
        st.markdown("**How to read this**  \n• " + "\n• ".join(bullets))

# -------------------------------------------------
# About page
# -------------------------------------------------
else:
    st.title("About this project")

    st.markdown(
        """
### About this project

Alan-NZ is an exploratory data project examining how **environmental context**
(night-time light and air quality) intersects with **health outcomes** across
Aotearoa New Zealand.

The goal is not prediction or causal inference, but to surface **structural
patterns**, raise better questions, and encourage careful interpretation of
publicly available data.

This work is intended as a starting point for discussion among analysts,
researchers, and policy practitioners.

### About the author

This project was developed by a health-sector data analyst in Aotearoa New Zealand,
with experience in public-sector analytics and population-level reporting.

The motivation behind Alan-NZ is to explore how routinely collected environmental
and health data can be combined to tell clearer, more context-aware stories.

**Built with:** Streamlit, Plotly, Pandas  
**Data:** NASA VIIRS, Stats NZ, LAWA, Ministry of Health (NZ)
        """
    )

    st.write("Repo:", f"{ROOT.name} (GitHub Pages at /docs)")