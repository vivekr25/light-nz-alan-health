# scripts/20b_aggregate_one_year.py
# Aggregate a single annual VIIRS raster to TA means and save CSV with names.
# Usage:
#   conda activate alan-nz
#   python scripts/20b_aggregate_one_year.py --year 2021

import argparse
from pathlib import Path
import json
import numpy as np
import pandas as pd
import rasterio
from rasterio.mask import mask

# --- paths (edit if needed) ---
TA_GEOJSON = Path("data_raw/ta2025_ms_5pct.geojson")
VIIRS_TIF_PATTERN = "data_raw/viirs_annual_{year}.tif"
OUT_DIR = Path("data_raw/viirs_yearly")
OUT_DIR.mkdir(parents=True, exist_ok=True)

def aggregate_year(year: int) -> Path:
    tif_path = Path(VIIRS_TIF_PATTERN.format(year=year))
    if not tif_path.exists():
        raise FileNotFoundError(f"Missing raster: {tif_path}")

    with open(TA_GEOJSON) as f:
        gj = json.load(f)

    # build code->name once
    code_to_name = {
        str(f["properties"]["TA2025_V1_"]).zfill(3): f["properties"].get("TA2025_V_2", "")
        for f in gj["features"]
    }

    recs = []
    with rasterio.open(tif_path) as src:
        nodata = src.nodata
        for feat in gj["features"]:
            code = str(feat["properties"]["TA2025_V1_"]).zfill(3)
            geom = feat["geometry"]
            try:
                data, _ = mask(src, [geom], crop=True, filled=True)
            except ValueError:
                recs.append({"ta_code_str": code, "radiance_mean": np.nan})
                continue

            arr = data[0].astype("float32")
            if nodata is not None:
                arr[arr == nodata] = np.nan
            arr[arr < 0] = np.nan

            mean_val = float(np.nanmean(arr)) if np.isfinite(arr).any() else np.nan
            recs.append({"ta_code_str": code, "radiance_mean": mean_val})

    df = pd.DataFrame(recs)
    df["viirs_year"] = year
    df["ta_name"] = df["ta_code_str"].map(code_to_name)
    out_csv = OUT_DIR / f"viirs_ta_annual_{year}_with_names.csv"
    df[["ta_code_str", "ta_name", "radiance_mean", "viirs_year"]].to_csv(out_csv, index=False)
    print(f"✅ Wrote {out_csv}  ({len(df)} rows)")
    return out_csv

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--year", type=int, required=True)
    args = ap.parse_args()
    aggregate_year(args.year)