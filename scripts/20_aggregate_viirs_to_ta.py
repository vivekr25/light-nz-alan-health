from pathlib import Path
import geopandas as gpd
import rasterio
from rasterstats import zonal_stats
import pandas as pd

RAW = Path("data_raw")
OUT = Path("data_proc")
OUT.mkdir(exist_ok=True)

# === 1) Read TA boundaries (auto-pick the .shp) ===
ta_dir = RAW / "ta_2025_gen"   # <-- folder you created
shps = list(ta_dir.glob("*.shp"))
if not shps:
    raise FileNotFoundError("No .shp found in data_raw/ta_2025_gen. Did you unzip the shapefile?")
shp = shps[0]  # there should be only one .shp

ta = gpd.read_file(shp)

# Find likely code/name columns (Stats NZ usually uses TAyyyy_V1 / TAyyyy_NAM)
name_col = next((c for c in ta.columns if c.endswith("_NAM")), None)
code_col = next((c for c in ta.columns if c.endswith("_V1")), None)
if name_col is None or code_col is None:
    raise ValueError(f"Could not find *_NAM / *_V1 columns. Columns are: {list(ta.columns)}")

# === 2) Open the VIIRS raster ===
year = 2021
viirs_tif = RAW / f"viirs_annual_{year}.tif"
if not viirs_tif.exists():
    raise FileNotFoundError(
        f"Missing {viirs_tif}. Put a VIIRS annual GeoTIFF in data_raw/ as 'viirs_annual_{year}.tif'."
    )

with rasterio.open(viirs_tif) as src:
    # Align coordinate systems: polygons -> same CRS as raster
    ta_match = ta.to_crs(src.crs)

    # === 3) Zonal statistics ===
    zs = zonal_stats(
        ta_match,
        viirs_tif.as_posix(),
        stats=["mean", "median", "max", "count"],
        nodata=0,
        geojson_out=False
    )

# === 4) Save a clean CSV ===
res = ta_match[[code_col, name_col]].copy()
res.columns = ["TA_CODE", "TA_NAME"]  # normalize column names
res["viirs_year"]       = year
res["radiance_mean"]    = [d["mean"]   for d in zs]
res["radiance_median"]  = [d["median"] for d in zs]
res["radiance_max"]     = [d["max"]    for d in zs]
res["radiance_countpx"] = [d["count"]  for d in zs]

out_csv = OUT / f"viirs_ta_annual_{year}.csv"
res.to_csv(out_csv, index=False)
print(f"✅ Saved {out_csv} with {len(res)} rows. Columns: {list(res.columns)}")