"""Gera imagem do balão estilo Reddit com Pillow (sem browser)."""

from __future__ import annotations

import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _wrap_title(title: str, max_chars: int = 38) -> list[str]:
    return textwrap.wrap(title, width=max_chars) or [title]


def render_bubble(
    title: str,
    output_path: Path,
    *,
    subreddit: str = "r/Geschichten",
    username: str = "u/Anonym",
    upvotes: str = "2,4k",
    comments: str = "187",
    template_path: Path | None = None,
) -> Path:
    del template_path  # compatibilidade com assinatura antiga

    lines = _wrap_title(title)
    card_w = 860
    line_h = 46
    title_h = len(lines) * line_h + 10
    card_h = 80 + title_h + 90
    img = Image.new("RGBA", (card_w + 40, card_h + 40), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    x0, y0 = 20, 20
    x1, y1 = x0 + card_w, y0 + card_h
    draw.rounded_rectangle((x0, y0, x1, y1), radius=18, fill=(255, 255, 255, 255))

    avatar_r = 24
    ax, ay = x0 + 28 + avatar_r, y0 + 28 + avatar_r
    draw.ellipse((ax - avatar_r, ay - avatar_r, ax + avatar_r, ay + avatar_r), fill=(255, 69, 0, 255))
    draw.text((ax - 10, ay - 14), "r/", fill=(255, 255, 255, 255), font=_load_font(18, bold=True))

    sub_font = _load_font(22, bold=True)
    user_font = _load_font(18)
    draw.text((x0 + 88, y0 + 24), subreddit, fill=(26, 26, 27, 255), font=sub_font)
    draw.text((x0 + 88, y0 + 52), username, fill=(120, 124, 126, 255), font=user_font)

    badge = "STORY"
    badge_font = _load_font(14, bold=True)
    bw = draw.textlength(badge, font=badge_font) + 20
    bx1 = x1 - 28
    bx0 = bx1 - bw
    draw.rounded_rectangle((bx0, y0 + 28, bx1, y0 + 56), radius=12, fill=(0, 121, 211, 255))
    draw.text((bx0 + 10, y0 + 33), badge, fill=(255, 255, 255, 255), font=badge_font)

    title_font = _load_font(34, bold=True)
    ty = y0 + 96
    for line in lines:
        draw.text((x0 + 28, ty), line, fill=(26, 26, 27, 255), font=title_font)
        ty += line_h

    footer_y = y1 - 56
    draw.line((x0 + 20, footer_y, x1 - 20, footer_y), fill=(237, 239, 241, 255), width=2)
    foot_font = _load_font(20, bold=True)
    draw.text((x0 + 28, footer_y + 14), f"⬆ {upvotes}    💬 {comments}    ↗ Teilen", fill=(120, 124, 126, 255), font=foot_font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG")
    return output_path
