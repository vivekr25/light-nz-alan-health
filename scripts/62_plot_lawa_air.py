#cat > scripts/62_plot_lawa_air.py <<'PY'
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

REG = "data_proc/air_annual_by_region.csv"
df = pd.read_csv(REG)

# pivot: one line per region for each indicator
for ind in ["PM2.5","PM10"]:
    sub = df[df["indicator"]==ind].copy()
    if sub.empty: 
        continue
    piv = sub.pivot(index="year", columns="region", values="mean_ugm3").sort_index()
    piv.plot(figsize=(10,6), marker="o")
    plt.title(f"{ind} annual mean by region")
    plt.xlabel("Year"); plt.ylabel("µg/m³")
    plt.tight_layout()
    Path("data_proc").mkdir(exist_ok=True, parents=True)
    out = f"data_proc/air_{ind.replace('.','')}_annual_by_region.png"
    plt.savefig(out, dpi=150)
    print("🖼️ Saved", out)

