"""Cocomelon-style AI video generator for Christian songs about Jesus.

This package turns a small JSON "song definition" (lyrics, tempo, colours and
a character) into a colourful, karaoke-style nursery-rhyme video using only
open/local tooling (Pillow for visuals, NumPy for a procedural melody and
ffmpeg/MoviePy for assembly). Optional online/offline text-to-speech engines
add sung vocals when available.
"""

from .models import Song, LyricLine

__all__ = ["Song", "LyricLine", "__version__"]

__version__ = "0.1.0"
