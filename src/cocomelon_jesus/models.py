"""Data models describing a song and its scenes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class LyricLine:
    """A single karaoke line.

    ``notes`` is an optional list of note names (e.g. ``["C4", "E4", "G4"]``)
    used to shape the procedural melody for this line. When omitted a pleasant
    default phrase is used.
    """

    text: str
    duration: float | None = None
    notes: list[str] = field(default_factory=list)

    @classmethod
    def from_obj(cls, obj: Any) -> "LyricLine":
        if isinstance(obj, str):
            return cls(text=obj)
        return cls(
            text=str(obj["text"]),
            duration=obj.get("duration"),
            notes=list(obj.get("notes", [])),
        )


@dataclass
class Song:
    """A complete song definition loaded from JSON."""

    title: str
    lyrics: list[LyricLine]
    bpm: int = 100
    key: str = "C4"
    # Cocomelon-ish colour theme (hex strings).
    sky_top: str = "#8ED2FF"
    sky_bottom: str = "#E8F8FF"
    accent: str = "#FFC93C"
    character: str = "lamb"
    # Freeform prompts describing how an external AI image/music/video model
    # could render this song. Purely informational for the procedural renderer.
    video_prompt: str = ""
    music_prompt: str = ""

    @property
    def slug(self) -> str:
        return "".join(
            c if c.isalnum() else "_" for c in self.title.lower()
        ).strip("_")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Song":
        lyrics = [LyricLine.from_obj(item) for item in data.get("lyrics", [])]
        if not lyrics:
            raise ValueError(f"Song '{data.get('title')}' has no lyrics.")
        known = {
            "title",
            "lyrics",
            "bpm",
            "key",
            "sky_top",
            "sky_bottom",
            "accent",
            "character",
            "video_prompt",
            "music_prompt",
        }
        kwargs = {
            k: v for k, v in data.items() if k in known and k not in ("lyrics", "title")
        }
        return cls(title=data["title"], lyrics=lyrics, **kwargs)

    @classmethod
    def from_json(cls, path: str | Path) -> "Song":
        with open(path, "r", encoding="utf-8") as fh:
            return cls.from_dict(json.load(fh))

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "bpm": self.bpm,
            "key": self.key,
            "sky_top": self.sky_top,
            "sky_bottom": self.sky_bottom,
            "accent": self.accent,
            "character": self.character,
            "video_prompt": self.video_prompt,
            "music_prompt": self.music_prompt,
            "lyrics": [
                {"text": ln.text, "duration": ln.duration, "notes": ln.notes}
                for ln in self.lyrics
            ],
        }
