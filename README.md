# Cocomelon-style Jesus Video Generator

Generate colourful, **Cocomelon-style nursery-rhyme videos** for Christian
songs about Jesus — entirely with open/local tools. From a small JSON song
definition (lyrics, tempo, colours and a character) the generator produces a
karaoke-style `.mp4` with:

- a bright animated background (sky gradient, sun, clouds, hills, a little cross),
- a cute character that **bounces to the beat** (lamb, dove or star),
- **karaoke lyrics** that highlight left-to-right,
- a **procedurally generated melody** (NumPy) plus optional **sung/spoken vocals**
  via text-to-speech.

No paid services are required. Visuals use [Pillow](https://python-pillow.org/),
audio uses NumPy, and everything is muxed with
[MoviePy](https://zulko.github.io/moviepy/) + `ffmpeg`. Optional vocals use
[`gTTS`](https://pypi.org/project/gTTS/) (online) or
[`pyttsx3`](https://pypi.org/project/pyttsx3/) (offline, needs `espeak`).

---

## Folder structure

```
.
├── assets/
│   ├── characters/     # (optional) custom PNG sprites; built-ins are drawn in code
│   ├── fonts/          # (optional) custom .ttf fonts
│   └── songs/          # song definitions (JSON)  <-- edit / add songs here
├── prompts/
│   └── jesus_songs.json  # example prompts for external AI image/video/music models
├── output/             # rendered .mp4 files land here
├── src/cocomelon_jesus/
│   ├── audio/          # procedural melody + TTS vocals
│   ├── visuals/        # backgrounds, characters, karaoke scene
│   ├── video/          # MoviePy assembly
│   ├── library.py      # load songs from assets/songs
│   ├── models.py       # Song / LyricLine data models
│   └── cli.py          # command-line interface
└── tests/
```

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .          # optional: enables the `jesus-video` command

# Create folders (already present in the repo) and list songs
python -m cocomelon_jesus init
python -m cocomelon_jesus list
python -m cocomelon_jesus characters

# Render a single song to output/jesus_loves_me.mp4
python -m cocomelon_jesus generate jesus_loves_me

# Render every bundled song
python -m cocomelon_jesus generate --all

# Faster/offline render (no online TTS, instrumental + karaoke text)
python -m cocomelon_jesus generate jesus_is_my_friend --voice none
```

If you ran `pip install -e .`, you can use the shorter `jesus-video ...` command
instead of `python -m cocomelon_jesus ...`.

## Vocals (text-to-speech)

`--voice` selects how lyrics are sung/spoken:

| value      | engine    | notes                                              |
|------------|-----------|----------------------------------------------------|
| `auto`     | best      | tries gTTS, then pyttsx3, else instrumental (default) |
| `gtts`     | gTTS      | high quality, **needs internet** at render time    |
| `pyttsx3`  | pyttsx3   | fully offline, needs system `espeak`/`espeak-ng`   |
| `none`     | —         | instrumental melody + on-screen karaoke only       |

## Add your own song

Create `assets/songs/my_song.json`:

```json
{
  "title": "My New Song",
  "bpm": 100,
  "sky_top": "#7FC8FF",
  "sky_bottom": "#EAF7FF",
  "accent": "#FFC93C",
  "character": "lamb",
  "lyrics": [
    { "text": "Jesus is the way,", "duration": 3.0, "notes": ["C4", "E4", "G4"] },
    { "text": "we sing and pray!", "duration": 3.0, "notes": ["G4", "E4", "C4"] }
  ]
}
```

`notes` (optional) shape the melody; `duration` (optional) sets how long each
line is shown/sung. Then run `python -m cocomelon_jesus generate my_song`.

## Extending with AI models

`prompts/jesus_songs.json` contains ready-to-use image/video/music prompts so
you can plug in "best available" AI models (text-to-image, text-to-video,
text-to-music) to replace the procedural visuals or melody while keeping the
same song structure.

## Running tests

```bash
pip install pytest
pytest
```
