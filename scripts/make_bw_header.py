"""Black & white services header (2400x1260, same size as header-services.png).
Portrait on the left over an extended studio wall; services arranged on a thin
circle with nodes on the right."""
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

SRC, OUT = sys.argv[1], sys.argv[2]
W, H = 2400, 1260
FD = "/usr/share/fonts/opentype/inter/"
WHITE = (245, 245, 243)

# --- portrait: grayscale, moodier tones ---
src = ImageOps.grayscale(Image.open(SRC))
ph = 1420                                   # scale so a little top wall is cropped
pw = round(src.width * ph / src.height)
src = src.resize((pw, ph), Image.LANCZOS)
ox, oy = 120, H - ph                        # anchor bottom-left-ish

a = np.asarray(src).astype(np.float32) / 255
a = a ** 1.9                                # darken mids: light wall -> charcoal
a = np.clip((a - 0.5) * 1.15 + 0.5, 0, 1)   # a touch more contrast
port = Image.fromarray((a * 255).astype(np.uint8))

# --- background: stretch portrait edge columns sideways, then blur ---
arr = np.asarray(port)
bg = np.zeros((H, W), np.uint8)
rows = arr[-oy:, :]                         # visible rows (H tall)
left = rows[:, 4:20].mean(1, keepdims=True)
right = rows[:, -20:-4].mean(1, keepdims=True)
bg[:, :ox + 20] = left
bg[:, ox + pw - 20:] = right
bg = Image.fromarray(bg)
canvas = bg.copy()
canvas.paste(port, (ox, oy))
# feather the seams by blending with a blurred version near the edges
blur = canvas.filter(ImageFilter.GaussianBlur(60))
seam = Image.new("L", (W, H), 0)
sd = ImageDraw.Draw(seam)
for x0 in (ox, ox + pw):
    sd.rectangle([x0 - 90, 0, x0 + 90, H], fill=255)
seam = seam.filter(ImageFilter.GaussianBlur(50))
canvas = Image.composite(blur, canvas, seam)

# right-side darkening so white type reads, plus soft vignette
g = np.asarray(canvas).astype(np.float32)
xs = np.linspace(0, 1, W)[None, :]
ramp = np.clip((xs - 0.38) / 0.35, 0, 1) * 0.55
yy, xx = np.mgrid[0:H, 0:W]
vig = 1 - 0.35 * (((xx - W / 2) / (W / 1.6)) ** 2 + ((yy - H / 2) / (H / 1.2)) ** 2)
g = g * (1 - ramp) * np.clip(vig, 0.6, 1)
canvas = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert("RGB")

# --- circle diagram ---
d = ImageDraw.Draw(canvas)
cx, cy, r = 1730, 640, 360
d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=WHITE, width=3)

lab = ImageFont.truetype(FD + "Inter-Regular.otf", 30)
center = ImageFont.truetype(FD + "Inter-Light.otf", 84)

def text_block(lines, x, y, anchor):
    """anchor: 'b' bottom-centred, 't' top-centred, 'l' left-mid, 'r' right-mid"""
    lh = 40
    total = lh * len(lines)
    for i, t in enumerate(lines):
        w = d.textlength(t, font=lab)
        if anchor in "bt":
            tx = x - w / 2
            ty = (y - total if anchor == "b" else y) + i * lh
            d.text((tx, ty), t, font=lab, fill=WHITE, anchor="la")
        else:
            ty = y - total / 2 + i * lh
            tx = x if anchor == "l" else x - w
            d.text((tx, ty), t, font=lab, fill=WHITE, anchor="la")

services = [
    (-90, ["PERSONAL", "BRANDING"], "b"),
    (0,   ["1:1 STRATEGY", "CALLS"], "l"),
    (90,  ["STEP ONE CREATE AGENCY", "COACHING COMMUNITY"], "t"),
    (180, ["SOCIAL MEDIA", "MANAGEMENT"], "r"),
]
for ang, lines, anc in services:
    t = math.radians(ang)
    nx, ny = cx + r * math.cos(t), cy + r * math.sin(t)
    d.ellipse([nx - 9, ny - 9, nx + 9, ny + 9], fill=WHITE)
    off = 30
    pos = {"b": (nx, ny - off), "t": (nx, ny + off + 4),
           "l": (nx + off, ny + 4), "r": (nx - off, ny + 4)}[anc]
    text_block(lines, *pos, anc)

d.text((cx, cy), "Work with me", font=center, fill=WHITE, anchor="mm")

canvas.save(OUT)
print("saved", OUT, canvas.size)
