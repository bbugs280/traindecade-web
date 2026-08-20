"""Generate dark/cinematic placeholder hero+cover images for Train Decade.

Produces 3 images at 1.91:1 (1600x838) dark gradient + subtle text, matching
the eventual Nano Banana style (dark, cinematic) so Vincent can hot-swap the
real generated art later by replacing files in assets/ + static/.
"""
import os

try:
    from PIL import Image, ImageDraw, ImageFilter
except ImportError as e:
    print("PIL NOT AVAILABLE:", e)
    raise SystemExit(2)

ASSETS = os.path.expanduser("~/Projects/traindecade-web/assets")
STATIC = os.path.expanduser("~/Projects/traindecade-web/static/images")
os.makedirs(STATIC, exist_ok=True)

W, H = 1600, 838  # 1.91:1


def make_img(path, title, sub, accent, c1, c2):
    img = Image.new("RGB", (W, H), c1)
    d = ImageDraw.Draw(img)
    # vertical gradient
    for y in range(H):
        t = y / H
        r = int(c1[0] + (c2[0] - c1[0]) * t)
        g = int(c1[1] + (c2[1] - c1[1]) * t)
        b = int(c1[2] + (c2[2] - c1[2]) * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))
    # soft vignette
    glow = Image.new("RGB", (W, H), (0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rectangle([0, 0, W, H], fill=(0, 0, 0))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.composite(img, glow, Image.new("L", (W, H), 160))
    d = ImageDraw.Draw(img)
    # text
    from PIL import ImageFont
    f_title = None
    f_sub = None
    for cand in ("/System/Library/Fonts/Helvetica.ttc",
                 "/Library/Fonts/Arial.ttf"):
        if os.path.exists(cand):
            try:
                f_title = ImageFont.truetype(cand, 72)
                f_sub = ImageFont.truetype(cand, 34)
                break
            except Exception:
                continue
    if f_title is None:
        f_title = ImageFont.load_default()
        f_sub = ImageFont.load_default()
    tw = d.textlength(title, font=f_title)
    d.text(((W - tw) / 2, H * 0.38), title, font=f_title, fill=accent)
    sw = d.textlength(sub, font=f_sub)
    d.text(((W - sw) / 2, H * 0.58), sub, font=f_sub, fill=(220, 220, 220))
    img.save(path, quality=92)
    print("wrote", path)


NAVY = (12, 20, 38)
CHARCOAL = (6, 8, 14)
CRIMSON = (196, 54, 74)
JADE = (52, 148, 128)

# Hero (goes to static/images) + two article covers (assets/)
make_img(os.path.join(STATIC, "hero.jpg"), "TRAIN DECADE",
         "The long game — a decade of strength, not six weeks", CRIMSON, NAVY, CHARCOAL)
make_img(os.path.join(ASSETS, "cover-welcome.png"), "Welcome",
         "Fitness, health, and body recomposition over years", JADE, NAVY, CHARCOAL)
make_img(os.path.join(ASSETS, "cover-decade.png"), "Why a Decade",
         "Not a six-week challenge", CRIMSON, NAVY, CHARCOAL)
