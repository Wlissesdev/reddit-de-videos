"""Text-to-Speech alemão gratuito via Google TTS (gTTS)."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from gtts import gTTS


@dataclass
class TTSResult:
    audio_path: Path
    duration: float
    srt_path: Path | None = None


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?…])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _format_srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3_600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _write_srt(entries: list[tuple[float, float, str]], path: Path) -> None:
    lines: list[str] = []
    for i, (start, end, text) in enumerate(entries, 1):
        lines.append(str(i))
        lines.append(f"{_format_srt_time(start)} --> {_format_srt_time(end)}")
        lines.append(text)
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _probe_duration(audio_path: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(audio_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return float(result.stdout.strip())


def _tts_to_file(text: str, output_path: Path, lang: str = "de") -> float:
    gTTS(text=text, lang=lang).save(str(output_path))
    return _probe_duration(output_path)


def _concat_audio(parts: list[Path], output: Path) -> None:
    if len(parts) == 1:
        parts[0].replace(output)
        return

    list_file = output.with_suffix(".txt")
    list_file.write_text("\n".join(f"file '{p.resolve().as_posix()}'" for p in parts), encoding="utf-8")
    result = subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(list_file), "-c", "copy", str(output)],
        capture_output=True,
        text=True,
    )
    list_file.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "Falha ao concatenar áudio")


def generate_title_tts(text: str, voice: str, audio_path: Path) -> TTSResult:
    del voice  # gTTS não usa voz por nome; lang vem do config separado se quiser expandir
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    duration = _tts_to_file(text, audio_path, lang="de")
    return TTSResult(audio_path=audio_path, duration=duration)


def generate_story_tts(text: str, voice: str, audio_path: Path, srt_path: Path) -> TTSResult:
    del voice
    audio_path.parent.mkdir(parents=True, exist_ok=True)
    sentences = _split_sentences(text)
    if not sentences:
        raise ValueError("História vazia")

    work_dir = audio_path.parent
    parts: list[Path] = []
    srt_entries: list[tuple[float, float, str]] = []
    cursor = 0.0

    for i, sentence in enumerate(sentences):
        part_path = work_dir / f"part_{i:03d}.mp3"
        duration = _tts_to_file(sentence, part_path, lang="de")
        parts.append(part_path)
        srt_entries.append((cursor, cursor + duration, sentence))
        cursor += duration + 0.12

    _concat_audio(parts, audio_path)
    _write_srt(srt_entries, srt_path)

    for part in parts:
        part.unlink(missing_ok=True)

    return TTSResult(audio_path=audio_path, duration=_probe_duration(audio_path), srt_path=srt_path)
