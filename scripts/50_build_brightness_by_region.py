import pandas as pd
from pathlib import Path

TA = "data_proc/viirs_ta_annual_2021_with_names.csv"
LUT = "data_raw/ta_to_health_region.csv"
OUT = Path("data_proc/brightness_by_health_region.csv")

ta = pd.read_csv(TA)
lut = pd.read_csv(LUT)

ta["ta_name"] = ta["ta_name"].str.strip()
lut["ta_name"] = lut["ta_name"].str.strip()

m = ta.merge(lut, on="ta_name", how="left")

missing = sorted(m.loc[m["health_region"].isna(), "ta_name"].dropna().unique())
if missing:
    print("⚠️ TAs missing from lookup (add to data_raw/ta_to_health_region.csv):")
    for x in missing:
        print(" -", x)

agg = (m.dropna(subset=["health_region"])
        .groupby("health_region", as_index=False)["radiance_mean"]
        .mean()
        .sort_values("radiance_mean", ascending=False))

OUT.parent.mkdir(parents=True, exist_ok=True)
agg.to_csv(OUT, index=False)
print("✅ Wrote", OUT.as_posix())
print(agg.to_string(index=False))