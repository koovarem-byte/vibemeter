"""Анимированные неоновые стикеры (видеостикеры Telegram: WEBM VP9 с прозрачностью,
512×512, 3 с, 30 к/с, до 256 КБ). Запуск: python3 assets/stickers/make_stickers.py

Нужны Pillow и ffmpeg с libvpx-vp9. Рядом кладёт и статичный .webp (первый кадр) —
запасной, если Telegram не примет видео.
"""

import math
import random
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

DIR = Path(__file__).resolve().parent
S = 512
N = 90            # кадров: 3 секунды по 30
FPS = 30
MAX_BYTES = 256 * 1024

VIOLET = (155, 92, 255)
PINK = (255, 61, 154)
BLUE = (77, 163, 255)
GOLD = (255, 200, 97)
WHITE = (255, 248, 255)
FONT = "/usr/share/fonts/opentype/inter/Inter-Black.otf"


def font(size):
    return ImageFont.truetype(FONT, size)


def wave(t, shift=0.0):
    """0..1, плавно и по кругу: кадр N совпадает с кадром 0."""
    return 0.5 + 0.5 * math.sin(2 * math.pi * (t + shift))


def tube(draw_fn, color, width, glow=1.0):
    """Неоновая трубка: широкое свечение цвета + яркая середина + белая сердцевина."""
    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for w_mul, blur, alpha in ((2.6, 22, 0.55), (1.6, 9, 0.8)):
        m = Image.new("L", (S, S), 0)
        draw_fn(ImageDraw.Draw(m), int(width * w_mul), 255)
        m = m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v, a=alpha * glow: min(255, int(v * a)))
        out.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (S, S), color).split(), m)))
    core = Image.new("L", (S, S), 0)
    draw_fn(ImageDraw.Draw(core), width, 255)
    out.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (S, S), color).split(), core)))
    white = Image.new("L", (S, S), 0)
    draw_fn(ImageDraw.Draw(white), max(2, width // 3), 255)
    white = white.filter(ImageFilter.GaussianBlur(0.8))
    out.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (S, S), WHITE).split(), white)))
    return out


def neon_text(text, size, y, color, glow=1.0):
    f = font(size)
    probe = ImageDraw.Draw(Image.new("L", (1, 1)))
    w = probe.textlength(text, font=f)
    x = (S - w) / 2

    def draw(d, width, fill):
        d.text((x, y), text, font=f, fill=fill, stroke_width=max(1, width // 2), stroke_fill=fill)

    out = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    for stroke, blur, alpha in ((10, 18, 0.7), (5, 7, 0.9)):
        m = Image.new("L", (S, S), 0)
        draw(ImageDraw.Draw(m), stroke, 255)
        m = m.filter(ImageFilter.GaussianBlur(blur)).point(lambda v, a=alpha * glow: min(255, int(v * a)))
        out.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (S, S), color).split(), m)))
    edge = Image.new("L", (S, S), 0)
    ImageDraw.Draw(edge).text((x, y), text, font=f, fill=255, stroke_width=3, stroke_fill=255)
    out.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (S, S), color).split(), edge)))
    core = Image.new("L", (S, S), 0)
    ImageDraw.Draw(core).text((x, y), text, font=f, fill=255)
    out.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (S, S), WHITE).split(), core)))
    return out


def sparkle(img, cx, cy, r, color, alpha):
    """Четырёхлучевая искра."""
    if alpha <= 0.02 or r < 1:
        return
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = int(255 * alpha)
    pts = [(cx, cy - r), (cx + r * 0.22, cy - r * 0.22), (cx + r, cy), (cx + r * 0.22, cy + r * 0.22),
           (cx, cy + r), (cx - r * 0.22, cy + r * 0.22), (cx - r, cy), (cx - r * 0.22, cy - r * 0.22)]
    d.polygon(pts, fill=color + (a,))
    glow = layer.filter(ImageFilter.GaussianBlur(r * 0.35))
    img.alpha_composite(glow)
    img.alpha_composite(layer)
    d2 = ImageDraw.Draw(img)
    d2.ellipse((cx - r * 0.15, cy - r * 0.15, cx + r * 0.15, cy + r * 0.15), fill=WHITE + (a,))


def sparkles(img, t, seed, count, area, colors):
    rnd = random.Random(seed)
    for _ in range(count):
        x = rnd.uniform(area[0], area[2])
        y = rnd.uniform(area[1], area[3])
        r = rnd.uniform(9, 20)
        phase = rnd.random()
        k = max(0.0, math.sin(2 * math.pi * (t + phase)))
        sparkle(img, x, y, r * (0.4 + 0.6 * k), rnd.choice(colors), k)


# ---------- фигуры ----------

def diamond_points(cx, cy, w, h):
    top, mid, bottom = cy - h * 0.42, cy - h * 0.1, cy + h * 0.58
    return {
        "outline": [(cx - w * 0.28, top), (cx + w * 0.28, top), (cx + w / 2, mid), (cx, bottom), (cx - w / 2, mid)],
        "facets": [
            [(cx - w / 2, mid), (cx + w / 2, mid)],
            [(cx - w * 0.28, top), (cx - w * 0.12, mid), (cx, bottom)],
            [(cx + w * 0.28, top), (cx + w * 0.12, mid), (cx, bottom)],
            [(cx - w * 0.12, mid), (cx, top), (cx + w * 0.12, mid)],
        ],
        "top": top, "bottom": bottom,
    }


def draw_diamond(img, t, cx, cy, w, h, c1, c2):
    p = diamond_points(cx, cy, w, h)
    glow = 0.75 + 0.35 * wave(t)

    def outline(d, width, fill):
        d.line(p["outline"] + [p["outline"][0]], fill=fill, width=width, joint="curve")

    def facets(d, width, fill):
        for line in p["facets"]:
            d.line(line, fill=fill, width=width, joint="curve")

    # слабая заливка внутри, чтобы алмаз «светился» изнутри
    fill = Image.new("L", (S, S), 0)
    ImageDraw.Draw(fill).polygon(p["outline"], fill=int(70 + 40 * wave(t)))
    fill = fill.filter(ImageFilter.GaussianBlur(6))
    img.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (S, S), c1).split(), fill)))

    # блик: полоса бежит по алмазу
    band = Image.new("L", (S, S), 0)
    x0 = -200 + (t * 1.6 % 1.6) * 700
    ImageDraw.Draw(band).polygon([(x0, 0), (x0 + 60, 0), (x0 - 200, S), (x0 - 260, S)], fill=200)
    band = band.filter(ImageFilter.GaussianBlur(14))
    shape = Image.new("L", (S, S), 0)
    ImageDraw.Draw(shape).polygon(p["outline"], fill=255)
    band = ImageChops.multiply(band, shape)
    img.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (S, S), WHITE).split(), band)))

    img.alpha_composite(tube(facets, c2, 5, glow * 0.8))
    img.alpha_composite(tube(outline, c1, 9, glow))


def crown_points(cx, cy, w, h):
    l, r = cx - w / 2, cx + w / 2
    top, base = cy - h / 2, cy + h / 2
    return [(l, base), (l - w * 0.04, top + h * 0.1), (cx - w * 0.25, cy), (cx, top - h * 0.05),
            (cx + w * 0.25, cy), (r + w * 0.04, top + h * 0.1), (r, base)]


def draw_crown(img, t, cx, cy, w, h):
    pts = crown_points(cx, cy, w, h)
    glow = 0.75 + 0.35 * wave(t)

    def outline(d, width, fill):
        d.line(pts + [pts[0]], fill=fill, width=width, joint="curve")

    def band(d, width, fill):
        d.line([(cx - w / 2, cy + h * 0.32), (cx + w / 2, cy + h * 0.32)], fill=fill, width=width)

    fill = Image.new("L", (S, S), 0)
    ImageDraw.Draw(fill).polygon(pts, fill=int(60 + 40 * wave(t)))
    img.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (S, S), GOLD).split(), fill.filter(ImageFilter.GaussianBlur(6)))))
    img.alpha_composite(tube(band, PINK, 5, glow * 0.8))
    img.alpha_composite(tube(outline, GOLD, 9, glow))
    # камни на зубцах мерцают по очереди
    for i, (x, y) in enumerate([pts[1], pts[3], pts[5]]):
        k = wave(t, i / 3)
        sparkle(img, x, y - 4, 10 + 8 * k, [VIOLET, BLUE, PINK][i], 0.6 + 0.4 * k)


def heart_poly(cx, cy, r):
    pts = []
    for i in range(160):
        a = 2 * math.pi * i / 160
        x = 16 * math.sin(a) ** 3
        y = 13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a)
        pts.append((cx + x * r / 16, cy - y * r / 16))
    return pts


def draw_heart(img, cx, cy, r, color, glow, width=9):
    pts = heart_poly(cx, cy, r)

    def outline(d, w, fill):
        d.line(pts + [pts[0]], fill=fill, width=w, joint="curve")

    fill = Image.new("L", (S, S), 0)
    ImageDraw.Draw(fill).polygon(pts, fill=int(70 * glow))
    img.alpha_composite(Image.merge("RGBA", (*Image.new("RGB", (S, S), color).split(), fill.filter(ImageFilter.GaussianBlur(6)))))
    img.alpha_composite(tube(outline, color, width, glow))


# ---------- стикеры ----------

def frame_vip_girls(t):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bob = 8 * math.sin(2 * math.pi * t)
    sparkles(img, t, 1, 7, (40, 30, 470, 260), [PINK, BLUE, WHITE, VIOLET])
    draw_diamond(img, t, 256, 150 + bob, 270, 220, VIOLET, PINK)
    img.alpha_composite(neon_text("VIP", 110, 300, PINK, 0.8 + 0.3 * wave(t, 0.25)))
    img.alpha_composite(neon_text("девушкам бесплатно", 36, 440, GOLD, 0.7))
    return img


def frame_vip_7days(t):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    bob = 6 * math.sin(2 * math.pi * t)
    sparkles(img, t, 2, 6, (40, 20, 470, 220), [GOLD, BLUE, PINK])
    draw_crown(img, t, 256, 120 + bob, 250, 130)
    img.alpha_composite(neon_text("VIP", 96, 210, VIOLET, 0.8 + 0.3 * wave(t, 0.25)))
    img.alpha_composite(neon_text("на 7 дней", 58, 330, GOLD, 0.75 + 0.25 * wave(t, 0.5)))
    img.alpha_composite(neon_text("за 3 подруги", 38, 420, BLUE, 0.7))
    return img


def frame_match(t):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    # маленькие сердечки всплывают по кругу
    rnd = random.Random(5)
    for i in range(6):
        x = rnd.uniform(70, 440)
        phase = (t + i / 6) % 1
        y = 330 - phase * 300
        a = math.sin(math.pi * phase)
        if a > 0.05:
            layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
            ImageDraw.Draw(layer).polygon(heart_poly(x, y, 14), fill=[PINK, VIOLET, BLUE][i % 3] + (int(200 * a),))
            img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(1.5)))
    # два сердца бьются по очереди: тук-тук
    def beat(shift):
        x = (t + shift) % 1
        return 1 + 0.09 * math.exp(-((x - 0.1) / 0.06) ** 2) + 0.06 * math.exp(-((x - 0.3) / 0.06) ** 2)
    draw_heart(img, 200, 185, 105 * beat(0), VIOLET, 0.9 * beat(0))
    draw_heart(img, 312, 200, 105 * beat(0.5), PINK, 0.9 * beat(0.5))
    img.alpha_composite(neon_text("ВЗАИМНЫЙ", 62, 345, VIOLET, 0.8 + 0.3 * wave(t)))
    img.alpha_composite(neon_text("ВАЙБ", 62, 420, PINK, 0.8 + 0.3 * wave(t, 0.5)))
    return img


def encode(name, make_frame):
    tmp = Path(tempfile.mkdtemp())
    try:
        frames = [make_frame(i / N) for i in range(N)]
        for i, f in enumerate(frames):
            f.save(tmp / f"f{i:03d}.png")
        frames[N // 4].save(DIR / f"{name}.webp", "WEBP", lossless=True)
        out = DIR / f"{name}.webm"
        for crf in (30, 36, 42, 48, 54):
            subprocess.run([
                "ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "f%03d.png"),
                "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-b:v", "0", "-crf", str(crf),
                "-an", "-t", "3", "-auto-alt-ref", "0", "-row-mt", "1", str(out),
            ], check=True)
            if out.stat().st_size <= MAX_BYTES:
                break
        print(f"ok {name}.webm {out.stat().st_size // 1024} КБ")
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    encode("sticker_2_vip_girls", frame_vip_girls)
    encode("sticker_3_vip_7days", frame_vip_7days)
    encode("sticker_5_match", frame_match)
