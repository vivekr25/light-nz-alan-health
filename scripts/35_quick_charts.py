import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data_proc/viirs_ta_annual_2021.csv").rename(
    columns={"TA_CODE":"ta_code","radiance_mean":"radiance_mean"}
)

top = df.sort_values("radiance_mean", ascending=False).head(15)

plt.figure()
plt.bar(top["ta_code"].astype(str), top["radiance_mean"])
plt.xticks(rotation=60)
plt.ylabel("Mean night radiance (VIIRS 2021)")
plt.title("Top 15 TA codes by brightness")
plt.tight_layout()
plt.savefig("data_proc/top15_viirs_2021.png", dpi=160)

plt.figure()
plt.hist(df["radiance_mean"].dropna(), bins=30)
plt.xlabel("Mean night radiance (VIIRS 2021)")
plt.ylabel("Count of TA")
plt.title("Distribution of TA mean brightness")
plt.tight_layout()
plt.savefig("data_proc/hist_viirs_2021.png", dpi=160)

print("✅ Saved charts in data_proc/")