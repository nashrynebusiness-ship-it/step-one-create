"""'About me' header (2400x1260): torn paper note with handwritten list,
paper-clipped over a natural B&W photo, on white."""
import sys, random
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

SRC, OUT = sys.argv[1], sys.argv[2]
W, H = 2400, 1260
HAND = "assets/fonts/IndieFlower-Regular.ttf"
INK = (34, 30, 160)
random.seed(7)
np.random.seed(7)

canvas = Image.new("RGB", (W, H), (255, 255, 255))

# --- photo block (right) ---
PX0, PY0, PX1, PY1 = 1060, 70, 2250, 1110
pw, ph = PX1 - PX0, PY1 - PY0
src = ImageOps.grayscale(Image.open(SRC))
s = pw / src.width * 1.0
src = src.resize((pw, round(src.height * s)), Image.LANCZOS)
top = int(270 * s)
photo = src.crop((0, top, pw, top + ph))
a = np.asarray(photo).astype(np.float32) / 255
a = np.clip(((a ** 1.05) - 0.5) * 1.1 + 0.5, 0, 1)
photo = Image.fromarray((a * 255).astype(np.uint8)).convert("RGB")
canvas.paste(photo, (PX0, PY0))

# --- torn paper (left, overlapping the photo) ---
NX0, NY0, NX1, NY1 = 230, 55, 1180, 1165

def jag(p0, p1, n, amp):
    (x0, y0), (x1, y1) = p0, p1
    pts = []
    for i in range(n):
        t = i / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        o = random.uniform(-amp, amp)
        if x0 == x1: x += o
        else: y += o
        pts.append((x, y))
    return pts

poly = (jag((NX0, NY0), (NX1, NY0), 160, 7) + jag((NX1, NY0), (NX1, NY1), 180, 7)
        + jag((NX1, NY1), (NX0, NY1), 160, 7) + jag((NX0, NY1), (NX0, NY0), 180, 7))
mask = Image.new("L", (W, H), 0)
ImageDraw.Draw(mask).polygon(poly, fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(1.2))

# paper texture: warm off-white with soft fibrous noise
noise = np.random.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
noise = np.asarray(Image.fromarray(((noise * 40) + 128).clip(0, 255).astype(np.uint8))
                   .resize((W, H)).filter(ImageFilter.GaussianBlur(1.5))).astype(np.float32)
emb = np.asarray(Image.fromarray(noise.astype(np.uint8)).filter(ImageFilter.EMBOSS)).astype(np.float32)
base = np.array([238, 235, 226], np.float32)
tex = base[None, None, :] + ((emb - 128) * 0.35)[..., None] + ((noise - 128) * 0.08)[..., None]
paper = Image.fromarray(tex.clip(0, 255).astype(np.uint8))

# deckled edge: slightly lighter, fuzzy rim
rim = mask.filter(ImageFilter.MinFilter(9))
edge = ImageOps.invert(rim).point(lambda v: 255 if v > 0 else 0)
edge = Image.composite(edge, Image.new("L", (W, H), 0), mask).filter(ImageFilter.GaussianBlur(3))
paper = Image.composite(Image.new("RGB", (W, H), (248, 246, 240)), paper, edge.point(lambda v: v // 2))

shadow = mask.filter(ImageFilter.GaussianBlur(14)).point(lambda v: int(v * 0.35))
canvas = Image.composite(Image.new("RGB", (W, H), (60, 60, 60)),
                         canvas, shadow.transform(
                             (W, H), Image.AFFINE, (1, 0, -6, 0, 1, -10)))
canvas = Image.composite(paper, canvas, mask)

# --- handwriting ---
d = ImageDraw.Draw(canvas)

def spaced(x, y, text, font, track=4):
    for ch in text:
        d.text((x, y), ch, font=font, fill=INK)
        x += d.textlength(ch, font=font) + track
    return x

title = ImageFont.truetype(HAND, 76)
body = ImageFont.truetype(HAND, 50)

tx, ty = 360, 130
end = spaced(tx, ty, "ABOUT ME", title, 6)
d.line([(NX0 + 70, ty + 108), (end + 120, ty + 104)], fill=INK, width=3)

lines = ["NASH, I'M THE FOUNDER", "BASED IN VANCOUVER", None,
         "PERSONAL BRANDING", "1:1 STRATEGY CALLS", "STEP ONE CREATE",
         "    COACHING COMMUNITY", "DIGITAL STRATEGY", "SOCIAL MEDIA MANAGEMENT",
         "CONTENT MARKETING", "CREATIVE STRATEGY"]
y = 300
for t in lines:
    if t is None:
        y += 40
        continue
    if not t.startswith("    "):
        d.ellipse([355, y + 36, 365, y + 46], fill=INK)
        spaced(392, y, t, body, 3)
    else:
        spaced(392, y, t.strip(), body, 3)
    y += 66

spaced(560, y + 40, "AND STILL BUILDING...", body, 3)

# stay tuned (under the photo)
small = ImageFont.truetype(HAND, 52)
st = "stay tuned for more!"
w = sum(d.textlength(c, font=small) + 4 for c in st)
spaced(PX1 - w, PY1 + 40, st, small, 4)

# --- paperclip on the paper's top edge ---
def clip(cx, cy, scale=1.0):
    col, wd = (70, 70, 72), 5
    def u(x0, x1, ytop, ybot):
        r = (x1 - x0) / 2
        d.arc([x0, ybot - 2 * r, x1, ybot], 0, 180, fill=col, width=wd)
        d.arc([x0, ytop, x1, ytop + 2 * r], 180, 360, fill=col, width=wd)
    # outer loop
    d.arc([cx - 30, cy - 10, cx + 30, cy + 50], 180, 360, fill=col, width=wd)
    d.line([(cx - 30, cy + 20), (cx - 30, cy + 200)], fill=col, width=wd)
    d.line([(cx + 30, cy + 20), (cx + 30, cy + 160)], fill=col, width=wd)
    d.arc([cx - 30, cy + 170, cx + 20, cy + 230], 0, 180, fill=col, width=wd)
    d.line([(cx + 20, cy + 200), (cx + 20, cy + 50)], fill=col, width=wd)
    d.arc([cx - 18, cy + 30, cx + 20, cy + 68], 180, 360, fill=col, width=wd)
    d.line([(cx - 18, cy + 49), (cx - 18, cy + 160)], fill=col, width=wd)

clip(1010, 20)

canvas.save(OUT)
print("saved", OUT, canvas.size, "list ends y", y)
