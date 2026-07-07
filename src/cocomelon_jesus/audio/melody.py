"""A tiny procedural music engine.

We synthesise a cheerful, nursery-rhyme style backing track entirely with
NumPy so the project has **zero** reliance on external music APIs. Each lyric
line gets a short melodic phrase; notes are rendered as softened sine tones
with a light attack/decay envelope so they sound bell-like rather than harsh.
"""

from __future__ import annotations

import numpy as np

# Semitone offsets from C for each note name.
_NOTE_BASE = {
    "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3, "E": 4,
    "F": 5, "F#": 6, "GB": 6, "G": 7, "G#": 8, "AB": 8, "A": 9,
    "A#": 10, "BB": 10, "B": 11,
}

# A gentle, singable phrase used when a lyric line doesn't specify notes.
_DEFAULT_PHRASE = ["C4", "E4", "G4", "E4", "C4", "D4", "E4", "C4"]


def note_to_freq(note: str) -> float:
    """Convert a note name like ``"A4"`` or ``"F#3"`` to a frequency in Hz."""
    note = note.strip().upper()
    if not note:
        return 0.0
    # Split trailing octave digit.
    octave = 4
    name = note
    if note[-1].isdigit():
        octave = int(note[-1])
        name = note[:-1]
    semitone = _NOTE_BASE.get(name)
    if semitone is None:
        return 0.0
    midi = 12 * (octave + 1) + semitone  # MIDI note number
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def _tone(freq: float, duration: float, sample_rate: int, volume: float) -> np.ndarray:
    """Render a single softened tone (fundamental + quiet overtones)."""
    n = max(1, int(duration * sample_rate))
    t = np.linspace(0.0, duration, n, endpoint=False)
    if freq <= 0.0:
        return np.zeros(n, dtype=np.float32)
    wave = (
        1.00 * np.sin(2 * np.pi * freq * t)
        + 0.35 * np.sin(2 * np.pi * freq * 2 * t)
        + 0.15 * np.sin(2 * np.pi * freq * 3 * t)
    )
    # Percussive-ish envelope: quick attack, gentle exponential decay.
    attack = int(0.02 * sample_rate)
    env = np.ones(n, dtype=np.float32)
    if attack > 0 and attack < n:
        env[:attack] = np.linspace(0.0, 1.0, attack)
    env *= np.exp(-3.0 * t / max(duration, 1e-6))
    return (wave * env * volume).astype(np.float32)


def _phrase_for_line(notes: list[str], duration: float, sample_rate: int) -> np.ndarray:
    """Render one lyric line's melodic phrase to fill ``duration`` seconds."""
    phrase = notes or _DEFAULT_PHRASE
    per_note = duration / len(phrase)
    segments = [
        _tone(note_to_freq(n), per_note, sample_rate, volume=0.28) for n in phrase
    ]
    return np.concatenate(segments) if segments else np.zeros(0, dtype=np.float32)


def build_song_melody(
    line_notes: list[list[str]],
    line_durations: list[float],
    sample_rate: int = 44100,
) -> np.ndarray:
    """Build the full backing melody for a song.

    ``line_notes`` and ``line_durations`` are parallel lists (one entry per
    lyric line). Returns a mono float32 waveform in the range [-1, 1].
    """
    parts: list[np.ndarray] = []
    for notes, dur in zip(line_notes, line_durations):
        parts.append(_phrase_for_line(notes, dur, sample_rate))
    if not parts:
        return np.zeros(0, dtype=np.float32)
    melody = np.concatenate(parts)
    peak = float(np.max(np.abs(melody))) if melody.size else 0.0
    if peak > 0:
        melody = melody / peak * 0.7
    return melody.astype(np.float32)
