# scripts/36_normalize_and_rank.py
import json
import pandas as pd
from pathlib import Path

VIIRS_CSV = "data_proc/viirs_ta_annual_2021_with_names.csv"
GEOJSON   = "data_raw/ta2025_ms_5pct.geojson"     # has AREA_SQ_KM in properties
POP_CSV   = "data_raw/pop_2023.csv"
OUT_CSV   = "data_proc/viirs_ta_2021_normalized.csv"

# --- VIIRS table ---
df = pd.read_csv(VIIRS_CSV)
df["ta_code"] = pd.to_numeric(df["ta_code"], errors="coerce").astype("Int64")
df["ta_code_str"] = df["ta_code"].astype(str).str.zfill(3)

# --- Areas from GeoJSON ---
with open(GEOJSON) as f:
    gj = json.load(f)

areas = []
for feat in gj["features"]:
    p = feat["properties"]
    areas.append({
        "ta_code_str": str(p["TA2025_V1_"]).zfill(3),
        "area_sq_km":  p.get("AREA_SQ_KM")
    })
area_df = pd.DataFrame(areas)

# --- Population (accept either population_2023 or pop_2023) ---
pop = pd.read_csv(POP_CSV)
if "pop_2023" not in pop.columns and "population_2023" in pop.columns:
    pop = pop.rename(columns={"population_2023": "pop_2023"})

pop["ta_code"] = pd.to_numeric(pop["ta_code"], errors="coerce").astype("Int64")
pop["ta_code_str"] = pop["ta_code"].astype(str).str.zfill(3)
pop = pop[["ta_code_str", "pop_2023"]]

# --- Merge everything ---
out = (df.merge(area_df, on="ta_code_str", how="left")
         .merge(pop,      on="ta_code_str", how="left"))

# --- Normalized metrics ---
out["radiance_per_km2"] = out["radiance_mean"] / out["area_sq_km"]

# per-capita (may be NaN if pop is missing)
out["pop_2023"] = pd.to_numeric(out["pop_2023"], errors="coerce")
out["radiance_per_capita"] = out["radiance_mean"] / out["pop_2023"]

# --- Ranks (lower rank = brighter) ---
out["rank_radiance"]         = out["radiance_mean"].rank(ascending=False, method="min")
out["rank_per_km2"]          = out["radiance_per_km2"].rank(ascending=False, method="min")
out["rank_per_capita"]       = out["radiance_per_capita"].rank(ascending=False, method="min")

# Save
Path("data_proc").mkdir(parents=True, exist_ok=True)
out.to_csv(OUT_CSV, index=False)
print(f"✅ wrote {OUT_CSV} with {len(out)} rows")
print(out.head(5)[[
    "ta_code","ta_name","radiance_mean","area_sq_km","pop_2023",
    "radiance_per_km2","radiance_per_capita"
]])