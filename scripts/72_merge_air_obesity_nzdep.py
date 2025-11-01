# scripts/72_merge_air_obesity_nzdep.py
from pathlib import Path
import pandas as pd

AIR_OBE = Path("data_proc/air_obesity_by_health_region_2023.csv")
NZDEP   = Path("data_raw/nzdep_by_health_region.csv")
OUT     = Path("data_proc/air_obesity_deprivation_2023.csv")

if not AIR_OBE.exists():
    raise FileNotFoundError(f"Missing {AIR_OBE}")
if not NZDEP.exists():
    raise FileNotFoundError(f"Missing {NZDEP} (run the template step & fill values)")

ao  = pd.read_csv(AIR_OBE)
dep = pd.read_csv(NZDEP)

# basic sanity
need_cols = {"health_region","nzdep_9_10_share"}
miss = need_cols - set(dep.columns)
if miss:
    raise ValueError(f"{NZDEP} missing columns: {miss}")

# keep only needed dep columns
dep = dep[["health_region","nzdep_9_10_share"]].copy()

m = (ao.merge(dep, on="health_region", how="left")
       .sort_values(["health_region","ethnicity"]))

# quick checks
if m["nzdep_9_10_share"].isna().any():
    missing_regions = m.loc[m["nzdep_9_10_share"].isna(),"health_region"].unique()
    print("⚠️ NZDep missing for:", missing_regions)

OUT.parent.mkdir(parents=True, exist_ok=True)
m.to_csv(OUT, index=False)
print(f"✅ Wrote {OUT}  (rows: {len(m)})")
print(m.head(8))