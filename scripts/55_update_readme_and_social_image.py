import re
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# ---------- paths ----------
IMG_SRC = Path("data_proc/obesity_vs_brightness_small_multiples.png")
IMG_SOCIAL = Path("data_proc/obesity_vs_brightness_social.png")
README = Path("README.md")

# ---------- helper: Pillow 9/10 text measurement ----------
def measure_text(draw, text, font):
    """Return (width, height) of text for the given font."""
    try:
        # Pillow ≥10
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        return right - left, bottom - top
    except AttributeError:
        # Pillow <10
        try:
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        except Exception:
            return draw.textsize(text, font=font)

# ---------- create social-friendly image ----------
img = Image.open(IMG_SRC)
W, H = img.size

pad_top, pad_bottom = 130, 80
new_img = Image.new("RGB", (W, H + pad_top + pad_bottom), "white")
new_img.paste(img, (0, pad_top))

draw = ImageDraw.Draw(new_img)
# fallback font path (macOS default)
font_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
font_title = ImageFont.truetype(font_path, 36)
font_footer = ImageFont.truetype(font_path, 22)

title = "Obesity vs Night-time Brightness — Health NZ Regions (2020/21)"
footer = "Data: NASA VIIRS 2021, MoH 2020/21 | vivekr25.github.io/light-nz-alan-health"

# Title centered
tw, th = measure_text(draw, title, font_title)
draw.text(((W - tw) / 2, 40), title, fill="black", font=font_title)

# Footer centered
fw, fh = measure_text(draw, footer, font_footer)
draw.text(((W - fw) / 2, H + pad_top + 20), footer, fill="gray", font=font_footer)

new_img.save(IMG_SOCIAL, dpi=(200, 200))
print(f"✅ Created social image: {IMG_SOCIAL}")

# ---------- README update ----------
section = f"""
---

## 🩺 Obesity vs Night-time Brightness (Health NZ Regions)

This visual pairs *NASA’s VIIRS 2021 night-lights* with *Ministry of Health 2020/21 adult obesity data* across Health NZ regions and ethnic groups.

- **Te Manawa Taki** stands out — the brightest and most uniformly high in obesity across all ethnicities.  
- **Te Tai Tokerau** and **Te Waipounamu** remain dimmer, yet ethnic disparities persist.  
- Urban brightness doesn’t erase inequities — it often illuminates them.

![Obesity vs Night-time Brightness Small Multiples](data_proc/obesity_vs_brightness_small_multiples.png)

[🔗 Explore the interactive map](https://vivekr25.github.io/light-nz-alan-health/)
"""

readme_txt = README.read_text()
if "Obesity vs Night-time Brightness (Health NZ Regions)" in readme_txt:
    print("ℹ️ README section already present; skipping insert.")
else:
    README.write_text(readme_txt.strip() + section)
    print("✅ Updated README with small-multiples analysis.")