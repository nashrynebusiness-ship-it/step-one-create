"""Render the services header: overlays service 'pills' (blurred grey panel +
cream outlined capsules, bold uppercase type) onto the original header collage."""
import sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance, ImageOps

SRC, OUT = sys.argv[1], sys.argv[2]
S = 2  # supersample: output at 2400x1260
FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
CREAM = (246, 243, 232, 255)

base = Image.open(SRC).convert("RGB")
base = base.resize((base.width * S, base.height * S), Image.LANCZOS)

# Panel region (1x coords) over the right column, below the headline
px0, py0, px1, py1 = 700, 232, 1092, 604
box = tuple(v * S for v in (px0, py0, px1, py1))
region = base.crop(box)
region = ImageOps.grayscale(region.filter(ImageFilter.GaussianBlur(14 * S))).convert("RGB")
region = ImageEnhance.Contrast(region).enhance(0.55)
grey = Image.new("RGB", region.size, (122, 125, 129))
region = Image.blend(region, grey, 0.6)

mask = Image.new("L", region.size, 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, region.width - 1, region.height - 1], radius=6 * S, fill=255)
shadow = Image.new("RGBA", base.size, (0, 0, 0, 0))
ImageDraw.Draw(shadow).rounded_rectangle([box[0] + 4 * S, box[1] + 8 * S, box[2] + 4 * S, box[3] + 8 * S], radius=6 * S, fill=(0, 0, 0, 70))
shadow = shadow.filter(ImageFilter.GaussianBlur(10 * S))
base = Image.alpha_composite(base.convert("RGBA"), shadow)
base.paste(region, box[:2], mask)

d = ImageDraw.Draw(base)
f = ImageFont.truetype(FONT, 14 * S)
fs = ImageFont.truetype(FONT, 10.5 * S)
fl = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 9 * S)

pw = px1 - px0
pad = 18
inner_w = pw - 2 * pad
gap = 10
h = 64
hm = 86
vgap = 34


def pill(x, y, w, hh, lines):
    X, Y, W, H = x * S, y * S, w * S, hh * S
    d.rounded_rectangle([X, Y, X + W, Y + H], radius=H // 2, outline=CREAM, width=int(1.6 * S))
    total = sum(fnt.getbbox(t)[3] - fnt.getbbox(t)[1] for t, fnt in lines) + (len(lines) - 1) * 5 * S
    cy = Y + (H - total) / 2
    for t, fnt in lines:
        bb = d.textbbox((0, 0), t, font=fnt)
        d.text((X + (W - (bb[2] - bb[0])) / 2 - bb[0], cy - bb[1]), t, font=fnt, fill=CREAM)
        cy += (bb[3] - bb[1]) + 5 * S


# small label
label = "S E R V I C E S"
d.text(((px0 + pad) * S, (py0 + 22) * S), label, font=fl, fill=CREAM)

y = py0 + 60
half = (inner_w - gap) / 2
pill(px0 + pad, y, half, h, [("PERSONAL BRANDING", f)])
pill(px0 + pad + half + gap, y, half, h, [("1:1 STRATEGY CALLS", f)])
y += h + vgap
pill(px0 + pad, y, inner_w, hm, [("STEP ONE CREATE AGENCY", f), ("COACHING COMMUNITY", fs)])
y += hm + vgap
pill(px0 + pad, y, inner_w, h, [("SOCIAL MEDIA MANAGEMENT", f)])

base.convert("RGB").save(OUT, quality=95)
print("saved", OUT, base.size)
