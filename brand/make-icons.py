#!/usr/bin/env python3
"""Generate the marketing site's logo and icon files from the master BillVexa logo.

Source: apps/billvexa-ui/public/assets/images/billvexa-half-logo-t.png (the same mark the
app and the transactional emails use). Run from anywhere:

    python3 marketing/coming-soon/brand/make-icons.py

Writes (into marketing/coming-soon/):
    logo.png              trimmed mark, transparent, 136px tall (4x the 34px nav/footer mark)
    favicon.svg           the mark embedded as a data URI (crisp at any size in modern browsers)
    favicon.ico           16 / 32 / 48 px, transparent
    apple-touch-icon.png  180 px on the site background (iOS ignores transparency)

og-image.png is NOT written here — re-render it from brand/og-image.html (see its header).
Requires Pillow.
"""
from __future__ import annotations

import base64
import io
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
SITE = HERE.parent
REPO = SITE.parent.parent
SOURCE = REPO / "apps/billvexa-ui/public/assets/images/billvexa-half-logo-t.png"
SITE_BG = "#F5F7FA"  # --bg in index.html


def trimmed_mark() -> Image.Image:
    im = Image.open(SOURCE).convert("RGBA")
    bbox = im.getchannel("A").getbbox()
    return im.crop(bbox)


def fit(im: Image.Image, *, height: int | None = None, width: int | None = None) -> Image.Image:
    w, h = im.size
    if height is not None:
        width = round(w * height / h)
    elif width is not None:
        height = round(h * width / w)
    return im.resize((width, height), Image.LANCZOS)


def on_square(im: Image.Image, size: int, pad: float, bg: str | None) -> Image.Image:
    inner = round(size * (1 - 2 * pad))
    mark = fit(im, width=inner) if im.width >= im.height else fit(im, height=inner)
    canvas = Image.new("RGBA", (size, size), bg or (0, 0, 0, 0))
    canvas.alpha_composite(mark, ((size - mark.width) // 2, (size - mark.height) // 2))
    return canvas


def main() -> None:
    mark = trimmed_mark()

    # 136px tall = 4x the 34px nav mark and 2x the 64px og-image mark. Palette PNG keeps it small.
    logo = fit(mark, height=136)
    logo.quantize(256, method=Image.Quantize.FASTOCTREE).save(SITE / "logo.png", optimize=True)
    print("logo.png", logo.size)

    fav = fit(mark, height=64)
    buf = io.BytesIO()
    fav.quantize(256, method=Image.Quantize.FASTOCTREE).save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode()
    w, h = fav.size
    (SITE / "favicon.svg").write_text(
        f"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 {w} {h}'>"
        f"<image width='{w}' height='{h}' href='data:image/png;base64,{b64}'/></svg>\n"
    )
    print("favicon.svg")

    ico_sizes = [48, 32, 16]
    frames = [on_square(mark, s, 0.0, None) for s in ico_sizes]
    frames[0].save(
        SITE / "favicon.ico",
        format="ICO",
        sizes=[(s, s) for s in ico_sizes],
        append_images=frames[1:],
    )
    print("favicon.ico", ico_sizes)

    touch = on_square(mark, 180, 0.16, SITE_BG).convert("RGB")
    touch.save(SITE / "apple-touch-icon.png", optimize=True)
    print("apple-touch-icon.png", touch.size)


if __name__ == "__main__":
    main()
