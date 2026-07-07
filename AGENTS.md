# AGENTS.md

Cocomelon-style AI video generator for Christian songs about Jesus. A Python
CLI that turns JSON song definitions (`assets/songs/*.json`) into karaoke-style
`.mp4` videos using Pillow (visuals), NumPy (procedural melody) and
MoviePy/ffmpeg (assembly), with optional TTS vocals.

## Cursor Cloud specific instructions

- **Always work inside the virtualenv.** The project is developed in `/workspace/.venv`.
  Activate it first: `source .venv/bin/activate`. The update script recreates this
  venv and installs deps, so do not `pip install` into the system Python.
- **System deps already present in the base image:** `ffmpeg` (required for
  rendering) and `python3.12-venv` (required to create the venv). `espeak`/`espeak-ng`
  is **not** installed, so the offline `pyttsx3` voice is unavailable by default.
- **Vocals / `--voice`:** default `auto` uses `gTTS`, which needs outbound
  internet at render time. Use `--voice none` for a fully offline render
  (instrumental melody + on-screen karaoke). To enable the offline `pyttsx3`
  voice, `sudo apt-get install -y espeak-ng` first.
- **Run commands** (see `README.md` for the full list): `python -m cocomelon_jesus list`,
  `python -m cocomelon_jesus generate <song> [--voice none]`, `... generate --all`.
  After `pip install -e .` the console script `jesus-video` is equivalent.
- **Rendered videos** go to `output/` (git-ignored). Rendering ~6 lines takes
  roughly 9–11s each.
- **Tests:** `pytest` (in the venv). Tests cover song loading, melody math and
  frame/character rendering and intentionally do **not** invoke ffmpeg, so they
  run in a couple hundred ms.
- **Verifying visuals/audio without a GUI:** the automated `videoReview` model
  is unreliable for this content (it under-reports fast per-beat bounce motion
  and the TTS vocals). Prefer objective checks instead: extract frames with
  `ffmpeg -vf select=eq(n\,N)`, measure the lamb's white-pixel centroid across
  frames to confirm the vertical bounce, and render an audio waveform
  (`ffmpeg -filter_complex showwavespic`) / per-window RMS to confirm vocal bursts.
