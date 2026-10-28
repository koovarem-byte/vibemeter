"""Запасные стикеры 512×512 (неон, прозрачный фон): python3 assets/stickers/make_stickers.py

Основные берутся из пака VibemeterNeon (stickers.PACK), эти — если Telegram
не примет эмодзи из пака стикером.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DIR = Path(__file__).resolve().parent
S = 512
VIOLET, PINK, GOLD, WHITE = (155, 92, 255), (255, 61, 154), (255, 200, 97), (244, 240, 255)
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"
FONT_B = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"


def font(size, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, size)


def gradient(c1, c2):
    g = Image.new("RGBA", (S, S))
    px = g.load()
    for y in range(S):
        for x in range(S):
            t = (x + y) / (2 * S)
            px[x, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3)) + (255,)
    return g


def neon(mask: Image.Image, c1=VIOLET, c2=PINK) -> Image.Image:
    """Заливка градиентом по маске + мягкое свечение."""
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    glow_color = Image.new("RGBA", (S, S), c1 + (255,))
    for radius, alpha in ((28, 150), (12, 200)):
        glow = mask.filter(ImageFilter.GaussianBlur(radius)).point(lambda v: v * alpha // 255)
        out = Image.alpha_composite(out, Image.composite(glow_color, out, glow))
    fill = gradient(c1, c2)
    out = Image.alpha_composite(out, Image.composite(fill, Image.new("RGBA", (S, S)), mask))
    return out


def text_layer(lines):
    """lines: [(текст, размер, y, цвет)] — белый текст с тёмной обводкой."""
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for text, size, y, color in lines:
        f = font(size)
        w = d.textlength(text, font=f)
        d.text(((S - w) / 2, y), text, font=f, fill=color, stroke_width=max(4, size // 12), stroke_fill=(20, 8, 40, 255))
    return layer


def diamond_mask(cx, cy, w, h):
    m = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    top = cy - h * 0.38
    mid = cy - h * 0.05
    d.polygon([(cx - w / 2, mid), (cx - w * 0.3, top), (cx + w * 0.3, top), (cx + w / 2, mid), (cx, cy + h * 0.55)], fill=255)
    return m


def heart_mask(cx, cy, r, mask=None):
    m = mask or Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(m)
    pts = []
    for i in range(200):
        t = math.pi * 2 * i / 200
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + x * r / 16, cy - y * r / 16))
    d.polygon(pts, fill=255)
    return m


def save(img, name):
    img.save(DIR / f"{name}.webp", "WEBP", lossless=True)
    print("ok", name)


def vip_girls():
    img = neon(diamond_mask(256, 190, 300, 260))
    img = Image.alpha_composite(img, text_layer([
        ("VIP", 120, 300, WHITE),
        ("девушкам бесплатно", 40, 440, GOLD),
    ]))
    save(img, "sticker_2_vip_girls")


def vip_7days():
    img = neon(diamond_mask(256, 150, 220, 190), VIOLET, GOLD)
    img = Image.alpha_composite(img, text_layer([
        ("VIP", 104, 220, WHITE),
        ("на 7 дней", 58, 340, GOLD),
        ("за 3 подруги", 40, 420, WHITE),
    ]))
    save(img, "sticker_3_vip_7days")


def match():
    m = heart_mask(200, 200, 120)
    heart_mask(320, 215, 120, m)
    img = neon(m, VIOLET, PINK)
    img = Image.alpha_composite(img, text_layer([
        ("ВЗАИМНЫЙ", 66, 360, WHITE),
        ("ВАЙБ", 66, 432, WHITE),
    ]))
    save(img, "sticker_5_match")


if __name__ == "__main__":
    vip_girls()
    vip_7days()
    match()
