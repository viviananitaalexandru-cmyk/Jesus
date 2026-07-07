"""Project-wide paths and rendering defaults.

Everything is resolved relative to the repository root so the tool works the
same regardless of the current working directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

# repo_root/src/cocomelon_jesus/config.py  ->  repo_root
ROOT_DIR = Path(__file__).resolve().parents[2]

ASSETS_DIR = ROOT_DIR / "assets"
CHARACTERS_DIR = ASSETS_DIR / "characters"
SONGS_DIR = ASSETS_DIR / "songs"
FONTS_DIR = ASSETS_DIR / "fonts"
PROMPTS_DIR = ROOT_DIR / "prompts"
OUTPUT_DIR = ROOT_DIR / "output"


@dataclass(frozen=True)
class RenderSettings:
    """Tunable knobs for how a video is rendered."""

    width: int = 1280
    height: int = 720
    fps: int = 24
    sample_rate: int = 44100
    # Seconds each lyric line stays on screen when a song omits per-line timing.
    seconds_per_line: float = 3.0
    # Which vocal engine to use: "auto", "gtts", "pyttsx3" or "none".
    voice: str = "auto"


def ensure_dirs() -> None:
    """Create the working directories if they do not already exist."""
    for directory in (CHARACTERS_DIR, SONGS_DIR, FONTS_DIR, PROMPTS_DIR, OUTPUT_DIR):
        directory.mkdir(parents=True, exist_ok=True)
