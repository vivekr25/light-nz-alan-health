# 🌌 NZ Night-time Brightness by Territorial Authority (VIIRS 2021)

This interactive choropleth visualizes average night-time radiance across New Zealand’s Territorial Authorities,  
derived from NASA’s VIIRS night-lights dataset.

Use the toggle buttons to switch between:
- **Relative (quantiles):** compares each TA’s brightness against others in 5 evenly distributed bands (Very Low → Very High)  
- **Absolute (radiance):** shows the actual mean radiance intensity in nW/cm²·sr

The map highlights areas with higher artificial light intensity — a proxy for **urban activity and energy use**.  
Both an interactive HTML version and a static export are available below.

---

### 🔗 Interactive version
👉 **[Open Interactive Map →](https://vivekr25.github.io/light-nz-alan-health/)**

### 🖼️ Static preview
![NZ Night-time Brightness Map](data_proc/ta_brightness_map_1600.png)

---

**Data sources:** NASA VIIRS Night Lights (2021) • Stats NZ TA 2025 Boundaries  
**Tools:** Python | Plotly | GeoJSON | Kaleido  