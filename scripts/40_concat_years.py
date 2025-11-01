from pathlib import Path
import pandas as pd

YEARLY_DIR = Path("data_raw/viirs_yearly")
OUT = Path("data_proc/viirs_ta_timeseries_2014_2023.csv")

def load_one(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    # --- normalize column names across possible variants ---
    cols = {c.lower(): c for c in df.columns}  # map lowercase->original

    # ta_code: accept 'ta_code', 'ta_code_str'
    if "ta_code" in cols:
        ta_code_col = cols["ta_code"]
        ta_code = pd.to_numeric(df[ta_code_col], errors="coerce").astype("Int64")
    elif "ta_code_str" in cols:
        # zero-padded '001' -> int
        ta_code_col = cols["ta_code_str"]
        ta_code = pd.to_numeric(df[ta_code_col], errors="coerce").astype("Int64")
    else:
        raise ValueError(f"{path} is missing a TA code column (ta_code or ta_code_str)")

    # ta_name
    if "ta_name" in cols:
        ta_name = df[cols["ta_name"]].astype(str)
    else:
        raise ValueError(f"{path} missing 'ta_name'")

    # viirs_year (could be 'year' or 'viirs_year')
    if "viirs_year" in cols:
        year = pd.to_numeric(df[cols["viirs_year"]], errors="coerce").astype(int)
    elif "year" in cols:
        year = pd.to_numeric(df[cols["year"]], errors="coerce").astype(int)
    else:
        # try to infer from filename
        import re
        m = re.search(r"(\d{4})", path.name)
        if not m:
            raise ValueError(f"{path} missing year column and couldn’t infer from filename")
        year = int(m.group(1))
        year = pd.Series([year] * len(df), dtype=int)

    # radiance_mean (accept 'radiance_mean' or 'mean_radiance' or 'radiance')
    rad_col = None
    for k in ("radiance_mean", "mean_radiance", "radiance"):
        if k in cols:
            rad_col = cols[k]
            break
    if rad_col is None:
        raise ValueError(f"{path} missing radiance column (radiance_mean/mean_radiance/radiance)")
    rad = pd.to_numeric(df[rad_col], errors="coerce")

    out = pd.DataFrame(
        {
            "viirs_year": year,
            "ta_code": ta_code,
            "ta_name": ta_name,
            "radiance_mean": rad,
        }
    )
    return out

files = sorted(YEARLY_DIR.glob("viirs_ta_annual_*_with_names.csv"))
if not files:
    raise SystemExit("No yearly CSVs found under data_raw/viirs_yearly/")

frames = [load_one(f) for f in files]
full = pd.concat(frames, ignore_index=True).sort_values(["ta_code", "viirs_year"])

OUT.parent.mkdir(parents=True, exist_ok=True)
full.to_csv(OUT, index=False)
print(f"✅ Wrote {OUT} with {len(full):,} rows from {len(files)} yearly files.")
print("   Columns:", list(full.columns))