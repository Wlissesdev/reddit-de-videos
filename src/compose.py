"""Montagem final do vídeo com FFmpeg."""

from __future__ import annotations

import subprocess
from pathlib import Path


def _run(cmd: list[str]) -> None:
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "FFmpeg falhou")


def _offset_srt(srt_path: Path, offset_seconds: float, output_path: Path) -> None:
    if offset_seconds <= 0:
        output_path.write_text(srt_path.read_text(encoding="utf-8"), encoding="utf-8")
        return

    lines = srt_path.read_text(encoding="utf-8").splitlines()
    out: list[str] = []

    def shift(ts: str) -> str:
        h, m, rest = ts.split(":")
        s, ms = rest.split(",")
        total = int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000 + offset_seconds
        nh = int(total // 3600)
        nm = int((total % 3600) // 60)
        ns = int(total % 60)
        nms = int(round((total - int(total)) * 1000))
        return f"{nh:02d}:{nm:02d}:{ns:02d},{nms:03d}"

    for line in lines:
        if "-->" in line:
            start, end = line.split(" --> ")
            out.append(f"{shift(start.strip())} --> {shift(end.strip())}")
        else:
            out.append(line)

    output_path.write_text("\n".join(out), encoding="utf-8")


def compose_video(
    background_video: Path,
    bubble_png: Path,
    title_audio: Path,
    story_audio: Path,
    story_srt: Path,
    output_path: Path,
    *,
    title_duration: float,
    title_padding: float,
    bubble_fade_out: float,
    width: int,
    height: int,
    loop_video: bool,
    subtitle_font_size: int,
    subtitle_margin_bottom: int,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    work = output_path.parent

    title_end = title_duration + title_padding
    story_srt_offset = work / "story_offset.srt"
    _offset_srt(story_srt, title_end, story_srt_offset)

    merged_audio = work / "merged_audio.m4a"
    _run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(title_audio),
            "-i",
            str(story_audio),
            "-filter_complex",
            "[0:a][1:a]concat=n=2:v=0:a=1[aout]",
            "-map",
            "[aout]",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(merged_audio),
        ]
    )

    dur_probe = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(merged_audio),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    total_duration = float(dur_probe.stdout.strip())

    fade_start = max(0.0, title_end - bubble_fade_out)
    srt_escaped = story_srt_offset.resolve().as_posix().replace(":", "\\:").replace("'", "\\'")
    subtitle_style = (
        f"FontName=Arial,FontSize={subtitle_font_size},PrimaryColour=&H00FFFFFF,"
        f"OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=1,Alignment=2,MarginV={subtitle_margin_bottom}"
    )

    loop_flag = ["-stream_loop", "-1"] if loop_video else []
    filter_complex = (
        f"[0:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},setsar=1,fps=30,trim=duration={total_duration},setpts=PTS-STARTPTS[bg];"
        f"[1:v]format=rgba,fade=t=out:st={fade_start}:d={bubble_fade_out}:alpha=1[bubble];"
        f"[bg][bubble]overlay=(W-w)/2:(H-h)/4:enable='between(t,0,{title_end})'[v1];"
        f"[v1]subtitles='{srt_escaped}':force_style='{subtitle_style}'[vout]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        *loop_flag,
        "-i",
        str(background_video),
        "-loop",
        "1",
        "-i",
        str(bubble_png),
        "-i",
        str(merged_audio),
        "-filter_complex",
        filter_complex,
        "-map",
        "[vout]",
        "-map",
        "2:a",
        "-t",
        str(total_duration),
        "-c:v",
        "libx264",
        "-preset",
        "medium",
        "-crf",
        "20",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    _run(cmd)
    return output_path
