"""Audio generation: procedural melody + optional TTS vocals."""

from .melody import build_song_melody, note_to_freq
from .vocals import synthesize_vocals

__all__ = ["build_song_melody", "note_to_freq", "synthesize_vocals"]
