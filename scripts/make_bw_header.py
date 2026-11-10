"""Black & white services header (2400x1260). Portrait cropped to fill the
frame, thin circle drawn around her with the services placed on nodes."""
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

SRC, OUT = sys.argv[1], sys.argv[2]
W, H = 2400, 1260
FD = "/usr/share/fonts/opentype/inter/"
WHITE = (245, 245, 243)
INK = (28, 28, 28)

# --- crop portrait to fill 2400x1260 ---
src = ImageOps.grayscale(Image.open(SRC))
s = W / src.width
src = src.resize((W, round(src.height * s)), Image.LANCZOS)
FACE_Y = 470 * s                     # face centre in the scaled photo
top = int(FACE_Y - 0.36 * H)
img = src.crop((0, top, W, top + H))

# natural tones: light touch of contrast, very soft vignette
a = np.asarray(img).astype(np.float32) / 255
a = np.clip(((a ** 1.08) - 0.5) * 1.08 + 0.5, 0, 1)
yy, xx = np.mgrid[0:H, 0:W]
vig = 1 - 0.18 * (((xx - W / 2) / (W / 1.5)) ** 2 + ((yy - H / 2) / (H / 1.1)) ** 2)
a = a * np.clip(vig, 0.8, 1)
canvas = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))

# --- circle around her ---
d = ImageDraw.Draw(layer)
ink_layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
di = ImageDraw.Draw(ink_layer)
cx, cy, r = 1280, 650, 450
d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=WHITE, width=3)

lab = ImageFont.truetype(FD + "Inter-Regular.otf", 30)
LH = 40

services = [
    ["PERSONAL", "BRANDING"],
    ["1:1 STRATEGY", "CALLS"],
    ["DIGITAL", "STRATEGY"],
    ["STEP ONE CREATE", "COACHING COMMUNITY"],
    ["SOCIAL MEDIA", "MANAGEMENT"],
    ["CONTENT", "MARKETING"],
    ["CREATIVE", "STRATEGY"],
]
# clockwise from the top; lower nodes kept off her shoulders
ANGLES = [-90, -42, 0, 32, 148, 180, -138]
for lines, deg in zip(services, ANGLES):
    ang = math.radians(deg)
    c, sn = math.cos(ang), math.sin(ang)
    nx, ny = cx + r * c, cy + r * sn
    d.ellipse([nx - 9, ny - 9, nx + 9, ny + 9], fill=WHITE)
    total = LH * len(lines)
    for j, t in enumerate(lines):
        w = d.textlength(t, font=lab)
        if abs(c) > 0.3:                      # side labels
            tx = nx + 36 if c > 0 else nx - 36 - w
            ty = ny - total / 2 + j * LH + 4
        elif sn < 0:                          # above
            tx, ty = nx - w / 2, ny - 30 - total + j * LH
        else:                                 # below
            tx, ty = nx - w / 2, ny + 30 + j * LH
        bb = (int(tx), int(ty), int(tx + w), int(ty + LH))
        lum = np.asarray(canvas.convert("L").crop(bb)).mean()
        col = WHITE if lum < 120 else INK
        (d if col == WHITE else di).text((tx, ty), t, font=lab, fill=col)

# soft shadow under the white line work so it reads on the light wall
alpha = layer.getchannel("A").filter(ImageFilter.GaussianBlur(5))
shadow = Image.new("RGBA", (W, H), (20, 20, 20, 0))
shadow.putalpha(alpha.point(lambda v: int(v * 0.75)))
canvas = Image.alpha_composite(Image.alpha_composite(canvas, shadow), layer)
canvas = Image.alpha_composite(canvas, ink_layer).convert("RGB")
canvas.save(OUT)
print("saved", OUT, canvas.size, "circle", cx, cy, r)
