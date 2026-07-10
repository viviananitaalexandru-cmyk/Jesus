#!/usr/bin/env python3
"""Cocomelon-style video with character pose animation."""

import asyncio
import json
import math
import os
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import edge_tts
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path("/workspace")
ASSETS = ROOT / "assets"
KF_DIR = ASSETS / "keyframes"
OUT = Path("/opt/cursor/artifacts")
WORK = ROOT / "work"
AUDIO = WORK / "audio"
CLIPS = WORK / "clips"

SAMPLE_RATE = 44100
WIDTH, HEIGHT = 1920, 1080
FPS = 24
VOICE = "en-US-AnaNeural"

NOTE = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
    "G4": 392.00, "A4": 440.00, "B4": 493.88, "C5": 523.25,
    "G3": 196.00,
}


def keyframes(pattern: str) -> list[Path]:
    return sorted(KF_DIR.glob(pattern))


KEYFRAME_SETS = {
    "title": keyframes("title-*.png"),
    "blind_road": keyframes("blind-road-*.png"),
    "jesus_meets": keyframes("jesus-meets-*.png"),
    "healing": keyframes("healing-*.png"),
    "can_see": keyframes("can-see-*.png"),
    "celebrate": keyframes("celebrate-*.png"),
}


@dataclass
class Phrase:
    text: str
    label: str | None
    scene: str
    notes: list[str]
    bounce: int = 12
    cycles: float = 1.2


PHRASES: list[Phrase] = [
    Phrase("Now He Can See!", None, "title", ["C5", "G4", "E4", "C5"], 10, 1.0),
    Phrase("There was a man who could not see,", "VERSE 1", "blind_road",
           ["C4", "C4", "C4", "G4", "C4", "C4", "C4", "E4"], 8, 0.9),
    Phrase("Could not see, could not see!", None, "blind_road",
           ["F4", "F4", "E4", "E4", "D4", "D4", "C4"], 10, 1.1),
    Phrase("He sat by the road so patiently,", None, "blind_road",
           ["C4", "C4", "D4", "E4", "F4", "G4", "G4", "E4"], 8, 0.8),
    Phrase("Waiting, waiting patiently.", None, "blind_road",
           ["E4", "E4", "D4", "D4", "C4", "C4", "G3"], 6, 0.7),
    Phrase("Jesus walked along the way,", "VERSE 2", "jesus_meets",
           ["C4", "C4", "C4", "G4", "A4", "A4", "G4"], 12, 1.0),
    Phrase("Along the way, along the way!", None, "jesus_meets",
           ["G4", "G4", "E4", "E4", "D4", "D4", "C4"], 14, 1.3),
    Phrase("He stopped and heard the blind man say,", None, "jesus_meets",
           ["C4", "D4", "E4", "F4", "G4", "G4", "A4", "G4"], 10, 1.0),
    Phrase("Jesus, help me see today!", None, "jesus_meets",
           ["E4", "E4", "F4", "G4", "A4", "A4", "G4"], 12, 1.1),
    Phrase("Jesus smiled and said to him,", "VERSE 3", "healing",
           ["C4", "C4", "D4", "E4", "F4", "G4", "G4"], 8, 1.0),
    Phrase("Said to him, said to him,", None, "healing",
           ["E4", "E4", "D4", "D4", "C4", "C4"], 8, 1.0),
    Phrase("Your faith has made you well again!", None, "healing",
           ["C4", "D4", "E4", "F4", "G4", "A4", "A4", "G4"], 10, 1.1),
    Phrase("And then — he could see!", None, "can_see",
           ["E4", "F4", "G4", "C5", "C5"], 18, 1.4),
    Phrase("Now he can see, praise the Lord, he can see!", "CHORUS", "celebrate",
           ["C5", "C5", "A4", "G4", "F4", "E4", "D4", "C5", "C5"], 20, 2.0),
    Phrase("Now he can see, praise the Lord, he can see!", None, "celebrate",
           ["C5", "C5", "A4", "G4", "F4", "E4", "D4", "C5", "C5"], 20, 2.0),
    Phrase("Jump and spin, let the happy news ring —", None, "can_see",
           ["E4", "F4", "G4", "A4", "G4", "F4", "E4", "D4"], 18, 1.6),
    Phrase("Jesus made the blind man see!", None, "celebrate",
           ["C4", "D4", "E4", "F4", "G4", "A4", "G4", "C5"], 20, 1.8),
    Phrase("Now he can see, praise the Lord, he can see!", "CHORUS", "celebrate",
           ["C5", "C5", "A4", "G4", "F4", "E4", "D4", "C5", "C5"], 22, 2.0),
    Phrase("Now he can see, praise the Lord, he can see!", None, "celebrate",
           ["C5", "C5", "A4", "G4", "F4", "E4", "D4", "C5", "C5"], 22, 2.0),
    Phrase("Jump and spin, let the happy news ring —", None, "can_see",
           ["E4", "F4", "G4", "A4", "G4", "F4", "E4", "D4"], 18, 1.6),
    Phrase("Jesus made the blind man see!", None, "celebrate",
           ["C4", "D4", "E4", "F4", "G4", "A4", "G4", "C5"], 20, 1.8),
    Phrase("Jesus loves you!", None, "title", ["G4", "A4", "C5", "C5"], 10, 1.0),
    Phrase("Bye-bye, friends!", None, "title", ["C5", "A4", "G4", "C4"], 12, 1.2),
]


def load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def fit_image(img: Image.Image) -> Image.Image:
    w, h = img.size
    scale = max(WIDTH / w, HEIGHT / h)
    nw, nh = int(w * scale), int(h * scale)
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - WIDTH) // 2, (nh - HEIGHT) // 2
    return resized.crop((left, top, left + WIDTH, top + HEIGHT))


def load_keyframe_set(scene: str) -> list[Image.Image]:
    paths = KEYFRAME_SETS[scene]
    if not paths:
        raise FileNotFoundError(f"No keyframes for scene: {scene}")
    return [fit_image(Image.open(p).convert("RGB")) for p in paths]


def draw_lyrics(frame: Image.Image, phrase: Phrase) -> Image.Image:
    img = frame.convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(HEIGHT // 2, HEIGHT):
        alpha = int(165 * ((y - HEIGHT // 2) / (HEIGHT // 2)) ** 1.1)
        draw.line([(0, y), (WIDTH, y)], fill=(12, 30, 100, alpha))

    lines = ([phrase.label] if phrase.label else []) + [phrase.text]
    colors = ["#FFD700", "#FFE66D", "#FF6B9D", "#4ECDC4", "#C77DFF", "#FFFFFF"]
    y0 = HEIGHT - 230 if len(lines) == 1 else HEIGHT - 280
    for i, line in enumerate(lines):
        is_label = phrase.label and i == 0
        font = load_font(46 if is_label else 60)
        color = "#FFD700" if is_label else colors[i % len(colors)]
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (WIDTH - (bbox[2] - bbox[0])) // 2
        y = y0 + i * 86
        for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2)]:
            draw.text((x + dx, y + dy), line, font=font, fill="#14213d")
        draw.text((x, y), line, font=font, fill=color)
    return Image.alpha_composite(img, overlay).convert("RGB")


def apply_motion(frame: Image.Image, bounce: int, sway: int, scale: float) -> Image.Image:
    """Bounce and sway like Cocomelon character bob."""
    fill = frame.getpixel((WIDTH // 2, HEIGHT // 2))
    sw, sh = int(WIDTH * scale), int(HEIGHT * scale)
    scaled = frame.resize((sw, sh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (WIDTH, HEIGHT), fill)
    x = (WIDTH - sw) // 2 + sway
    y = (HEIGHT - sh) // 2 + bounce
    canvas.paste(scaled, (x, y))
    return canvas


def interpolate_pose(poses: list[Image.Image], t: float) -> Image.Image:
    """Blend between keyframe poses. t in [0, 1] across full pose cycle."""
    if len(poses) == 1:
        return poses[0]
    span = len(poses) - 1
    pos = t * span
    idx = min(int(pos), span - 1)
    blend = pos - idx
    return Image.blend(poses[idx], poses[idx + 1], blend)


def render_character_clip(idx: int, phrase: Phrase, duration: float) -> Path:
    poses = load_keyframe_set(phrase.scene)
    total_frames = max(1, int(duration * FPS))
    clip = CLIPS / f"clip_{idx:02d}.mp4"

    proc = subprocess.Popen([
        "ffmpeg", "-y", "-f", "rawvideo", "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}", "-pix_fmt", "rgb24", "-r", str(FPS),
        "-i", "-", "-an",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast",
        str(clip),
    ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    for i in range(total_frames):
        t = i / max(total_frames - 1, 1)
        pose_t = (t * phrase.cycles) % 1.0
        frame = interpolate_pose(poses, pose_t)

        # Cocomelon-style rhythmic head-bob (snappy up-down on beat)
        beat = math.sin(i * 0.42)
        bounce_y = int(phrase.bounce * (beat ** 3))
        sway_x = int((phrase.bounce * 0.25) * math.sin(i * 0.21))
        pulse = 1.0 + 0.018 * abs(beat)
        frame = apply_motion(frame, bounce_y, sway_x, pulse)
        frame = draw_lyrics(frame, phrase)
        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    if proc.wait() != 0:
        raise RuntimeError(f"ffmpeg failed for clip {idx}")
    return clip


def probe_duration(path: Path) -> float:
    out = subprocess.check_output([
        "ffprobe", "-v", "quiet", "-show_entries", "format=duration",
        "-of", "json", str(path),
    ])
    return float(json.loads(out)["format"]["duration"])


async def synth_phrase_audio(idx: int, phrase: Phrase) -> tuple[Path, float]:
    mp3 = AUDIO / f"phrase_{idx:02d}.mp3"
    communicate = edge_tts.Communicate(phrase.text, VOICE, rate="+2%", pitch="+2Hz")
    await communicate.save(str(mp3))
    return mp3, probe_duration(mp3)


def note_wave(freq: float, duration: float, volume: float = 0.18) -> np.ndarray:
    n = max(1, int(SAMPLE_RATE * duration))
    t = np.linspace(0, duration, n, endpoint=False)
    env = np.sin(np.pi * t / duration) ** 0.85
    tone = np.sin(2 * np.pi * freq * t) * env
    bell = 0.35 * np.sin(2 * np.pi * freq * 2 * t) * env
    return volume * (tone + bell)


def build_phrase_music(notes: list[str], duration: float) -> np.ndarray:
    n = int(SAMPLE_RATE * duration) + 1
    buf = np.zeros(n)
    note_lens = [duration / len(notes)] * len(notes)
    note_lens[-1] *= 1.15
    scale = duration / sum(note_lens)
    note_lens = [l * scale for l in note_lens]
    offset = 0.0
    for name, nd in zip(notes, note_lens):
        chunk = note_wave(NOTE[name], nd)
        start = int(offset * SAMPLE_RATE)
        end = min(start + len(chunk), len(buf))
        buf[start:end] += chunk[: end - start]
        offset += nd
    return buf


def mp3_to_pcm(path: Path) -> np.ndarray:
    wav = path.with_suffix(".wav")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(path), "-ar", str(SAMPLE_RATE), "-ac", "1", str(wav)
    ], check=True, capture_output=True)
    with wave.open(str(wav), "r") as wf:
        data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32)
        return data / 32768.0


async def build_all() -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    AUDIO.mkdir(parents=True, exist_ok=True)
    CLIPS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    print("Building character-animated clips...")
    vocal_parts, music_parts, clips = [], [], []

    for idx, phrase in enumerate(PHRASES):
        mp3, dur = await synth_phrase_audio(idx, phrase)
        pad = 0.18 if phrase.label else 0.12
        dur_total = dur + pad

        vocal = mp3_to_pcm(mp3)
        vlen = int(dur_total * SAMPLE_RATE)
        vp = np.zeros(vlen)
        vp[: len(vocal)] = vocal
        vocal_parts.append(vp)

        music = build_phrase_music(phrase.notes, dur_total)
        mlen = int(dur_total * SAMPLE_RATE)
        music_parts.append((music[:mlen] if len(music) >= mlen else np.pad(music, (0, mlen - len(music)))) * 0.55)

        clip = render_character_clip(idx, phrase, dur_total)
        clips.append(clip)
        print(f"  [{idx+1:02d}/{len(PHRASES)}] {dur_total:.1f}s  {phrase.scene:12s}  {phrase.text[:40]}")

    vocals = np.concatenate(vocal_parts)
    music = np.concatenate(music_parts)
    length = min(len(vocals), len(music))
    mixed = np.clip(vocals[:length] * 1.05 + music[:length], -1, 1)

    mixed_wav = AUDIO / "mixed.wav"
    pcm = (mixed * 32767 * 0.92).astype(np.int16)
    with wave.open(str(mixed_wav), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())

    concat = CLIPS / "concat.txt"
    with open(concat, "w") as f:
        for c in clips:
            f.write(f"file '{c}'\n")

    silent = CLIPS / "silent.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c", "copy", str(silent),
    ], check=True, capture_output=True)

    final = OUT / "now-he-can-see-animated.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(silent), "-i", str(mixed_wav),
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
        str(final),
    ], check=True, capture_output=True)

    total = length / SAMPLE_RATE
    print(f"\nDone: {final} ({total:.1f}s)")
    return final


def main() -> None:
    asyncio.run(build_all())


if __name__ == "__main__":
    main()
