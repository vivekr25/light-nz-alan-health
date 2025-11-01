# scripts/52_merge_obesity_brightness.py
import pandas as pd
from pathlib import Path

OBES = "data_proc/obesity_by_region_ethnicity.csv"
BRGT = "data_proc/brightness_by_health_region.csv"   # if you generated it earlier
OUT  = "data_proc/obesity_vs_brightness_by_region.csv"

Path("data_proc").mkdir(parents=True, exist_ok=True)

def norm_region(s: str) -> str:
    s = str(s).strip()
    if "Tai Tokerau" in s or "Northern" in s:
        return "Te Tai Tokerau"
    if "Manawa Taki" in s or "Midland" in s:
        return "Te Manawa Taki"
    if "Ikaroa" in s or "Central" in s:
        return "Te Ikaroa"
    if "Waipounamu" in s or "Southern" in s:
        return "Te Waipounamu"
    return s

ob = pd.read_csv(OBES)
if "health_region" not in ob.columns:
    raise SystemExit("obesity file missing health_region — re-run 51_clean_obesity_by_region.py")

ob["health_region"] = ob["health_region"].apply(norm_region)

br = pd.read_csv(BRGT)
if "health_region" not in br.columns:
    raise SystemExit("brightness file missing health_region. Create it as data_proc/brightness_by_health_region.csv")

br["health_region"] = br["health_region"].apply(norm_region)

# show coverage
print("Obesity regions:", sorted(ob["health_region"].unique()))
print("Brightness regions:", sorted(br["health_region"].unique()))

m = ob.merge(br, on="health_region", how="left")

# sanity: which regions lost brightness?
missing = m[m["radiance_mean"].isna()]["health_region"].unique().tolist()
if missing:
    print("⚠️ Missing brightness for regions:", missing,
          "\nIf you see 'Te Tai Tokerau' here, regenerate the brightness file so it includes that region.")

m.to_csv(OUT, index=False)
print(f"✅ Saved merged dataset → {OUT}  (rows: {len(m)})")