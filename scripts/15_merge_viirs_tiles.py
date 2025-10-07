from pathlib import Path
import rasterio
from rasterio.merge import merge

RAW = Path("data_raw")
# Pick all parts that start with the prefix but are NOT the final merged file
tiles = sorted([p for p in RAW.glob("viirs_annual_2021-*.tif") if p.name != "viirs_annual_2021.tif"])

if not tiles:
    raise SystemExit("No VIIRS tiles found matching 'viirs_annual_2021-*.tif' in data_raw/")

print("Merging tiles:", [t.name for t in tiles])

# Open all sources
srcs = [rasterio.open(t) for t in tiles]

# Merge into a single mosaic (keeps georeferencing)
mosaic, transform = merge(srcs)
meta = srcs[0].meta.copy()
for s in srcs:
    s.close()

# Update metadata to new size and transform
meta.update({
    "height": mosaic.shape[1],
    "width": mosaic.shape[2],
    "transform": transform
})

out_path = RAW / "viirs_annual_2021.tif"
with rasterio.open(out_path, "w", **meta) as dst:
    dst.write(mosaic)

print(f"✅ Wrote {out_path} ({round(out_path.stat().st_size/1e6, 1)} MB)")