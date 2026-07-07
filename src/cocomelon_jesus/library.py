"""Load bundled song definitions from ``assets/songs/*.json``."""

from __future__ import annotations

from pathlib import Path

from .config import SONGS_DIR
from .models import Song


def song_files(songs_dir: Path | None = None) -> list[Path]:
    directory = songs_dir or SONGS_DIR
    return sorted(directory.glob("*.json"))


def load_songs(songs_dir: Path | None = None) -> list[Song]:
    songs = []
    for path in song_files(songs_dir):
        try:
            songs.append(Song.from_json(path))
        except (ValueError, KeyError) as exc:  # skip malformed files
            print(f"  ! skipping {path.name}: {exc}")
    return songs


def find_song(name: str, songs_dir: Path | None = None) -> Song | None:
    """Find a song by slug, filename stem or (case-insensitive) title."""
    target = name.lower().strip()
    for path in song_files(songs_dir):
        if path.stem.lower() == target:
            return Song.from_json(path)
    for song in load_songs(songs_dir):
        if song.slug == target or song.title.lower() == target:
            return song
    return None
