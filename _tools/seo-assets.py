#!/usr/bin/env python3
"""Generate OG image, favicon set, and apple-touch-icon from logo.png."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGO = os.path.join(ROOT, "logo.png")
FAV_DIR = os.path.join(ROOT, "assets", "favicons")
os.makedirs(FAV_DIR, exist_ok=True)

# ---------- 1. Square favicons ----------
logo = Image.open(LOGO).convert("RGBA")
for size, name in [(16, "favicon-16.png"), (32, "favicon-32.png"),
                   (192, "favicon-192.png"), (512, "favicon-512.png"),
                   (180, "apple-touch-icon.png")]:
    out = logo.resize((size, size), Image.LANCZOS)
    out.save(os.path.join(FAV_DIR, name), "PNG", optimize=True)
    print(f"wrote {name} ({size}x{size})")

# ---------- 2. SVG favicon (vector) ----------
# Use a minimal SVG that re-encodes the logo at its native aspect.
# This avoids a giant base64 blob while keeping it crisp at any size.
svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <rect width="256" height="256" rx="56" fill="#100F0F"/>
  <g transform="translate(128,128)">
    <path d="M0,-72 L62,-36 L62,36 L0,72 L-62,36 L-62,-36 Z"
          fill="none" stroke="#E5E5E5" stroke-width="10" stroke-linejoin="round"/>
    <path d="M0,-30 L26,-15 L26,15 L0,30 L-26,15 L-26,-15 Z"
          fill="#E5E5E5"/>
  </g>
</svg>'''
with open(os.path.join(FAV_DIR, "favicon.svg"), "w") as f:
    f.write(svg)
print("wrote favicon.svg")

# ---------- 3. 1200x630 OG image ----------
W, H = 1200, 630
og = Image.new("RGB", (W, H), (16, 15, 15))

# Subtle radial gradient for depth
overlay = Image.new("RGB", (W, H), (16, 15, 15))
mask = Image.new("L", (W, H), 0)
md = ImageDraw.Draw(mask)
for r in range(700, 0, -20):
    alpha = int(60 * (1 - r/700))
    md.ellipse([W/2 - r, H/2 - r, W/2 + r, H/2 + r], fill=alpha)
overlay = Image.composite(Image.new("RGB", (W, H), (38, 30, 30)), overlay, mask)
og = Image.blend(og, overlay, 0.5)

# Logo hex
hex_img = logo.copy()
target_h = 280
ratio = target_h / hex_img.height
hex_img = hex_img.resize((int(hex_img.width * ratio), target_h), Image.LANCZOS)
og.paste(hex_img, (90, (H - target_h) // 2), hex_img)

# Text block
draw = ImageDraw.Draw(og)

def load_font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Inter-Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Inter-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()

f_brand = load_font(40, bold=True)
f_title = load_font(58, bold=True)
f_sub = load_font(30, bold=False)
f_meta = load_font(22, bold=False)

text_x = 90 + hex_img.width + 50

# Eyebrow
draw.text((text_x, 160), "SHAYAN SPIEL", font=f_brand, fill=(229, 229, 229))
# Title (two lines, manual wrap)
draw.text((text_x, 210), "Session-as-Content", font=f_title, fill=(245, 245, 245))
draw.text((text_x, 280), "Infrastructure", font=f_title, fill=(245, 245, 245))
# Subtitle
draw.text((text_x, 380), "Building & testing agentic AI workflows in public.", font=f_sub, fill=(180, 180, 180))
# URL
draw.text((text_x, 510), "shayanspiel.github.io", font=f_meta, fill=(140, 140, 140))

# Bottom rule + tagline
draw.line([(90, 580), (W - 90, 580)], fill=(60, 60, 60), width=1)

og.save(os.path.join(ROOT, "assets", "og-default.png"), "PNG", optimize=True)
print("wrote assets/og-default.png (1200x630)")
