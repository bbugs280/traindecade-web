"""Generate elegant gradient banners for Train Decade.

Style reference: freeaitool.com — soft gradient background, elegant serif
background text (faint/decorative), centered bold sans-serif title + subtitle,
subtle thematic motifs. Palette adapted to Train Decade: deep navy → lighter
periwinkle gradient with crimson accent (pairing: teal/jade secondary).

These are the OPPOSITE of the earlier flat/dark AI art — light, airy, editorial.
"""
import os
import math
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

STATIC = os.path.expanduser("~/Projects/traindecade-web/static/images")
ASSETS = os.path.expanduser("~/Projects/traindecade-web/assets")
os.makedirs(STATIC, exist_ok=True)
os.makedirs(ASSETS, exist_ok=True)


def _font(size, bold=False):
    cands = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf",
    ]
    for c in cands:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _serif(size):
    for c in ("/System/Library/Fonts/Georgia.ttf",
              "/Library/Fonts/Georgia.ttf",
              "/System/Library/Fonts/Times New Roman.ttf"):
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return _font(size)


# --- palette (navy gradient, crimson accent; soft/airy) ---
C_TOP = (24, 32, 68)       # deep navy
C_BOT = (94, 106, 168)     # lighter periwinkle
ACCENT = (177, 33, 45)     # crimson
ACCENT2 = (52, 148, 128)   # jade


def _gradient(size, c1, c2, angle=0):
    w, h = size
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    # vertical gradient (angle ignored, kept simple)
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        d.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def _motif(d, cx, cy, radius, color, kind, alpha=140):
    """Draw a translucent thematic motif: dumbbell, hourglass, or leaf."""
    c = color + (alpha,)
    if kind == "dumbbell":
        # bar + two plate pairs
        bar_h = radius * 0.16
        d.rounded_rectangle([cx - radius, cy - bar_h, cx + radius, cy + bar_h],
                            radius=radius * 0.08, fill=c)
        for dx in (radius, radius * 0.62):
            for sign in (-1, 1):
                x = cx + sign * dx
                d.rounded_rectangle(
                    [x - radius * 0.22, cy - radius * 0.9,
                     x + radius * 0.22, cy + radius * 0.9],
                    radius=radius * 0.22, fill=c)
    elif kind == "hourglass":
        top = cy - radius
        r = radius * 0.5
        d.polygon([(cx - r, top), (cx + r, top), (cx, cy),
                   (cx - r, top + radius * 2), (cx + r, top + radius * 2),
                   (cx, cy)], fill=c)
    elif kind == "leaf":
        d.ellipse([cx - radius * 0.9, cy - radius * 0.35,
                   cx + radius * 0.9, cy + radius * 0.35], fill=c)


def _scatter_motifs(size, mot, n=9):
    """Return a translucent motif overlay (RGBA)."""
    w, h = size
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    random.seed(7)
    for _ in range(n):
        x = random.randint(int(w * 0.05), int(w * 0.95))
        y = random.randint(int(h * 0.05), int(h * 0.95))
        r = random.randint(int(min(w, h) * 0.03), int(min(w, h) * 0.09))
        col = random.choice([ACCENT, ACCENT2, ACCENT])
        d = ImageDraw.Draw(layer)
        _motif(d, x, y, r, col, mot, alpha=random.randint(60, 150))
    return layer.filter(ImageFilter.GaussianBlur(0.3))


def make_banner(path, title, subtitle, bg_text, motif, w, h):
    img = _gradient((w, h), C_TOP, C_BOT)
    base = img.convert("RGBA")
    layer = _scatter_motifs((w, h), motif)
    base = Image.alpha_composite(base, layer)
    # soft white glow center for depth
    glow = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([w * 0.3, -h * 0.3, w * 0.7, h * 0.7], fill=(255, 255, 255, 28))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    base = Image.alpha_composite(base, glow)
    img = base.convert("RGB")
    d = ImageDraw.Draw(img, "RGBA")

    # faint decorative serif background text (left, vertical-ish)
    fs = _serif(int(h * 0.045))
    d.text((int(w * 0.04), int(h * 0.06)), bg_text,
           font=fs, fill=(255, 255, 255, 90))

    # faint top-left partial word  ("Table" analog → "TRAIN")
    fbig = _serif(int(h * 0.16))
    d.text((int(w * 0.02), int(-h * 0.02)), "TRAIN",
           font=fbig, fill=(255, 255, 255, 60))

    # centered title (bold sans)
    ft = _font(int(h * 0.11))
    tw = d.textlength(title, font=ft)
    d.text(((w - tw) / 2, h * 0.40), title, font=ft, fill=(255, 255, 255, 255))

    # subtitle
    fs2 = _font(int(h * 0.038))
    sw = d.textlength(subtitle, font=fs2)
    d.text(((w - sw) / 2, h * 0.60), subtitle, font=fs2,
           fill=(240, 240, 245, 255))

    # accent underline (crimson)
    d.rounded_rectangle(
        [w * 0.40, h * 0.745, w * 0.60, h * 0.745 + int(h * 0.006)],
        radius=4, fill=(ACCENT[0], ACCENT[1], ACCENT[2], 220))

    img.save(path, quality=92)
    print("wrote", path)


# Hero banner (2.5:1) — brand hero
make_banner(
    os.path.join(STATIC, "hero.jpg"),
    "TRAIN DECADE",
    "The long game of strength and body recomposition",
    "Consistency over intensity. Evidence over hype.",
    "dumbbell", 1920, 768)

# Article covers (16:9)
make_banner(
    os.path.join(ASSETS, "cover-welcome.png"),
    "The Long Game",
    "Training and nutrition built to last a decade",
    "Train · Recover · Repeat",
    "leaf", 1280, 720)

make_banner(
    os.path.join(ASSETS, "cover-decade.png"),
    "Why a Decade",
    "Not a six-week challenge",
    "Slow compounds. Fast rebounds.",
    "hourglass", 1280, 720)
