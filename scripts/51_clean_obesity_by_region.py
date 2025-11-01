# scripts/51_clean_obesity_by_region.py
# Purpose: Clean adult unadjusted obesity CSV to ethnicity x Health Region rows
# Run in VS Code terminal (conda env alan-nz):
#   /opt/anaconda3/bin/conda run -n alan-nz python scripts/51_clean_obesity_by_region.py

import os, re
import pandas as pd

SRC = "data_raw/adult_unadjusted_topic_body_size_includes_obesity.csv"
OUT = "data_proc/obesity_by_region_ethnicity.csv"

def norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    return s

def pick(col_map, *candidates):
    """Pick the first column whose normalized name matches any of candidates."""
    for want in candidates:
        want_n = norm(want)
        for raw, n in col_map.items():
            if n == want_n:
                return raw
    raise KeyError(f"Couldn't find any of: {candidates}")

assert os.path.exists(SRC), f"Missing input CSV: {SRC}"
df = pd.read_csv(SRC)

# Build normalized map {raw_col: normalized_col}
col_map = {c: norm(c) for c in df.columns}

# Try to find flexible column names
col_indicator  = pick(col_map, "indicator")
col_year       = pick(col_map, "year", "year_ending_june", "year_to")
# Health region column name varies across MoH extracts
col_region     = pick(col_map, "health_region", "region", "health service area", "health service area name")
# Prioritised ethnicity is key for comparing Māori/Pacific/Asian/European
# Try several possibilities
try:
    col_eth = pick(col_map, "ethnicity_prioritised", "ethnicity prioritised", "ethnicity")
except KeyError:
    # If the file only has subgroup columns, fall back to generic "subgroup"
    col_eth = pick(col_map, "subgroup")

# The measure column: often "estimate" (%) or "value" or "percentage"
# In many MoH “unadjusted” sheets, it's called "estimate"
measure_candidates = ("estimate", "percent", "percentage", "value", "rate")
for m in measure_candidates:
    try:
        col_val = pick(col_map, m)
        break
    except KeyError:
        continue
else:
    raise KeyError(f"Couldn't find any measure column among: {measure_candidates}")

# Overweight+Obese filter – be broad but safe
mask_indicator = df[col_indicator].str.contains(
    r"(overw[_ ]?obese|overweight.*obese)", case=False, na=False
)

# Ethnicity of interest (prioritised set)
ETH_KEEP = ["Māori", "Pacific", "Asian", "European/Other", "European / Other", "European and Other", "European and other"]

sub = df[mask_indicator].copy()

# Keep only the latest combined year if a “year range” format like "2020/21" exists
# If it's numeric years, this will still work—then we'll just keep the max.
# Convert year to string for safety
sub[col_year] = sub[col_year].astype(str)
latest_year = sub[col_year].max()

# Filter “All” sex/age/etc if those columns exist (best-effort)
for maybe_all in ["sex","age_group","imbp","imd","deprivation","disability","smoking_status","rurality","residence"]:
    if maybe_all in col_map.values():
        # find the raw column name for this normalized key
        raw = [k for k,v in col_map.items() if v == maybe_all][0]
        if raw in sub.columns:
            sub = sub[(sub[raw].astype(str).str.lower()=="all") | (~sub[raw].notna())]

# Keep the rows for ethnicities of interest (if the column exists)
if col_eth in sub.columns:
    # normalize values to a consistent set
    sub["ethnicity"] = (
        sub[col_eth]
        .replace({"European and Other":"European/Other","European / Other":"European/Other"})
        .astype(str)
    )
    sub = sub[sub["ethnicity"].isin(ETH_KEEP)]
else:
    sub["ethnicity"] = "All"

# Region cleanups (collapse long names to short like Te Manawa Taki)
sub["health_region"] = sub[col_region].astype(str)
# Tidy common variants
sub["health_region"] = (
    sub["health_region"]
      .str.replace(r"^Central.*Ikaroa.*$", "Te Ikaroa", regex=True)
      .str.replace(r"^Midland.*Manawa.*Taki.*$", "Te Manawa Taki", regex=True)
      .str.replace(r"^Northern.*Taitokerau.*$", "Taitokerau", regex=True)
      .str.replace(r"^Southern.*Waipounamu.*$", "Te Waipounamu", regex=True)
)

# Keep the latest year
sub = sub[sub[col_year] == latest_year].copy()
sub.rename(columns={col_val: "obesity_rate"}, inplace=True)

# Keep and coerce the measure
sub["obesity_rate"] = pd.to_numeric(sub["obesity_rate"], errors="coerce") / (100.0 if sub["obesity_rate"].max() > 1.5 else 1.0)

out = sub[["health_region", col_year, "ethnicity", "obesity_rate"]].rename(columns={col_year:"year_to"})
out = out.dropna(subset=["health_region","obesity_rate"])

# Print quick sanity
print(f"Latest year found: {latest_year}")
print("Regions:", sorted(out["health_region"].unique()))
print("Ethnicities:", sorted(out["ethnicity"].unique()))
print(out.groupby(["health_region","ethnicity"]).size().rename("rows"))

os.makedirs("data_proc", exist_ok=True)
out.to_csv(OUT, index=False)
print(f"✅ Saved ethnicity-level obesity data → {OUT}  (rows: {len(out)})")