"""Optional text-to-speech vocals.

Two "best available" open engines are supported and selected automatically:

* **gTTS** – Google's online TTS API. High quality, needs internet at runtime.
* **pyttsx3** – fully offline, but relies on the system ``espeak``/``espeak-ng``.

If neither is usable the generator gracefully falls back to an instrumental
track with on-screen karaoke lyrics (``synthesize_vocals`` returns ``None``).
"""

from __future__ import annotations

import shutil
import wave
from pathlib import Path

import numpy as np


def _read_wav_mono(path: Path, sample_rate: int) -> np.ndarray | None:
    """Read a WAV file as a mono float32 array, resampled to ``sample_rate``."""
    try:
        with wave.open(str(path), "rb") as wf:
            n_channels = wf.getnchannels()
            width = wf.getsampwidth()
            src_rate = wf.getframerate()
            raw = wf.readframes(wf.getnframes())
    except Exception:
        return None

    if width == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif width == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128) / 128.0
    else:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / (2**31)

    if n_channels > 1:
        data = data.reshape(-1, n_channels).mean(axis=1)

    if src_rate != sample_rate and data.size:
        # Simple linear resample – good enough for kids' vocals.
        target_len = int(round(data.size * sample_rate / src_rate))
        data = np.interp(
            np.linspace(0, data.size, target_len, endpoint=False),
            np.arange(data.size),
            data,
        ).astype(np.float32)
    return data


def _gtts_to_wav(text: str, out_mp3: Path, out_wav: Path) -> bool:
    try:
        from gtts import gTTS  # noqa: PLC0415
    except Exception:
        return False
    if shutil.which("ffmpeg") is None:
        return False
    try:
        gTTS(text=text, lang="en", slow=False).save(str(out_mp3))
    except Exception:
        return False
    # Convert mp3 -> wav with ffmpeg (already required by MoviePy).
    import subprocess  # noqa: PLC0415

    result = subprocess.run(
        ["ffmpeg", "-y", "-i", str(out_mp3), str(out_wav)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0 and out_wav.exists()


def _pyttsx3_to_wav(text: str, out_wav: Path) -> bool:
    if shutil.which("espeak") is None and shutil.which("espeak-ng") is None:
        return False
    try:
        import pyttsx3  # noqa: PLC0415

        engine = pyttsx3.init()
        engine.setProperty("rate", 150)
        engine.save_to_file(text, str(out_wav))
        engine.runAndWait()
    except Exception:
        return False
    return out_wav.exists()


def synthesize_vocals(
    text: str,
    tmp_dir: Path,
    sample_rate: int,
    engine: str = "auto",
) -> np.ndarray | None:
    """Render ``text`` to a mono float32 waveform, or ``None`` if unavailable.

    ``engine`` is one of ``"auto"``, ``"gtts"``, ``"pyttsx3"`` or ``"none"``.
    """
    if engine == "none" or not text.strip():
        return None

    tmp_dir.mkdir(parents=True, exist_ok=True)
    out_mp3 = tmp_dir / "vocals.mp3"
    out_wav = tmp_dir / "vocals.wav"

    order = ["gtts", "pyttsx3"] if engine == "auto" else [engine]
    for eng in order:
        ok = False
        if eng == "gtts":
            ok = _gtts_to_wav(text, out_mp3, out_wav)
        elif eng == "pyttsx3":
            ok = _pyttsx3_to_wav(text, out_wav)
        if ok:
            data = _read_wav_mono(out_wav, sample_rate)
            if data is not None and data.size:
                peak = float(np.max(np.abs(data)))
                if peak > 0:
                    data = data / peak * 0.9
                return data.astype(np.float32)
    return None
