"""Generates the site's brand assets from the official white Elyos logo.

    uv run --no-project --with pillow python site/tools/brand_assets.py <ElyosLogoBlanco.png>

Source logo: elyosracingteam.com (ElyosLogoBlanco.png, 6000 x 3375). Outputs in site/assets/:
logo-white.png (web size), favicon-32.png, apple-touch-icon.png, og.png (1200 x 630 share card).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

SITE = Path(__file__).resolve().parents[1]
ASSETS = SITE / "assets"
NAVY = (15, 56, 84)        # #0F3854, sampled from the logo
DEEP = (8, 32, 47)         # #08202F
SIGNAL = (94, 151, 255)    # #5E97FF


def trimmed(img: Image.Image) -> Image.Image:
    return img.crop(img.getchannel("A").point(lambda a: 255 if a > 8 else 0).getbbox())


def y_mark(logo: Image.Image) -> Image.Image:
    """The checkered Y: the glyph of the wordmark that holds the logo's navy pixels."""
    w, h = logo.size
    alpha = logo.getchannel("A")
    rows = [y for y in range(h) if alpha.crop((0, y, w, y + 1)).getbbox()]
    word_bottom = rows[0]  # wordmark = first band of rows; "RACING TEAM" comes after a gap
    for y in rows[1:]:
        if y - word_bottom > 4:
            break
        word_bottom = y
    word = logo.crop((0, rows[0], w, word_bottom + 1))
    px = word.load()
    occ = [any(px[x, y][3] > 8 for y in range(0, word.height, 3)) for x in range(w)]
    runs, start = [], None
    for x, o in enumerate(occ + [False]):
        if o and start is None:
            start = x
        elif not o and start is not None:
            runs.append((start, x))
            start = None
    def has_navy(r):
        return any(px[x, y][:3] == NAVY and px[x, y][3] > 200 for x in range(r[0], r[1], 3) for y in range(0, word.height, 6))
    x0, x1 = next(r for r in runs if has_navy(r))
    # The L can touch the Y: start where the checkered flag (grey or navy pixels, never pure white) begins.
    def tinted(x):
        return any(px[x, y][3] > 200 and px[x, y][:3] != (255, 255, 255) for y in range(0, word.height, 2))
    x0 = next(x for x in range(x0, x1) if tinted(x))
    mark = word.crop((x0, 0, x1, word.height))
    # remove the end of the L's foot that overlaps the crop (pure white, bottom-left, below the flag)
    mp = mark.load()
    for y in range(int(mark.height * 0.55), mark.height):
        for x in range(int(mark.width * 0.3)):
            if mp[x, y][:3] == (255, 255, 255):
                mp[x, y] = (0, 0, 0, 0)
    return mark


def icon(mark: Image.Image, size: int) -> Image.Image:
    """Y on the deep navy; its navy arm is lifted to the signal blue so it reads at small sizes."""
    bg = Image.new("RGBA", (size, size), DEEP + (255,))
    m = mark.copy()
    m.putdata([(SIGNAL + (a,)) if (r, g, b) == NAVY or (abs(r - 15) < 12 and abs(g - 56) < 12 and abs(b - 84) < 12)
               else (r, g, b, a) for r, g, b, a in m.getdata()])
    m.thumbnail((int(size * 0.8), int(size * 0.8)), Image.LANCZOS)
    bg.alpha_composite(m, ((size - m.width) // 2, (size - m.height) // 2))
    return bg


def og_card(logo: Image.Image) -> Image.Image:
    w, h = 1200, 630
    card = Image.new("RGBA", (w, h), DEEP + (255,))
    t = json.loads((SITE / "tracks.json").read_text(encoding="utf-8"))["ims"]
    vw, vh = (float(v) for v in t["viewBox"].split()[2:])
    pts = [tuple(float(c) for c in p.strip("MLZ ").split(",")) for p in t["d"].replace("M", "L").split("L") if "," in p]
    scale = min((w - 160) / vw, (h * 0.55) / vh)
    ox, oy = (w - vw * scale) / 2, h - vh * scale - 50
    xy = [(ox + x * scale, oy + y * scale) for x, y in pts]
    d = ImageDraw.Draw(card)
    d.line(xy + [xy[0]], fill=SIGNAL + (255,), width=5, joint="curve")
    lg = logo.copy()
    lg.thumbnail((620, 220), Image.LANCZOS)
    card.alpha_composite(lg, ((w - lg.width) // 2, 50))
    return card.convert("RGB")


def main(src: str) -> None:
    ASSETS.mkdir(exist_ok=True)
    logo = trimmed(Image.open(src).convert("RGBA"))
    web = logo.copy()
    web.thumbnail((900, 400), Image.LANCZOS)
    web.save(ASSETS / "logo-white.png", optimize=True)
    # header version: on the deep navy the logo's navy arm disappears, so it is lifted to the signal blue
    dark = web.copy()
    dark.putdata([(SIGNAL + (a,)) if abs(r - 15) < 14 and abs(g - 56) < 14 and abs(b - 84) < 14 and a > 0
                  else (r, g, b, a) for r, g, b, a in dark.getdata()])
    dark.save(ASSETS / "logo-on-dark.png", optimize=True)
    mark = y_mark(logo)
    icon(mark, 32).save(ASSETS / "favicon-32.png", optimize=True)
    icon(mark, 180).save(ASSETS / "apple-touch-icon.png", optimize=True)
    og_card(logo).save(ASSETS / "og.png", optimize=True)
    for f in sorted(ASSETS.iterdir()):
        print(f.name, f.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1])
