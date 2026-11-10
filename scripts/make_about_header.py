"""'About me' header (2400x1260): small torn paper note with handwritten list,
slightly tilted and paper-clipped over a natural B&W photo, on white."""
import sys, random, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

SRC, OUT = sys.argv[1], sys.argv[2]
W, H = 2400, 1260
HAND = "assets/fonts/IndieFlower-Regular.ttf"
INK = (34, 30, 160)
random.seed(7)
np.random.seed(7)

canvas = Image.new("RGB", (W, H), (255, 255, 255))

# --- photo block (large, right) ---
PX0, PY0, PX1, PY1 = 960, 110, 1840, 1070
pw, ph = PX1 - PX0, PY1 - PY0
src = ImageOps.grayscale(Image.open(SRC))
s = pw / src.width
src = src.resize((pw, round(src.height * s)), Image.LANCZOS)
top = int((int(sys.argv[3]) if len(sys.argv) > 3 else 270) * s)   # crop top, original px
photo = src.crop((0, top, pw, top + ph))
a = np.asarray(photo).astype(np.float32) / 255
a = np.clip(0.10 + 0.88 * (a ** 0.92), 0, 1)   # soft, lifted blacks
canvas.paste(Image.fromarray((a * 255).astype(np.uint8)).convert("RGB"), (PX0, PY0))

# --- note (built flat, then tilted) ---
NW, NH, M = 520, 760, 40                       # paper size + margin for rotation
LW, LH = NW + 2 * M, NH + 2 * M

def jag(p0, p1, n, amp):
    (x0, y0), (x1, y1) = p0, p1
    out = []
    for i in range(n):
        t = i / n
        x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        o = random.uniform(-amp, amp)
        if x0 == x1: x += o
        else: y += o
        out.append((x, y))
    return out

c = [(M, M), (M + NW, M), (M + NW, M + NH), (M, M + NH)]
poly = jag(c[0], c[1], 130, 4) + jag(c[1], c[2], 170, 4) + jag(c[2], c[3], 130, 4) + jag(c[3], c[0], 170, 4)
mask = Image.new("L", (LW, LH), 0)
ImageDraw.Draw(mask).polygon(poly, fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(0.8))

# paper texture: warm off-white, fine fibres
noise = np.random.normal(0, 1, (LH // 2, LW // 2)).astype(np.float32)
noise_img = Image.fromarray(((noise * 40) + 128).clip(0, 255).astype(np.uint8)).resize((LW, LH)).filter(ImageFilter.GaussianBlur(1.2))
nz = np.asarray(noise_img).astype(np.float32)
emb = np.asarray(noise_img.filter(ImageFilter.EMBOSS)).astype(np.float32)
base = np.array([240, 237, 229], np.float32)
tex = base + ((emb - 128) * 0.28)[..., None] + ((nz - 128) * 0.06)[..., None]
note = Image.fromarray(tex.clip(0, 255).astype(np.uint8)).convert("RGBA")

# handwriting
d = ImageDraw.Draw(note)
def spaced(x, y, text, font, track=3):
    for ch in text:
        d.text((x, y), ch, font=font, fill=INK)
        x += d.textlength(ch, font=font) + track
    return x

title = ImageFont.truetype(HAND, 44)
body = ImageFont.truetype(HAND, 27)

tx, ty = M + 70, M + 52
end = spaced(tx, ty, "ABOUT ME", title, 4)
d.line([(M + 40, ty + 64), (end + 60, ty + 61)], fill=INK, width=2)

lines = ["NASH, I'M THE FOUNDER", "BASED IN VANCOUVER", None,
         "PERSONAL BRANDING", "1:1 STRATEGY CALLS", "STEP ONE CREATE",
         "~COACHING COMMUNITY", "DIGITAL STRATEGY", "SOCIAL MEDIA MANAGEMENT",
         "CONTENT MARKETING", "CREATIVE STRATEGY"]
y = M + 165
bx = M + 62
for t in lines:
    if t is None:
        y += 22
        continue
    if t.startswith("~"):
        spaced(bx + 20, y, t[1:], body, 2)
    else:
        d.ellipse([bx, y + 19, bx + 6, y + 25], fill=INK)
        spaced(bx + 20, y, t, body, 2)
    y += 42
spaced(M + 200, y + 34, "AND STILL BUILDING...", body, 2)

note.putalpha(mask)
ANG = 1.4                                      # gentle tilt
note = note.rotate(ANG, resample=Image.BICUBIC, expand=True)
NX, NY = 460, 200
shadow_a = note.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: int(v * 0.28))
shadow = Image.new("RGBA", note.size, (40, 40, 40, 0)); shadow.putalpha(shadow_a)
canvas = canvas.convert("RGBA")
canvas.alpha_composite(shadow, (NX + 5, NY + 9))
canvas.alpha_composite(note, (NX, NY))

# --- small paperclip on the note's top edge (drawn 4x, downsampled) ---
def clip_path():
    pts = []
    def line(a, b, n=20):
        for i in range(n + 1):
            t = i / n
            pts.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    def arc(cx, cy, r, a0, a1, n=30):
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    line((10, 92), (10, 24)); arc(17, 24, 7, 180, 360)
    line((24, 24), (24, 108)); arc(12, 108, 12, 0, 180)
    line((0, 108), (0, 17)); arc(17, 17, 17, 180, 360)
    line((34, 17), (34, 84))
    return pts

def paste_clip(x, y, scale=0.72, ss=4):
    k = scale * ss
    pad = 6 * ss
    lw, lh = int(34 * k + 2 * pad), int(120 * k + 2 * pad)
    lay = Image.new("RGBA", (lw, lh), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    P = [(px * k + pad, py * k + pad) for px, py in clip_path()]
    ld.line([(px + 2 * ss, py + 3 * ss) for px, py in P], fill=(0, 0, 0, 55), width=int(2.6 * ss), joint="curve")
    ld.line(P, fill=(95, 97, 102, 255), width=int(2.6 * ss), joint="curve")
    ld.line([(px - 0.5 * ss, py - 0.5 * ss) for px, py in P], fill=(205, 207, 210, 200), width=int(0.9 * ss), joint="curve")
    lay = lay.resize((lw // ss, lh // ss), Image.LANCZOS).rotate(ANG, resample=Image.BICUBIC, expand=True)
    canvas.alpha_composite(lay, (x, y))

paste_clip(NX + M + NW - 120, NY + 6)

# stay tuned (under the photo)
cd = ImageDraw.Draw(canvas)
small = ImageFont.truetype(HAND, 34)
st = "stay tuned for more!"
w = sum(cd.textlength(ch, font=small) + 3 for ch in st)
x = PX1 - w
for ch in st:
    cd.text((x, PY1 + 30), ch, font=small, fill=INK)
    x += cd.textlength(ch, font=small) + 3

canvas.convert("RGB").save(OUT)
print("saved", OUT, canvas.size, "list ends y", y, "of", M + NH)
