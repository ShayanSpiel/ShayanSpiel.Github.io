#!/usr/bin/env python3
"""Generate OG image (1200x630) and favicon set from personal brand logo.

OG composition: large personal lockup (icon + "Shayan Spiel" wordmark) as the
hero, single methodology line beneath, footer with URL. Personal brand
positioning -- Shayan Spiel (operator), Session-as-Content (methodology),
Technical Founders (audience). The lockup is 5x more prominent than the
previous icon-only layout.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSONAL_DIR = os.path.join(ROOT, "assets", "logos", "personal")
PERSONAL_PRIMARY_PNG = os.path.join(PERSONAL_DIR, "primary-transparent.png")
PERSONAL_ICON_PNG = os.path.join(PERSONAL_DIR, "icon-transparent.png")
FAV_DIR = os.path.join(ROOT, "assets", "favicons")
os.makedirs(FAV_DIR, exist_ok=True)


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


# ---------- 1. Square favicons from personal icon ----------
icon = Image.open(PERSONAL_ICON_PNG).convert("RGBA")
for size, name in [(16, "favicon-16.png"), (32, "favicon-32.png"),
                   (192, "favicon-192.png"), (512, "favicon-512.png"),
                   (180, "apple-touch-icon.png")]:
    out = icon.resize((size, size), Image.LANCZOS)
    out.save(os.path.join(FAV_DIR, name), "PNG", optimize=True)
    print(f"wrote {name} ({size}x{size})")

# ---------- 2. SVG favicon (vector) ----------
# Skull mark from /branding — must match the rasterized PNGs above so a re-run
# of this script can't silently replace the favicon with a different mark.
svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <rect width="256" height="256" rx="48" fill="#000000"/>
  <g transform="translate(0, 0) scale(8)">
    <path d="M16 7l-12 12 6 6 3-3 3 3 3-3 3 3 6-6-12-12zM16 19l-3-3 3-3 3 3-3 3z" fill="#ffffff"/>
  </g>
</svg>'''
with open(os.path.join(FAV_DIR, "favicon.svg"), "w") as f:
    f.write(svg)
print("wrote favicon.svg")

# ---------- 3. 1200x630 OG image ----------
W, H = 1200, 630
og = Image.new("RGB", (W, H), (16, 15, 15))

# Subtle radial gradient for depth (top-left light source)
overlay = Image.new("RGB", (W, H), (16, 15, 15))
mask = Image.new("L", (W, H), 0)
md = ImageDraw.Draw(mask)
for r in range(700, 0, -20):
    alpha = int(55 * (1 - r / 700))
    md.ellipse([W * 0.25 - r, H * 0.35 - r, W * 0.25 + r, H * 0.35 + r], fill=alpha)
overlay = Image.composite(Image.new("RGB", (W, H), (38, 30, 30)), overlay, mask)
og = Image.blend(og, overlay, 0.55)

draw = ImageDraw.Draw(og)

# --- HERO: large personal logo lockup (icon + "Shayan Spiel") ---
lockup = Image.open(PERSONAL_PRIMARY_PNG).convert("RGBA")
lockup_target_w = 1040  # ~1.73x of the 600px source; the wordmark dominates
ratio = lockup_target_w / lockup.width
lockup_h = int(lockup.height * ratio)
lockup = lockup.resize((lockup_target_w, lockup_h), Image.LANCZOS)
lockup_x = (W - lockup_target_w) // 2
lockup_y = 110
og.paste(lockup, (lockup_x, lockup_y), lockup)

# --- Position copy block beneath the lockup ---
f_method = load_font(56, bold=True)
f_audience = load_font(34, bold=False)
f_under = load_font(22, bold=False)

copy_y = lockup_y + lockup_h + 64
method_text = "Session-as-Content."
audience_text = "For technical founders who build in public."

# Center each line
def center_text(draw, text, font, y, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((W - w) // 2, y), text, font=font, fill=fill)

center_text(draw, method_text, f_method, copy_y, (245, 245, 245))
center_text(draw, audience_text, f_audience, copy_y + 70, (180, 180, 180))

# --- Footer rule + URL ---
rule_y = 545
draw.line([(120, rule_y), (W - 120, rule_y)], fill=(60, 60, 60), width=1)

f_url = load_font(20, bold=False)
url_text = "spielos.xyz"
f_meta = load_font(18, bold=False)
meta_text = "Solo operator. Building Session-as-Content Infrastructure. Based in Tehran."

draw.text((120, rule_y + 18), url_text, font=f_url, fill=(200, 200, 200))
bbox = draw.textbbox((0, 0), meta_text, font=f_meta)
meta_w = bbox[2] - bbox[0]
draw.text((W - 120 - meta_w, rule_y + 22), meta_text, font=f_meta, fill=(120, 120, 120))

og.save(os.path.join(ROOT, "assets", "og-default.png"), "PNG", optimize=True)
print("wrote assets/og-default.png (1200x630)")
