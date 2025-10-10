# 🌃 NZ Night-time Brightness by Territorial Authority (VIIRS 2021)

This project maps and ranks average night-time **radiance** across New Zealand’s Territorial Authorities (TAs) using NASA’s **VIIRS Night Lights** (2021). It includes both an **interactive choropleth** and static charts.

**Live map:** 👉 **[Open Interactive Map](https://vivekr25.github.io/light-nz-alan-health/)**

![Map preview](data_proc/ta_brightness_map_1600.png)

---

## Key findings (first pass)

- **Overall mean radiance (absolute):**  
  **Hamilton City** ranks highest, followed by **Tauranga** and **Napier**.  
  This reflects **total light output over each TA** (urban extent + intensity).

- **Radiance per km² (density):**  
  **Kawerau District** tops the list, then **Hamilton City** and **Napier City**.  
  Density highlights **concentrated lighting** (e.g., industrial sites or compact urban cores), not just large urban area.

- **Why Hamilton > Auckland on the absolute chart?**  
  Our metric is **TA-average radiance**, not total lumens. Hamilton’s urban area is compact and consistently bright, which pushes up its mean. Auckland’s very large TA includes darker rural/coastal areas that **dilute** the mean.

  📊 Radiance Trends and Urban Patterns (2021 Snapshot)

🗺️ National Trend — VIIRS Annual
Currently only 2021 data is available, so this chart shows a single point.
	•	Future additions (2014–2023) will reveal whether NZ’s average night-time brightness — a proxy for urban and economic activity — is rising, flattening, or declining.
	•	A higher mean than median indicates that a few bright cities (e.g., Hamilton, Tauranga, Auckland) are pulling the national average upward.
	•	Expected pattern once full data is loaded: a gradual upward drift reflecting expanding infrastructure, housing, and electrification.

  🌆 Top 12 Territorial Authorities by Mean Radiance (2021)
  The brightest areas include Hamilton City, Tauranga City, Napier City, Wellington, Christchurch, and Kawerau District.
	•	These represent densely lit urban cores or industrial hubs with concentrated artificial light.
	•	Hamilton City currently stands out as NZ’s brightest region by mean radiance.
	•	Once earlier years are added, these small multiples will reveal which cities are growing faster in light intensity and which have stabilized.

  🏙️ City vs District Radiance Distribution (2021)
  Cities have a much higher median and a broader range of brightness than districts.
	•	The upper quartile for cities is roughly 10× brighter than the typical district.
	•	Districts appear dimmer overall because light is averaged over larger, more rural land areas.
	•	Example:
	•	Auckland’s mean brightness looks lower than Hamilton’s — not because it’s darker, but because its lighting is spread across a vast area.
	•	Compact cities like Hamilton or Tauranga have intense light concentration, driving higher mean values.

  🧭 Summary Insight

New Zealand’s night-time light landscape is dominated by compact urban centers rather than sprawling metros.
As more years are added, this dataset will help quantify how urban brightness evolves over time — a valuable proxy for both economic activity and energy use efficiency.

⸻

✅ Charts generated using VIIRS Night-time Lights (NASA, 2021) and Stats NZ TA 2025 boundaries.
💡 Next: Extend dataset to 2014–2023 and visualize longitudinal growth patterns.

### Top 15: absolute mean radiance
![Top 15 by mean radiance](data_proc/top15_abs_radiance.png)

### Top 15: radiance per km² (density)
![Top 15 by radiance per km²](data_proc/top15_radiance_per_km2.png)

---

## What’s in the repo

- `data_proc/viirs_ta_annual_2021_with_names.csv` – TA-level radiance with names  
- `data_proc/ta_single_map_toggle.html` – interactive choropleth  
- `data_proc/ta_brightness_map_1600.png` – static map image  
- `data_proc/top15_abs_radiance.png` – bar chart (absolute mean)  
- `data_proc/top15_radiance_per_km2.png` – bar chart (density)

---

## Reproduce locally

```bash
conda activate alan-nz
python scripts/31_single_map_toggle.py        # builds map + PNG
python scripts/36_normalize_and_rank.py       # builds normalized CSV
python scripts/37_make_normalized_charts.py   # builds the two charts

## Data & credits
	•	VIIRS Night Lights (2021) – NASA/NOAA
	•	Administrative boundaries – Stats NZ, TA 2025
	•	Processing & visualization – Python, Pandas, Plotly.
