"""Basic tests for song loading, audio and character rendering (no ffmpeg)."""

from __future__ import annotations

import numpy as np

from cocomelon_jesus.audio.melody import build_song_melody, note_to_freq
from cocomelon_jesus.library import find_song, load_songs
from cocomelon_jesus.models import Song
from cocomelon_jesus.visuals.characters import available_characters, render_character
from cocomelon_jesus.visuals.scene import SceneRenderer


def test_songs_load_and_are_valid():
    songs = load_songs()
    assert len(songs) >= 4
    for song in songs:
        assert song.title
        assert song.lyrics
        assert all(line.text for line in song.lyrics)


def test_find_song_by_slug_and_title():
    assert find_song("jesus_loves_me") is not None
    assert find_song("Jesus Loves Me") is not None
    assert find_song("does_not_exist") is None


def test_note_to_freq_a4():
    assert abs(note_to_freq("A4") - 440.0) < 1e-6
    assert note_to_freq("C4") < note_to_freq("C5")


def test_build_melody_shape_and_range():
    sr = 8000
    durations = [1.0, 0.5]
    melody = build_song_melody([["C4"], ["E4"]], durations, sr)
    assert melody.shape[0] == int(1.0 * sr) + int(0.5 * sr)
    assert float(np.max(np.abs(melody))) <= 1.0


def test_characters_render():
    assert "lamb" in available_characters()
    sprite = render_character("lamb", size=64)
    assert sprite.size == (64, 64)
    assert sprite.mode == "RGBA"


def test_scene_frame_shape():
    song = Song.from_dict(
        {"title": "T", "lyrics": ["hello world"], "sky_top": "#8ED2FF",
         "sky_bottom": "#E8F8FF", "accent": "#FFC93C", "character": "lamb"}
    )
    renderer = SceneRenderer(song, 320, 180, bpm=100)
    frame = renderer.render_frame(0.5, "hello world", 0.5)
    assert frame.shape == (180, 320, 3)
