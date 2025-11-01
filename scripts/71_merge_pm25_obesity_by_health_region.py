import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_RAW  = ROOT / "data_raw"
DATA_PROC = ROOT / "data_proc"

LAWA_XLS   = DATA_RAW / "lawa_air-quality-download-data_2016-2024.xlsx"
RC2HR_CSV  = DATA_RAW / "regional_council_to_health_region.csv"
OBE_CSV    = DATA_PROC / "obesity_by_region_ethnicity.csv"
OUT_CSV    = DATA_PROC / "air_obesity_by_health_region_2023.csv"

# --- Load LAWA and build annual means ---
xls = pd.ExcelFile(LAWA_XLS, engine="openpyxl")
sheet = next((s for s in xls.sheet_names if re.search(r"(data|monitor|dataset|pm|meas|observ)", s, re.I)), xls.sheet_names[0])
df = xls.parse(sheet)
df.columns = [c.strip() for c in df.columns]

col_region = [c for c in df.columns if c.lower() in ("region","regional council","council")][0]
col_ind    = [c for c in df.columns if "indicator" in c.lower()][0]
col_date   = [c for c in df.columns if "sample date" in c.lower()][0]
col_value  = [c for c in df.columns if "concentration" in c.lower()][0]

df[col_date] = pd.to_datetime(df[col_date], errors="coerce")
df["year"]   = df[col_date].dt.year

annual = (df.groupby([col_region,"year",col_ind], as_index=False)[col_value]
            .mean()
            .rename(columns={col_region:"region", col_ind:"indicator", col_value:"value_ugm3"}))

pm = (annual[(annual["indicator"].str.contains("PM2.5", case=False, regex=False)) & (annual["year"]==2023)]
        .copy()[["region","value_ugm3"]])

# --- Map Regional Council -> Health Region and aggregate ---
lut = pd.read_csv(RC2HR_CSV)
pm = pm.merge(lut, on="region", how="left")
pm_hr = pm.groupby("health_region", as_index=False)["value_ugm3"].mean().rename(columns={"value_ugm3":"pm25_ugm3_2023"})

# --- Load obesity (ethnicity-level) and join ---
obe = pd.read_csv(OBE_CSV)  # columns: health_region, year_to, ethnicity, obesity_rate, ...
obe23 = obe.copy()  # 2020/21 snapshot; you can filter if you add more years later

merged = (obe23.merge(pm_hr, on="health_region", how="left")
                .dropna(subset=["pm25_ugm3_2023"]))

OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
merged.to_csv(OUT_CSV, index=False)
print(f"✅ Wrote {OUT_CSV}  (rows: {len(merged)})")
print(merged.head())