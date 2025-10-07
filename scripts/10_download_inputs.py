import io, zipfile, requests
from pathlib import Path

DATA = Path("data_raw")
DATA.mkdir(exist_ok=True)

TA_URL = (
    "https://datafinder.stats.govt.nz/layer/106668-territorial-authority-2022-generalised/"
    "download/?format=esri-shapefile&clean=true"
)

zip_path = DATA / "ta_2022_gen.zip"
out_dir = DATA / "ta_2022_gen"

if out_dir.exists():
    print("✔️ TA shapefile already present")
else:
    print("↓ Downloading TA shapefile…")
    # add a browser-like header; some hosts require it
    r = requests.get(TA_URL, timeout=90, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True)
    r.raise_for_status()

    # Quick sanity check: must look like a zip
    ctype = r.headers.get("Content-Type", "")
    if "zip" not in ctype.lower():
        # Save what we got for debugging and exit gracefully
        bad = DATA / "ta_download_response.html"
        bad.write_bytes(r.content)
        raise SystemExit(
            f"Got non-zip content ({ctype}). "
            f"I saved it to {bad}.\n"
            "Use the manual download steps below and place the unzipped files in data_raw/ta_2022_gen/"
        )

    zip_path.write_bytes(r.content)
    with zipfile.ZipFile(io.BytesIO(r.content)) as z:
        z.extractall(out_dir)
    print(f"✅ Extracted to {out_dir}")