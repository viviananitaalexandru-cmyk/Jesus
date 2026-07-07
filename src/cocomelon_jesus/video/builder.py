"""Assemble a finished nursery-rhyme video from a :class:`Song`.

Pipeline
--------
1. Work out how long each lyric line lasts.
2. Synthesise a procedural backing melody (NumPy) and optional TTS vocals.
3. Mix them into a single WAV soundtrack.
4. Render frames on the fly with :class:`SceneRenderer` (bouncing character +
   karaoke lyrics) and mux everything together with MoviePy/ffmpeg.
"""

from __future__ import annotations

import tempfile
import wave
from bisect import bisect_right
from pathlib import Path

import numpy as np

from ..audio.melody import build_song_melody
from ..audio.vocals import synthesize_vocals
from ..config import OUTPUT_DIR, RenderSettings
from ..models import Song
from ..visuals.scene import SceneRenderer


class VideoBuilder:
    def __init__(self, song: Song, settings: RenderSettings | None = None):
        self.song = song
        self.settings = settings or RenderSettings()

    # --- timing ------------------------------------------------------------
    def line_durations(self) -> list[float]:
        default = self.settings.seconds_per_line
        return [
            (ln.duration if ln.duration and ln.duration > 0 else default)
            for ln in self.song.lyrics
        ]

    def _line_starts(self, durations: list[float]) -> list[float]:
        starts, acc = [], 0.0
        for d in durations:
            starts.append(acc)
            acc += d
        return starts

    # --- audio -------------------------------------------------------------
    def _build_soundtrack(self, durations: list[float], tmp: Path) -> np.ndarray:
        sr = self.settings.sample_rate
        line_notes = [ln.notes for ln in self.song.lyrics]
        melody = build_song_melody(line_notes, durations, sr)

        total_samples = int(round(sum(durations) * sr))
        vocals = np.zeros(total_samples, dtype=np.float32)

        starts = self._line_starts(durations)
        any_vocals = False
        for ln, start, dur in zip(self.song.lyrics, starts, durations):
            voc = synthesize_vocals(ln.text, tmp, sr, self.settings.voice)
            if voc is None:
                continue
            any_vocals = True
            begin = int(round(start * sr))
            allowed = int(round(dur * sr))
            seg = voc[:allowed]
            end = min(begin + seg.size, total_samples)
            vocals[begin:end] += seg[: end - begin]

        track = np.zeros(total_samples, dtype=np.float32)
        m = min(len(melody), total_samples)
        if any_vocals:
            # Duck the melody so the vocals sit clearly on top.
            track[:m] += melody[:m] * 0.22
            track += vocals * 1.0
        else:
            # No TTS available: let the melody carry the tune.
            track[:m] += melody[:m] * 0.85

        peak = float(np.max(np.abs(track))) if track.size else 0.0
        if peak > 1.0:
            track /= peak
        return track

    @staticmethod
    def _write_wav(samples: np.ndarray, path: Path, sample_rate: int) -> None:
        data = np.clip(samples, -1.0, 1.0)
        pcm = (data * 32767.0).astype("<i2")
        with wave.open(str(path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm.tobytes())

    # --- render ------------------------------------------------------------
    def render(self, output_path: str | Path | None = None) -> Path:
        from moviepy import AudioFileClip, VideoClip  # local import (heavy)

        s = self.settings
        durations = self.line_durations()
        total = float(sum(durations))
        starts = self._line_starts(durations)
        texts = [ln.text for ln in self.song.lyrics]

        renderer = SceneRenderer(self.song, s.width, s.height, self.song.bpm)

        def frame_function(t: float) -> np.ndarray:
            idx = bisect_right(starts, t) - 1
            idx = max(0, min(idx, len(texts) - 1))
            line_start = starts[idx]
            line_dur = durations[idx]
            progress = (t - line_start) / line_dur if line_dur > 0 else 1.0
            return renderer.render_frame(t, texts[idx], progress)

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        if output_path is None:
            output_path = OUTPUT_DIR / f"{self.song.slug}.mp4"
        output_path = Path(output_path)

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            track = self._build_soundtrack(durations, tmp)
            wav_path = tmp / "soundtrack.wav"
            self._write_wav(track, wav_path, s.sample_rate)

            video = VideoClip(frame_function=frame_function, duration=total)
            audio = AudioFileClip(str(wav_path))
            video = video.with_audio(audio)
            video.write_videofile(
                str(output_path),
                fps=s.fps,
                codec="libx264",
                audio_codec="aac",
                logger=None,
            )
            video.close()
            audio.close()

        return output_path


def render_song(song: Song, settings: RenderSettings | None = None,
                output_path: str | Path | None = None) -> Path:
    """Convenience wrapper: render ``song`` and return the output path."""
    return VideoBuilder(song, settings).render(output_path)
