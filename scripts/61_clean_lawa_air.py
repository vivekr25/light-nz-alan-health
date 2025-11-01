#cat > scripts/61_clean_lawa_air.py <<'PY'
import pandas as pd
from pathlib import Path

SRC = "data_raw/lawa_air-quality-download-data_2016-2024.xlsx"
OUT_DAILY = "data_proc/air_daily_clean.csv"
OUT_ANNUAL_SITE = "data_proc/air_annual_by_site.csv"
OUT_ANNUAL_REGION = "data_proc/air_annual_by_region.csv"
OUT_THRESH = "data_proc/air_thresholds_by_site.csv"

# WHO 2021 daily guidelines (µg/m³). Adjust if you prefer other limits.
WHO_PM25_DAILY = 15.0
WHO_PM10_DAILY = 45.0
# NZ NES (common reference in NZ): PM10 24-hr = 50 µg/m³
NES_PM10_DAILY = 50.0

print("Loading…", SRC)
xls = pd.ExcelFile(SRC, engine="openpyxl")
# The sheet name you saw:
sheet = "Monitoring dataset "
df = xls.parse(sheet)

# Standardize column names
df = df.rename(columns={
    "Region": "region",
    "Agency": "agency",
    "Town": "town",
    "Site Name": "site_name",
    "LAWA Site ID": "lawa_site_id",
    "Site ID": "site_id",
    "Latitude": "lat",
    "Longitude": "lon",
    "Site Type": "site_type",
    "Indicator": "indicator",
    "Sample Date": "sample_date",
    "Concentration (ug/m3)": "value_ugm3",
})

# Keep PM10 & PM2.5 only, drop NA
df = df[df["indicator"].isin(["PM10","PM2.5"])].copy()
df["sample_date"] = pd.to_datetime(df["sample_date"], errors="coerce")
df = df.dropna(subset=["sample_date","value_ugm3"])

# Ensure numeric
df["value_ugm3"] = pd.to_numeric(df["value_ugm3"], errors="coerce")
df = df.dropna(subset=["value_ugm3"])

# Minimal tidy daily table
keep_cols = ["region","agency","town","site_name","lawa_site_id","site_id",
             "lat","lon","site_type","indicator","sample_date","value_ugm3"]
daily = df[keep_cols].sort_values(["region","site_name","indicator","sample_date"])

Path("data_proc").mkdir(parents=True, exist_ok=True)
daily.to_csv(OUT_DAILY, index=False)
print(f"✅ Wrote {OUT_DAILY}  rows={len(daily):,}")

# --- Annual summaries ---
daily["year"] = daily["sample_date"].dt.year

# Per-site, per-year (mean, days captured, %missing relative to full year)
site_year = (daily
    .groupby(["region","site_name","lawa_site_id","indicator","year"], as_index=False)
    .agg(
        mean_ugm3=("value_ugm3","mean"),
        days_measured=("value_ugm3","count"),
        first_date=("sample_date","min"),
        last_date=("sample_date","max"),
    )
)
# Approx coverage vs 365
site_year["pct_coverage"] = (site_year["days_measured"] / 365 * 100).round(1)
site_year.to_csv(OUT_ANNUAL_SITE, index=False)
print(f"✅ Wrote {OUT_ANNUAL_SITE}  rows={len(site_year):,}")

# Region-year (mean of site means to avoid over-weighting sites with more samples)
region_year = (site_year
    .groupby(["region","indicator","year"], as_index=False)
    .agg(mean_ugm3=("mean_ugm3","mean"),
         n_sites=("site_name","nunique"))
    .sort_values(["region","indicator","year"])
)
region_year.to_csv(OUT_ANNUAL_REGION, index=False)
print(f"✅ Wrote {OUT_ANNUAL_REGION}  rows={len(region_year):,}")

# --- Threshold exceedances (daily) by site-year ---
def limits_for(ind):
    if ind == "PM2.5":
        return {"who_daily": WHO_PM25_DAILY}
    if ind == "PM10":
        return {"who_daily": WHO_PM10_DAILY, "nes_daily": NES_PM10_DAILY}
    return {}

rows = []
for (reg, site, lawasid, ind, yr), g in daily.groupby(["region","site_name","lawa_site_id","indicator","year"]):
    lims = limits_for(ind)
    out = {
        "region": reg, "site_name": site, "lawa_site_id": lawasid,
        "indicator": ind, "year": yr, "days_measured": len(g)
    }
    for label, thr in lims.items():
        out[f"exceed_{label}"] = int((g["value_ugm3"] > thr).sum())
    rows.append(out)

thresh = pd.DataFrame(rows).sort_values(["region","site_name","indicator","year"])
thresh.to_csv(OUT_THRESH, index=False)
print(f"✅ Wrote {OUT_THRESH}  rows={len(thresh):,}")