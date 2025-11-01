# scripts/39_batch_years.py
# Discover available annual VIIRS GeoTIFFs and aggregate each year to TA CSVs.

import re
from pathlib import Path
import subprocess

RAW = Path("data_raw")
PATTERN = re.compile(r"viirs_annual_(\d{4})\.tif$", re.I)

tifs = sorted(p for p in RAW.glob("viirs_annual_*.tif") if PATTERN.search(p.name))
years = [int(PATTERN.search(p.name).group(1)) for p in tifs]

if not years:
    print("No annual TIFFs found in data_raw/ (expected files like viirs_annual_2021.tif).")
    print("Once you add them, re-run:  python scripts/39_batch_years.py")
    raise SystemExit(0)

print("→ Found annual rasters for years:", years)

for y in years:
    print(f"→ Aggregating {y} …")
    subprocess.check_call(
        ["python", "scripts/20b_aggregate_one_year.py", "--year", str(y)]
    )

print("✅ Done. Yearly TA CSVs are in data_raw/viirs_yearly/")