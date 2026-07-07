"""Colourful gradient backgrounds with sun, clouds, hills and a cross."""

from __future__ import annotations

from PIL import Image, ImageDraw

from .palette import RGB, blend, hex_to_rgb


def render_background(width: int, height: int, sky_top: str, sky_bottom: str,
                     accent: str) -> Image.Image:
    top = hex_to_rgb(sky_top)
    bottom = hex_to_rgb(sky_bottom)
    accent_rgb = hex_to_rgb(accent)

    img = Image.new("RGB", (width, height), bottom)
    px = img.load()
    # Vertical sky gradient.
    for y in range(height):
        colour = blend(top, bottom, y / max(1, height - 1))
        for x in range(width):
            px[x, y] = colour

    d = ImageDraw.Draw(img, "RGBA")

    # Sun with soft glow.
    sun_x, sun_y, sun_r = width * 0.82, height * 0.2, height * 0.09
    for i in range(6, 0, -1):
        alpha = int(18 * i / 6)
        r = sun_r * (1 + i * 0.28)
        d.ellipse([sun_x - r, sun_y - r, sun_x + r, sun_y + r],
                  fill=(*accent_rgb, alpha))
    d.ellipse([sun_x - sun_r, sun_y - sun_r, sun_x + sun_r, sun_y + sun_r],
              fill=(*accent_rgb, 255))

    # Fluffy clouds.
    for cx, cy, s in [(width * 0.2, height * 0.18, 1.0),
                      (width * 0.55, height * 0.12, 0.7),
                      (width * 0.38, height * 0.3, 0.5)]:
        _cloud(d, cx, cy, height * 0.06 * s)

    # Rolling hills.
    hill_top: RGB = (150, 214, 120)
    hill_front: RGB = (110, 190, 95)
    d.ellipse([-width * 0.2, height * 0.7, width * 0.7, height * 1.5], fill=hill_top)
    d.ellipse([width * 0.4, height * 0.78, width * 1.3, height * 1.6], fill=hill_front)
    d.rectangle([0, int(height * 0.88), width, height], fill=hill_front)

    # A simple cross on the hill (subtle, Christian theme).
    cx = width * 0.5
    base_y = height * 0.86
    beam = max(4, int(width * 0.012))
    wood = (140, 100, 60, 235)
    d.rectangle([cx - beam / 2, base_y - height * 0.22, cx + beam / 2, base_y], fill=wood)
    d.rectangle([cx - width * 0.05, base_y - height * 0.17,
                 cx + width * 0.05, base_y - height * 0.17 + beam], fill=wood)

    return img


def _cloud(d: ImageDraw.ImageDraw, cx: float, cy: float, r: float) -> None:
    white = (255, 255, 255, 235)
    for dx, dy, s in [(-r, 0, 1.0), (0, -r * 0.4, 1.3), (r, 0, 1.0), (0, r * 0.2, 1.1)]:
        d.ellipse([cx + dx - r * s, cy + dy - r * s, cx + dx + r * s, cy + dy + r * s],
                  fill=white)
