#!/usr/bin/env python3
"""Gera lote de vídeos Reddit Story em alemão."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from bubble import render_bubble
from compose import compose_video
from tts import generate_story_tts, generate_title_tts


def load_config(path: Path) -> dict:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_stories(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("stories.json deve ser uma lista de histórias")
    return data


def process_story(
    index: int,
    story: dict,
    *,
    background_video: Path,
    output_dir: Path,
    config: dict,
) -> Path:
    work = output_dir / f"story_{index:02d}"
    work.mkdir(parents=True, exist_ok=True)

    title = story["title"].strip()
    body = story["body"].strip()
    bubble_cfg = config["bubble"]
    subreddit = story.get("subreddit", bubble_cfg["subreddit"])
    username = story.get("username", bubble_cfg["username"])

    print(f"[{index:02d}] Gerando balão Reddit...")
    bubble_png = render_bubble(
        title,
        work / "bubble.png",
        subreddit=subreddit,
        username=username,
        upvotes=bubble_cfg["upvotes"],
        comments=bubble_cfg["comments"],
    )

    voice = config["voice"]
    print(f"[{index:02d}] Gerando narração do título...")
    title_tts = generate_title_tts(title, voice, work / "title.mp3")

    print(f"[{index:02d}] Gerando narração da história + legendas...")
    story_tts = generate_story_tts(body, voice, work / "story.mp3", work / "story.srt")

    final_path = output_dir / f"video_{index:02d}.mp4"
    print(f"[{index:02d}] Montando vídeo final...")
    compose_video(
        background_video,
        bubble_png,
        title_tts.audio_path,
        story_tts.audio_path,
        story_tts.srt_path,
        final_path,
        title_duration=title_tts.duration,
        title_padding=float(bubble_cfg["duration_padding"]),
        bubble_fade_out=float(bubble_cfg["fade_out"]),
        width=int(config["width"]),
        height=int(config["height"]),
        loop_video=bool(config["video"]["loop"]),
        subtitle_font_size=int(config["subtitles"]["font_size"]),
        subtitle_margin_bottom=int(config["subtitles"]["margin_bottom"]),
    )
    print(f"[{index:02d}] Pronto: {final_path}")
    return final_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Automatiza vídeos Reddit Story em alemão")
    parser.add_argument("--video", type=Path, default=ROOT / "input" / "video.mp4", help="Vídeo de fundo")
    parser.add_argument("--stories", type=Path, default=ROOT / "input" / "stories.json", help="JSON com histórias")
    parser.add_argument("--config", type=Path, default=ROOT / "config.yaml", help="Configurações")
    parser.add_argument("--output", type=Path, default=ROOT / "output", help="Pasta de saída")
    parser.add_argument("--from", dest="from_index", type=int, default=1, help="Índice inicial (1-based)")
    parser.add_argument("--to", dest="to_index", type=int, default=0, help="Índice final (0 = todas)")
    args = parser.parse_args()

    if not args.video.exists():
        raise SystemExit(f"Vídeo não encontrado: {args.video}\nColoque seu vídeo em input/video.mp4")
    if not args.stories.exists():
        raise SystemExit(
            f"Arquivo de histórias não encontrado: {args.stories}\n"
            f"Copie input/stories.example.json para input/stories.json e edite."
        )

    config = load_config(args.config)
    stories = load_stories(args.stories)
    args.output.mkdir(parents=True, exist_ok=True)

    start = max(1, args.from_index)
    end = args.to_index if args.to_index > 0 else len(stories)
    end = min(end, len(stories))

    print(f"Processando histórias {start} a {end} de {len(stories)}...")
    for i in range(start, end + 1):
        process_story(i, stories[i - 1], background_video=args.video, output_dir=args.output, config=config)

    print("\nConcluído! Vídeos em:", args.output.resolve())


if __name__ == "__main__":
    main()
