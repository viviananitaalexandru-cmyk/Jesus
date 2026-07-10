#!/usr/bin/env python3
"""Animated Cocomelon-style video: Jesus heals the blind man."""

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
OUT = Path("/opt/cursor/artifacts")
WORK = ROOT / "work"
AUDIO = WORK / "audio"
CLIPS = WORK / "clips"

TITLE = ASSETS / "jesus-stories-title.png"
BLIND_ROAD = ASSETS / "blind-man-road.png"
JESUS_MEETS = ASSETS / "jesus-meets-blind-man.png"
HEALING = ASSETS / "healing-moment.png"
CAN_SEE = ASSETS / "blind-man-can-see.png"
CELEBRATE = ASSETS / "jesus-with-children.png"

SAMPLE_RATE = 44100
WIDTH, HEIGHT = 1920, 1080
FPS = 24
VOICE = "en-US-AnaNeural"

# C-major frequencies (Wheels on the Bus / Jesus Loves Me feel)
NOTE = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
    "G4": 392.00, "A4": 440.00, "B4": 493.88, "C5": 523.25,
    "G3": 196.00,
}

@dataclass
class Phrase:
    text: str
    label: str | None
    image: Path
    notes: list[str]
    motion: str  # zoom_in | pan_right | pan_left | pulse | bounce | gentle


PHRASES: list[Phrase] = [
    Phrase("Now He Can See!", None, TITLE, ["C5", "G4", "E4", "C5"], "gentle"),
    Phrase("There was a man who could not see,", "VERSE 1", BLIND_ROAD,
           ["C4", "C4", "C4", "G4", "C4", "C4", "C4", "E4"], "gentle"),
    Phrase("Could not see, could not see!", None, BLIND_ROAD,
           ["F4", "F4", "E4", "E4", "D4", "D4", "C4"], "zoom_in"),
    Phrase("He sat by the road so patiently,", None, BLIND_ROAD,
           ["C4", "C4", "D4", "E4", "F4", "G4", "G4", "E4"], "pan_right"),
    Phrase("Waiting, waiting patiently.", None, BLIND_ROAD,
           ["E4", "E4", "D4", "D4", "C4", "C4", "G3"], "gentle"),
    Phrase("Jesus walked along the way,", "VERSE 2", JESUS_MEETS,
           ["C4", "C4", "C4", "G4", "A4", "A4", "G4"], "pan_right"),
    Phrase("Along the way, along the way!", None, JESUS_MEETS,
           ["G4", "G4", "E4", "E4", "D4", "D4", "C4"], "pan_right"),
    Phrase("He stopped and heard the blind man say,", None, JESUS_MEETS,
           ["C4", "D4", "E4", "F4", "G4", "G4", "A4", "G4"], "zoom_in"),
    Phrase("Jesus, help me see today!", None, JESUS_MEETS,
           ["E4", "E4", "F4", "G4", "A4", "A4", "G4"], "pulse"),
    Phrase("Jesus smiled and said to him,", "VERSE 3", HEALING,
           ["C4", "C4", "D4", "E4", "F4", "G4", "G4"], "zoom_in"),
    Phrase("Said to him, said to him,", None, HEALING,
           ["E4", "E4", "D4", "D4", "C4", "C4"], "pulse"),
    Phrase("Your faith has made you well again!", None, HEALING,
           ["C4", "D4", "E4", "F4", "G4", "A4", "A4", "G4"], "pulse"),
    Phrase("And then — he could see!", None, CAN_SEE,
           ["E4", "F4", "G4", "C5", "C5"], "bounce"),
    Phrase("Now he can see, praise the Lord, he can see!", "CHORUS", CELEBRATE,
           ["C5", "C5", "A4", "G4", "F4", "E4", "D4", "C5", "C5"], "bounce"),
    Phrase("Now he can see, praise the Lord, he can see!", None, CELEBRATE,
           ["C5", "C5", "A4", "G4", "F4", "E4", "D4", "C5", "C5"], "bounce"),
    Phrase("Jump and spin, let the happy news ring —", None, CAN_SEE,
           ["E4", "F4", "G4", "A4", "G4", "F4", "E4", "D4"], "bounce"),
    Phrase("Jesus made the blind man see!", None, CELEBRATE,
           ["C4", "D4", "E4", "F4", "G4", "A4", "G4", "C5"], "bounce"),
    Phrase("Now he can see, praise the Lord, he can see!", "CHORUS", CELEBRATE,
           ["C5", "C5", "A4", "G4", "F4", "E4", "D4", "C5", "C5"], "bounce"),
    Phrase("Now he can see, praise the Lord, he can see!", None, CELEBRATE,
           ["C5", "C5", "A4", "G4", "F4", "E4", "D4", "C5", "C5"], "bounce"),
    Phrase("Jump and spin, let the happy news ring —", None, CAN_SEE,
           ["E4", "F4", "G4", "A4", "G4", "F4", "E4", "D4"], "bounce"),
    Phrase("Jesus made the blind man see!", None, CELEBRATE,
           ["C4", "D4", "E4", "F4", "G4", "A4", "G4", "C5"], "bounce"),
    Phrase("Jesus loves you!", None, TITLE, ["G4", "A4", "C5", "C5"], "gentle"),
    Phrase("Bye-bye, friends!", None, TITLE, ["C5", "A4", "G4", "C4"], "gentle"),
]


def load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
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


def render_slide(image: Path, phrase: Phrase) -> Path:
    base = fit_image(Image.open(image).convert("RGB")).convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(HEIGHT // 2, HEIGHT):
        alpha = int(165 * ((y - HEIGHT // 2) / (HEIGHT // 2)) ** 1.1)
        draw.line([(0, y), (WIDTH, y)], fill=(12, 30, 100, alpha))

    lines = []
    if phrase.label:
        lines.append(phrase.label)
    lines.append(phrase.text)

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

    out = WORK / "slides" / f"{hash(phrase.text) & 0xFFFF:04x}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.alpha_composite(base, overlay).convert("RGB").save(out, optimize=True)
    return out


def motion_filter(kind: str, frames: int) -> str:
    z = "1.0"
    if kind == "zoom_in":
        z = "min(zoom+0.0018,1.22)"
    elif kind == "pan_right":
        z = "1.12"
        return (
            f"zoompan=z='{z}':x='(iw-iw/zoom)*on/{frames}':y='(ih-ih/zoom)/2':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    elif kind == "pan_left":
        z = "1.12"
        return (
            f"zoompan=z='{z}':x='(iw-iw/zoom)*(1-on/{frames})':y='(ih-ih/zoom)/2':"
            f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
        )
    elif kind == "pulse":
        z = "1.08+0.04*sin(2*PI*on/18)"
    elif kind == "bounce":
        z = "1.1+0.06*sin(2*PI*on/12)"
    elif kind == "gentle":
        z = "min(zoom+0.0009,1.1)"
    return (
        f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"d={frames}:s={WIDTH}x{HEIGHT}:fps={FPS}"
    )


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
    dur = probe_duration(mp3)
    return mp3, dur


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
    # Slight emphasis on last note of each phrase
    note_lens[-1] *= 1.15
    scale = duration / sum(note_lens)
    note_lens = [l * scale for l in note_lens]

    offset = 0.0
    for name, nd in zip(notes, note_lens):
        chunk = note_wave(NOTE[name], nd)
        start = int(offset * SAMPLE_RATE)
        end = start + len(chunk)
        if end > len(buf):
            chunk = chunk[: len(buf) - start]
            end = len(buf)
        buf[start:end] += chunk
        offset += nd
    return buf


def mp3_to_pcm(path: Path) -> np.ndarray:
    wav = path.with_suffix(".wav")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(path), "-ar", str(SAMPLE_RATE), "-ac", "1", str(wav)
    ], check=True, capture_output=True)
    with wave.open(str(wav), "r") as wf:
        data = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32)
        data /= 32768.0
    return data


def animate_clip(idx: int, slide: Path, duration: float, motion: str) -> Path:
    frames = max(1, int(math.ceil(duration * FPS)))
    clip = CLIPS / f"clip_{idx:02d}.mp4"
    vf = motion_filter(motion, frames)
    subprocess.run([
        "ffmpeg", "-y", "-loop", "1", "-i", str(slide),
        "-vf", vf,
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(FPS),
        str(clip),
    ], check=True, capture_output=True)
    return clip


async def build_all() -> Path:
    WORK.mkdir(parents=True, exist_ok=True)
    AUDIO.mkdir(parents=True, exist_ok=True)
    CLIPS.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)

    print("Synthesizing phrase vocals...")
    timings = []
    vocal_parts = []
    music_parts = []
    clips = []

    for idx, phrase in enumerate(PHRASES):
        mp3, dur = await synth_phrase_audio(idx, phrase)
        pad = 0.18 if phrase.label else 0.12
        dur_total = dur + pad
        timings.append((phrase.text, dur_total))

        vocal = mp3_to_pcm(mp3)
        vlen = int(dur_total * SAMPLE_RATE)
        vp = np.zeros(vlen)
        vp[: len(vocal)] = vocal
        vocal_parts.append(vp)

        music = build_phrase_music(phrase.notes, dur_total)
        mlen = int(dur_total * SAMPLE_RATE)
        if len(music) < mlen:
            music = np.pad(music, (0, mlen - len(music)))
        else:
            music = music[:mlen]
        music_parts.append(music * 0.55)

        slide = render_slide(phrase.image, phrase)
        clip = animate_clip(idx, slide, dur_total, phrase.motion)
        clips.append(clip)
        print(f"  [{idx+1:02d}/{len(PHRASES)}] {dur_total:.1f}s  {phrase.text[:42]}")

    vocals = np.concatenate(vocal_parts)
    music = np.concatenate(music_parts)
    length = min(len(vocals), len(music))
    vocals, music = vocals[:length], music[:length]
    mixed = np.clip(vocals * 1.05 + music, -1, 1)

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
    meta = {"duration_sec": total, "phrases": timings}
    (OUT / "video-meta.json").write_text(json.dumps(meta, indent=2))
    print(f"\nDone: {final} ({total:.1f}s)")
    return final


def main() -> None:
    asyncio.run(build_all())


if __name__ == "__main__":
    main()
