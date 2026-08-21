"""Generate neon/dark article-cover + hero images for Train Decade.

Style reference: freeaitool.com — dark (deep navy/black) backgrounds, neon
(crimson/jade) glowing accents, bold text overlays, ~16:9 cards. Stylized
illustration-grade placeholders (flat vector + neon glow) until real Nano
Banana art is generated.
"""
import os
import math

try:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
except ImportError as e:
    print("PIL NOT AVAILABLE:", e)
    raise SystemExit(2)

ASSETS = os.path.expanduser("~/Projects/traindecade-web/assets")
STATIC = os.path.expanduser("~/Projects/traindecade-web/static/images")
os.makedirs(STATIC, exist_ok=True)

# 16:9 for article cards (matches freeaitool) ; hero slightly wider
W, H = 1280, 720       # 16:9 article cover
WH, HH = 1920, 720     # hero banner 2.67:1


def _font(size):
    for cand in ("/System/Library/Fonts/Helvetica.ttc",
                 "/Library/Fonts/Arial.ttf",
                 "/System/Library/Fonts/HelveticaNeue.ttc"):
        if os.path.exists(cand):
            try:
                return ImageFont.truetype(cand, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _radial_glow(size, center, radius, color, alpha):
    w, h = size
    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy = center
    steps = 40
    for i in range(steps, 0, -1):
        r = int(radius * i / steps)
        a = int(alpha * (1 - i / steps) * (i / steps))
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color + (a,))
    return glow.filter(ImageFilter.GaussianBlur(12))


def make_cover(path, title, tag, accent, c_top, c_bot, sub=None):
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    # diagonal-ish vertical gradient
    for y in range(H):
        t = y / H
        r = int(c_top[0] + (c_bot[0] - c_top[0]) * t)
        g = int(c_top[1] + (c_bot[1] - c_top[1]) * t)
        b = int(c_top[2] + (c_bot[2] - c_top[2]) * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))

    base = img.convert("RGBA")
    # neon glow top-right + bottom-left
    g1 = _radial_glow((W, H), (int(W * 0.85), int(H * 0.18)), int(H * 0.55),
                      accent, 110)
    g2 = _radial_glow((W, H), (int(W * 0.12), int(H * 0.88)), int(H * 0.60),
                      accent, 80)
    base = Image.alpha_composite(base, g1)
    base = Image.alpha_composite(base, g2)
    img = base.convert("RGB")
    d = ImageDraw.Draw(img)

    # accent geometric accents (thin lines / bars) — fake "UI" feel
    d.rectangle([int(W * 0.06), int(H * 0.16), int(W * 0.06) + 6, int(H * 0.16) + 6],
                fill=accent)
    d.line([int(W * 0.06) + 16, int(H * 0.16) + 3, int(W * 0.20), int(H * 0.16) + 3],
           fill=accent, width=3)

    # tag pill (category)
    f_tag = _font(30)
    tag_txt = tag.upper()
    tw = d.textlength(tag_txt, font=f_tag)
    pad = 22
    pill = [int(W * 0.06), int(H * 0.06), int(W * 0.06) + tw + pad * 2, int(H * 0.06) + 64]
    d.rounded_rectangle(pill, radius=32, fill=accent)
    d.text((pill[0] + pad, pill[1] + 12), tag_txt, font=f_tag, fill=(255, 255, 255))

    # title
    f_title = _font(88)
    words = title.split()
    line1 = " ".join(words[: len(words) // 2 or 1])
    line2 = " ".join(words[(len(words) // 2 or 1):])
    y = int(H * 0.52)
    for line in (line1, line2):
        if not line:
            continue
        lw = d.textlength(line, font=f_title)
        d.text(((W - lw) / 2, y), line, font=f_title, fill=(240, 242, 245))
        y += 100

    # sub
    if sub:
        f_sub = _font(36)
        sw = d.textlength(sub, font=f_sub)
        d.text(((W - sw) / 2, int(H * 0.80)), sub, font=f_sub, fill=accent)

    img.save(path, quality=92)
    print("wrote", path)


def make_hero(path, title, sub, accent, c_top, c_bot):
    img = Image.new("RGB", (WH, HH))
    d = ImageDraw.Draw(img)
    for y in range(HH):
        t = y / HH
        r = int(c_top[0] + (c_bot[0] - c_top[0]) * t)
        g = int(c_top[1] + (c_bot[1] - c_top[1]) * t)
        b = int(c_top[2] + (c_bot[2] - c_top[2]) * t)
        d.line([(0, y), (WH, y)], fill=(r, g, b))
    base = img.convert("RGBA")
    g1 = _radial_glow((WH, HH), (int(WH * 0.78), int(HH * 0.30)), int(HH * 0.7),
                      accent, 120)
    g2 = _radial_glow((WH, HH), (int(WH * 0.10), int(HH * 0.85)), int(HH * 0.7),
                      accent, 90)
    base = Image.alpha_composite(base, g1)
    base = Image.alpha_composite(base, g2)
    img = base.convert("RGB")
    d = ImageDraw.Draw(img)

    f_title = _font(120)
    tw = d.textlength(title, font=f_title)

    # subtle dumbbell motif above the title (two plates + bar)
    cy = int(HH * 0.20)
    cx = WH // 2
    bar_y = cy
    d.rounded_rectangle([cx - 140, bar_y - 8, cx + 140, bar_y + 8], radius=8,
                        fill=accent)
    _plate = lambda x: d.rounded_rectangle(
        [x - 26, bar_y - 46, x + 26, bar_y + 46], radius=16, fill=accent)
    _plate(cx - 140)
    _plate(cx + 140)
    _plate(cx - 96)
    _plate(cx + 96)

    d.text(((WH - tw) / 2, int(HH * 0.34)), title, font=f_title, fill=(240, 242, 245))

    f_sub = _font(44)
    sw = d.textlength(sub, font=f_sub)
    d.text(((WH - sw) / 2, int(HH * 0.66)), sub, font=f_sub, fill=accent)
    img.save(path, quality=92)
    print("wrote", path)


NAVY = (13, 22, 40)
DEEP = (5, 8, 14)
CRIMSON = (214, 61, 82)
JADE = (55, 155, 135)

# Article covers (16:9, assets/)
make_cover(os.path.join(ASSETS, "cover-decade.png"),
           "Why a Decade",
           "Mindset", CRIMSON, NAVY, DEEP,
           sub="Not a 6-week challenge")
make_cover(os.path.join(ASSETS, "cover-welcome.png"),
           "Welcome",
           "Traindecade", JADE, NAVY, DEEP,
           sub="The long game of strength")

# Hero (2.67:1, static/images/hero.jpg)
make_hero(os.path.join(STATIC, "hero.jpg"),
          "TRAIN DECADE",
          "20 years in. The long game works.",
          CRIMSON, NAVY, DEEP)
