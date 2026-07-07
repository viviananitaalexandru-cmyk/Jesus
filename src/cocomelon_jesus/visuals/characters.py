"""Cute, procedurally drawn characters.

These are intentionally simple vector-style sprites drawn with Pillow so the
project needs no external art assets. Each character is drawn onto a
transparent RGBA layer and can be dropped onto a background at any position and
scale (used to make the character "bounce" to the beat).
"""

from __future__ import annotations

from PIL import Image, ImageDraw

RGBA = tuple[int, int, int, int]


def _circle(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, fill: RGBA,
            outline: RGBA | None = None, width: int = 0) -> None:
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=outline, width=width)


def _face(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float) -> None:
    """Draw two friendly eyes and a smile centred on (cx, cy)."""
    eye_dx = r * 0.38
    eye_y = cy - r * 0.12
    eye_r = max(2, r * 0.12)
    for sign in (-1, 1):
        _circle(draw, cx + sign * eye_dx, eye_y, eye_r, (40, 40, 60, 255))
        _circle(draw, cx + sign * eye_dx - eye_r * 0.3, eye_y - eye_r * 0.3,
                eye_r * 0.35, (255, 255, 255, 255))
    # Rosy cheeks.
    for sign in (-1, 1):
        _circle(draw, cx + sign * r * 0.55, cy + r * 0.12, r * 0.14, (255, 170, 170, 130))
    # Smile.
    mouth_r = r * 0.45
    draw.arc(
        [cx - mouth_r, cy - mouth_r * 0.2, cx + mouth_r, cy + mouth_r * 1.1],
        start=20, end=160, fill=(120, 60, 60, 255), width=max(2, int(r * 0.06)),
    )


def _draw_lamb(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2
    body_r = size * 0.34
    wool = (255, 255, 255, 255)
    # Fluffy wool body (cluster of circles).
    for ang in range(0, 360, 45):
        import math
        x = c + body_r * 0.6 * math.cos(math.radians(ang))
        y = c + body_r * 0.6 * math.sin(math.radians(ang))
        _circle(d, x, y, body_r * 0.42, wool, outline=(220, 220, 230, 255), width=2)
    _circle(d, c, c, body_r * 0.7, wool)
    # Face.
    face_r = size * 0.2
    _circle(d, c, c + size * 0.02, face_r, (60, 60, 75, 255))
    _circle(d, c, c + size * 0.02, face_r * 0.86, (245, 240, 240, 255))
    _face(d, c, c + size * 0.02, face_r * 0.86)
    # Ears.
    for sign in (-1, 1):
        d.ellipse(
            [c + sign * face_r - face_r * 0.5, c - face_r * 0.5,
             c + sign * face_r + face_r * 0.5, c + face_r * 0.1],
            fill=(60, 60, 75, 255),
        )
    return img


def _draw_star(size: int) -> Image.Image:
    import math
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2
    outer, inner = size * 0.42, size * 0.2
    points = []
    for i in range(10):
        r = outer if i % 2 == 0 else inner
        ang = math.radians(i * 36 - 90)
        points.append((c + r * math.cos(ang), c + r * math.sin(ang)))
    d.polygon(points, fill=(255, 213, 79, 255), outline=(240, 170, 40, 255))
    _face(d, c, c, size * 0.18)
    return img


def _draw_dove(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = size / 2
    body = (250, 250, 255, 255)
    # Body + head.
    d.ellipse([c - size * 0.3, c - size * 0.1, c + size * 0.25, c + size * 0.28],
              fill=body, outline=(210, 215, 235, 255), width=2)
    _circle(d, c + size * 0.2, c - size * 0.12, size * 0.13, body,
            outline=(210, 215, 235, 255), width=2)
    # Wing.
    d.pieslice([c - size * 0.25, c - size * 0.25, c + size * 0.2, c + size * 0.2],
               start=200, end=340, fill=(232, 236, 250, 255))
    # Beak + eye.
    d.polygon([(c + size * 0.32, c - size * 0.12), (c + size * 0.42, c - size * 0.09),
               (c + size * 0.32, c - size * 0.06)], fill=(255, 190, 70, 255))
    _circle(d, c + size * 0.24, c - size * 0.14, size * 0.02, (40, 40, 60, 255))
    return img


_CHARACTERS = {
    "lamb": _draw_lamb,
    "star": _draw_star,
    "dove": _draw_dove,
}


def available_characters() -> list[str]:
    return sorted(_CHARACTERS)


def render_character(name: str, size: int = 320) -> Image.Image:
    """Return an RGBA sprite for ``name`` (falls back to the lamb)."""
    draw_fn = _CHARACTERS.get(name.lower(), _draw_lamb)
    return draw_fn(size)
