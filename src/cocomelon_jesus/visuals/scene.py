"""Compose full video frames (background + bouncing character + karaoke text)."""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from ..models import Song
from .background import render_background
from .characters import render_character
from .palette import hex_to_rgb, load_font


class SceneRenderer:
    """Renders individual frames for a song at a given timestamp."""

    def __init__(self, song: Song, width: int, height: int, bpm: int):
        self.song = song
        self.width = width
        self.height = height
        self.bpm = max(40, bpm)

        # Pre-render the static background once (expensive pixel loop).
        self._background = render_background(
            width, height, song.sky_top, song.sky_bottom, song.accent
        )
        char_size = int(height * 0.42)
        self._character = render_character(song.character, char_size)
        self._char_size = char_size

        self._title_font = load_font(int(height * 0.075), bold=True)
        self._lyric_font = load_font(int(height * 0.06), bold=True)
        self._accent = hex_to_rgb(song.accent)

    def render_frame(self, t: float, line_text: str, line_progress: float) -> np.ndarray:
        """Render the frame at time ``t`` (seconds).

        ``line_text`` is the currently active lyric; ``line_progress`` in [0, 1]
        drives the karaoke word highlight.
        """
        frame = self._background.copy()
        d = ImageDraw.Draw(frame, "RGBA")

        # Character bounces vertically in time with the beat, with a gentle
        # "squash & stretch" scale pulse (whole sprite scales together so it
        # reads as a clear bounce rather than a wobble).
        beat_hz = self.bpm / 60.0
        bounce = abs(math.sin(math.pi * beat_hz * t))
        cx = self.width * 0.5
        base_y = self.height * 0.64
        cy = base_y - bounce * self.height * 0.13
        scale = 1.0 + 0.06 * bounce
        cs = max(1, int(self._char_size * scale))
        sprite = (
            self._character
            if cs == self._char_size
            else self._character.resize((cs, cs), Image.LANCZOS)
        )
        frame.paste(sprite, (int(cx - cs / 2), int(cy - cs / 2)), sprite)

        self._draw_title(d)
        if line_text:
            self._draw_karaoke(frame, d, line_text, line_progress)

        return np.asarray(frame)

    # --- helpers -----------------------------------------------------------
    def _draw_title(self, d: ImageDraw.ImageDraw) -> None:
        text = self.song.title
        bbox = d.textbbox((0, 0), text, font=self._title_font)
        w = bbox[2] - bbox[0]
        x = (self.width - w) / 2
        y = self.height * 0.05
        # Rounded banner behind the title.
        pad = self.height * 0.02
        d.rounded_rectangle(
            [x - pad, y - pad, x + w + pad, y + (bbox[3] - bbox[1]) + pad * 1.6],
            radius=int(self.height * 0.03), fill=(255, 255, 255, 210),
            outline=(*self._accent, 255), width=max(3, int(self.height * 0.006)),
        )
        self._outlined_text(d, (x, y), text, self._title_font,
                            fill=(60, 90, 160), outline=(255, 255, 255))

    def _draw_karaoke(self, frame: Image.Image, d: ImageDraw.ImageDraw,
                      text: str, progress: float) -> None:
        bbox = d.textbbox((0, 0), text, font=self._lyric_font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        x = (self.width - w) / 2
        y = self.height * 0.82
        pad = self.height * 0.022
        d.rounded_rectangle(
            [x - pad, y - pad, x + w + pad, y + h + pad * 1.6],
            radius=int(self.height * 0.03), fill=(30, 40, 90, 180),
        )
        # Base lyric text.
        self._outlined_text(d, (x, y), text, self._lyric_font,
                            fill=(255, 255, 255), outline=(20, 30, 70))
        # Karaoke highlight: reveal an accent-coloured copy left-to-right.
        reveal = int(max(0.0, min(1.0, progress)) * w)
        if reveal > 0:
            highlight = Image.new("RGBA", frame.size, (0, 0, 0, 0))
            hd = ImageDraw.Draw(highlight)
            self._outlined_text(hd, (x, y), text, self._lyric_font,
                                fill=(*self._accent, 255), outline=(120, 80, 20, 255))
            mask = Image.new("L", frame.size, 0)
            ImageDraw.Draw(mask).rectangle(
                [0, 0, int(x) + reveal, frame.height], fill=255
            )
            frame.paste(highlight, (0, 0), Image.composite(
                highlight.split()[3], Image.new("L", frame.size, 0), mask
            ))

    @staticmethod
    def _outlined_text(d: ImageDraw.ImageDraw, pos, text, font, fill, outline) -> None:
        x, y = pos
        for dx in (-2, 0, 2):
            for dy in (-2, 0, 2):
                if dx or dy:
                    d.text((x + dx, y + dy), text, font=font, fill=outline)
        d.text((x, y), text, font=font, fill=fill)
