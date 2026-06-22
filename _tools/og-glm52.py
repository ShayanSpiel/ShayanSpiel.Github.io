#!/usr/bin/env python3
"""Generate the OG image for /GLM5.2-Cost-Breakdown/.

1200x630, dark surface, skull logo, page title, new broader positioning
(AI Operator, Agentic AI, Content Systems, Games). No wordmark typography.
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ICON_LOGO = os.path.join(ROOT, "assets", "logos", "icon-transparent.png")
OUT = os.path.join(ROOT, "assets", "uploads", "glm52-pricing.png")

W, H = 1200, 630

# ── Surface ──
og = Image.new("RGB", (W, H), (10, 10, 10))

# Subtle radial gradient (warm dark center)
overlay = Image.new("RGB", (W, H), (10, 10, 10))
mask = Image.new("L", (W, H), 0)
md = ImageDraw.Draw(mask)
for r in range(800, 0, -20):
    alpha = int(40 * (1 - r / 800))
    md.ellipse([W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r], fill=alpha)
overlay = Image.composite(Image.new("RGB", (W, H), (32, 24, 24)), overlay, mask)
og = Image.blend(og, overlay, 0.5)

# ── Skull logo (left) ──
logo = Image.open(ICON_LOGO).convert("RGBA")
target_h = 360
ratio = target_h / logo.height
logo = logo.resize((int(logo.width * ratio), target_h), Image.LANCZOS)
LOGO_X, LOGO_Y = 90, (H - target_h) // 2
og.paste(logo, (LOGO_X, LOGO_Y), logo)

# ── Fonts ──
def load_font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()


draw = ImageDraw.Draw(og)

f_brand = load_font(22, bold=True)
f_meta = load_font(20, bold=False)
f_role = load_font(26, bold=True)
f_role_sub = load_font(20, bold=False)
f_title_1 = load_font(72, bold=True)
f_title_2 = load_font(72, bold=True)
f_desc = load_font(28, bold=False)
f_desc_sub = load_font(22, bold=False)
f_url = load_font(22, bold=True)
f_foot = load_font(20, bold=False)

# ── Right column ──
RX = LOGO_X + logo.width + 70
LINE_TOP = 100

# Top eyebrow: site brand
draw.text((RX, LINE_TOP), "SHAYAN SPIEL", font=f_brand, fill=(229, 229, 229))

# Author positioning — broader than Session-as-Content
draw.text((RX, LINE_TOP + 36), "AI Operator  ·  Builder", font=f_role, fill=(245, 245, 245))
draw.text(
    (RX, LINE_TOP + 76),
    "Agentic AI  ·  Content Systems  ·  Games",
    font=f_role_sub,
    fill=(160, 160, 160),
)

# Divider
DIV_Y = LINE_TOP + 130
draw.line([(RX, DIV_Y), (W - 90, DIV_Y)], fill=(50, 50, 50), width=1)

# Page title (two lines, large)
TITLE_Y = DIV_Y + 40
draw.text((RX, TITLE_Y), "Is GLM-5.2 cheaper", font=f_title_1, fill=(255, 255, 255))
draw.text((RX, TITLE_Y + 90), "than the frontier?", font=f_title_2, fill=(255, 255, 255))

# Page subtitle
SUB_Y = TITLE_Y + 200
draw.text(
    (RX, SUB_Y),
    "LLM API pricing breakdown",
    font=f_desc,
    fill=(200, 200, 200),
)
draw.text(
    (RX, SUB_Y + 38),
    "Z.ai  ·  Anthropic  ·  OpenAI  ·  Google",
    font=f_desc_sub,
    fill=(140, 140, 140),
)

# Footer rule
draw.line([(RX, H - 90), (W - 90, H - 90)], fill=(50, 50, 50), width=1)

# URL
draw.text(
    (RX, H - 70),
    "spielos.xyz/GLM5.2-Cost-Breakdown",
    font=f_url,
    fill=(229, 229, 229),
)

# Small date/version
date_text = "Jun 21, 2026  ·  spielos.xyz"
try:
    bbox = draw.textbbox((0, 0), date_text, font=f_foot)
    text_w = bbox[2] - bbox[0]
except AttributeError:
    text_w = draw.textlength(date_text, font=f_foot)
draw.text(
    (W - 90 - text_w, H - 70),
    date_text,
    font=f_foot,
    fill=(120, 120, 120),
)

og.save(OUT, "PNG", optimize=True)
print(f"wrote {OUT} (1200x630)")
