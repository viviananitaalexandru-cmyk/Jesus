"""Command-line interface for the Cocomelon-style Jesus video generator.

Examples
--------
    jesus-video init                 # create folders (characters/songs/output)
    jesus-video list                 # list bundled songs
    jesus-video characters           # list available drawn characters
    jesus-video generate jesus_loves_me
    jesus-video generate --all --seconds-per-line 2.5
    jesus-video generate jesus_is_my_friend --voice none --duration-per-line 2
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import OUTPUT_DIR, RenderSettings, ensure_dirs
from .library import find_song, load_songs
from .models import Song
from .video.builder import render_song
from .visuals.characters import available_characters


def _build_settings(args: argparse.Namespace) -> RenderSettings:
    return RenderSettings(
        width=args.width,
        height=args.height,
        fps=args.fps,
        seconds_per_line=args.seconds_per_line,
        voice=args.voice,
    )


def _cmd_init(_: argparse.Namespace) -> int:
    ensure_dirs()
    print("Created project folders:")
    for label, path in [
        ("characters", "assets/characters"),
        ("songs", "assets/songs"),
        ("fonts", "assets/fonts"),
        ("prompts", "prompts"),
        ("output", "output"),
    ]:
        print(f"  - {label:11s} -> {path}")
    return 0


def _cmd_list(_: argparse.Namespace) -> int:
    songs = load_songs()
    if not songs:
        print("No songs found in assets/songs/. Run `jesus-video init` first.")
        return 1
    print(f"Available songs ({len(songs)}):\n")
    for song in songs:
        print(f"  {song.slug:22s} {song.title}  [{song.character}, {song.bpm} bpm]")
    return 0


def _cmd_characters(_: argparse.Namespace) -> int:
    print("Available characters: " + ", ".join(available_characters()))
    return 0


def _render(song: Song, args: argparse.Namespace) -> Path:
    settings = _build_settings(args)
    out = Path(args.output) if args.output else None
    print(f"Rendering '{song.title}' ({len(song.lyrics)} lines, voice={args.voice})...")
    path = render_song(song, settings, out)
    print(f"  -> {path}")
    return path


def _cmd_generate(args: argparse.Namespace) -> int:
    if args.all:
        songs = load_songs()
        if not songs:
            print("No songs found. Run `jesus-video init` first.")
            return 1
        for song in songs:
            _render(song, args)
        print(f"\nDone. Videos are in {OUTPUT_DIR}")
        return 0

    if not args.song:
        print("error: provide a song name or use --all", file=sys.stderr)
        return 2

    song = find_song(args.song)
    if song is None:
        print(f"error: song '{args.song}' not found. Try `jesus-video list`.",
              file=sys.stderr)
        return 1
    _render(song, args)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jesus-video",
        description="Generate Cocomelon-style videos for songs about Jesus.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init", help="create project folders").set_defaults(func=_cmd_init)
    sub.add_parser("list", help="list bundled songs").set_defaults(func=_cmd_list)
    sub.add_parser("characters", help="list drawable characters").set_defaults(
        func=_cmd_characters
    )

    gen = sub.add_parser("generate", help="render a video")
    gen.add_argument("song", nargs="?", help="song slug/title (omit with --all)")
    gen.add_argument("--all", action="store_true", help="render every bundled song")
    gen.add_argument("--output", help="explicit output .mp4 path")
    gen.add_argument("--width", type=int, default=1280)
    gen.add_argument("--height", type=int, default=720)
    gen.add_argument("--fps", type=int, default=24)
    gen.add_argument(
        "--seconds-per-line", "--duration-per-line", dest="seconds_per_line",
        type=float, default=3.0,
        help="seconds per lyric line when a song omits timing (default 3.0)",
    )
    gen.add_argument(
        "--voice", choices=["auto", "gtts", "pyttsx3", "none"], default="auto",
        help="text-to-speech engine for vocals (default auto)",
    )
    gen.set_defaults(func=_cmd_generate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
