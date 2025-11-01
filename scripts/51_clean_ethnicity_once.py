import os, sys, pandas as pd

IN  = "data_raw/adult_unadjusted_topic_body_size_includes_obesity.csv"
OUT = "data_proc/obesity_by_region_ethnicity.csv"

print("Python:", sys.executable)
assert os.path.exists(IN), f"CSV not found: {IN}"
os.makedirs("data_proc", exist_ok=True)

def truthy(v):
    return str(v).strip().lower() in {"yes","y","true","1","t"}

df = pd.read_csv(IN, encoding="utf-8", low_memory=False)
print("Loaded rows:", len(df), "| cols:", len(df.columns))

# ---- base filter (unadjusted, all ages, both sexes, real regions) ----
mask_indicator = df["indicator"].str.contains(
    r"(overw[_ ]?obese|overweight.*obese|^obese$)", case=False, na=False
)
mask_unadj = df["age_standardised"].astype(str).str.lower().eq("no")
mask_age   = df["agegroup"].astype(str).str.lower().isin({"all ages","total"})
mask_sex   = df["gender"].astype(str).str.lower().isin({"all","both","male and female","total"})
mask_reg   = df["health_region"].astype(str).str.strip().ne("All")

base = df.loc[mask_indicator & mask_unadj & mask_age & mask_sex & mask_reg].copy()

# Choose rate columns (prefer proportion; else mean)
rate_col = "proportion" if "proportion" in base.columns else ("mean" if "mean" in base.columns else None)
lo_col   = "proportion_low" if "proportion_low" in base.columns else ("mean_low" if "mean_low" in base.columns else None)
hi_col   = "proportion_high" if "proportion_high" in base.columns else ("mean_high" if "mean_high" in base.columns else None)
if rate_col is None:
    raise RuntimeError("No rate column (proportion/mean) found.")

eth_cols = [("Māori","māori"), ("Pacific","pacific"), ("Asian","asian"), ("European/Other","other_euro")]
pieces = []

for label, flag_col in eth_cols:
    if flag_col not in base.columns:
        print(f"⚠️ Missing ethnicity flag column: {flag_col} — skipping")
        continue

    take = base.loc[base[flag_col].apply(lambda v: str(v).strip() != "" and truthy(v)),
                    ["health_region","year_to", rate_col] + ([lo_col] if lo_col else []) + ([hi_col] if hi_col else [])].copy()
    # If that yields nothing (some files have non-yes values), fall back to "not null"
    if take.empty:
        take = base.loc[base[flag_col].notna(),
                        ["health_region","year_to", rate_col] + ([lo_col] if lo_col else []) + ([hi_col] if hi_col else [])].copy()
    if take.empty:
        print(f"ℹ️ No rows found for {label} after filters — skipping.")
        continue

    # For each region, keep the latest available year (years may differ by ethnicity)
    take["year_to_str"] = take["year_to"].astype(str)
    take["year_to_num"] = take["year_to_str"].str.extract(r"(\d{2})(?:\D*)$")[0].astype(float).fillna(-1)
    idx = take.groupby("health_region")["year_to_num"].idxmax()
    take = take.loc[idx].drop(columns=["year_to_num","year_to_str"]).copy()
    take["ethnicity"] = label

    rename = {rate_col: "obesity_rate"}
    if lo_col: rename[lo_col] = "obesity_rate_low"
    if hi_col: rename[hi_col] = "obesity_rate_high"
    take.rename(columns=rename, inplace=True)

    pieces.append(take)

out = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame(
    columns=["health_region","year_to","ethnicity","obesity_rate"]
)

# Normalise region names to short form (right side after " | ")
def short_region(s):
    s = str(s)
    parts = [p.strip() for p in s.split("|")]
    return parts[-1] if len(parts) >= 2 else s.strip()

out["health_region"] = out["health_region"].map(short_region)

# Order + save
cols = ["health_region","year_to","ethnicity","obesity_rate"]
for c in ["obesity_rate_low","obesity_rate_high"]:
    if c in out.columns: cols.append(c)
out = out[cols].sort_values(["health_region","ethnicity"])
out.to_csv(OUT, index=False)

print(f"\n✅ Saved ethnicity-level obesity data → {OUT}  (rows: {len(out)})")
print("Regions found:", sorted(out["health_region"].unique()))
if not out.empty:
    print("\nCounts by region × ethnicity:")
    print(out.groupby(["health_region","ethnicity"]).size().unstack(fill_value=0))
else:
    print("\n…no rows matched (consider relaxing filters further).")
