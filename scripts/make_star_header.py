"""Light, natural B&W header (2400x1260): portrait centred, services scattered
around her as small labels with a star, handwritten notes left and right."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

SRC, OUT = sys.argv[1], sys.argv[2]
W, H = 2400, 1260
INTER = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"
STAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
HAND = "assets/fonts/RockSalt-Regular.ttf"
INK = (22, 22, 22)

# --- portrait: crop head & shoulders, light natural B&W ---
src = ImageOps.grayscale(Image.open(SRC))
TOP, BOT, FACE_X = 320, 860, 600          # window in original photo px
s = H / (BOT - TOP)
src = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
ox = int(W / 2 - FACE_X * s)
port = src.crop((0, int(TOP * s), src.width, int(TOP * s) + H))

a = np.asarray(port).astype(np.float32) / 255
a = np.clip(a ** 0.8 * 1.05, 0, 1)          # lift the wall towards paper white
port = Image.fromarray((a * 255).astype(np.uint8))

# sides: stretch the photo's own edge columns so the wall continues
arr = np.asarray(port)
bg = np.empty((H, W), np.uint8)
bg[:, :] = arr[:, 4:24].mean(1, keepdims=True)
bg[:, ox + port.width // 2:] = arr[:, -24:-4].mean(1, keepdims=True)
bg = Image.fromarray(bg).filter(ImageFilter.GaussianBlur(40))
mask = Image.new("L", port.size, 255)
md = ImageDraw.Draw(mask)
for i in range(120):                         # feather left/right edges
    v = int(255 * i / 120)
    md.line([(i, 0), (i, H)], fill=v)
    md.line([(port.width - 1 - i, 0), (port.width - 1 - i, H)], fill=v)
bg.paste(port, (ox, 0), mask)
canvas = bg.convert("RGB")

# --- type ---
d = ImageDraw.Draw(canvas)
lab = ImageFont.truetype(INTER, 30)
star = ImageFont.truetype(STAR, 26)
hand = ImageFont.truetype(HAND, 46)

def service(text, x, y):
    lines = text.split("\n")
    for i, t in enumerate(lines):
        d.text((x, y + i * 38), t, font=lab, fill=INK, anchor="ma")
    d.text((x, y + len(lines) * 38 + 10), "★", font=star, fill=INK, anchor="ma")

SERVICES = [
    ("Personal Branding",         600, 110),
    ("Content Marketing",         400, 360),
    ("Social Media\nManagement",  290, 880),
    ("1:1 Strategy Calls",        1830, 110),
    ("Digital Strategy",          2030, 360),
    ("Creative Strategy",         1990, 840),
    ("Step One Create\nCoaching Community", 2100, 1040),
]
for t, x, y in SERVICES:
    service(t, x, y)

d.text((80, 590), "HI! I'M A...", font=hand, fill=INK)
d.text((2330, 560), "NICE MEETING", font=hand, fill=INK, anchor="ra")
d.text((2330, 640), "YOU!", font=hand, fill=INK, anchor="ra")

canvas.save(OUT)
print("saved", OUT, canvas.size, "photo x", ox, port.width)
