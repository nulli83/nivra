"""Antialiased rounded surfaces via Pillow (crisp on HiDPI)."""

from __future__ import annotations

import tkinter as tk
from functools import lru_cache

from PIL import Image, ImageDraw, ImageTk


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    c = color.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


@lru_cache(maxsize=256)
def _rounded_rgba(
    width: int,
    height: int,
    radius: int,
    fill: str,
    outline: str,
    bg: str,
    outline_width: int,
    scale: int,
) -> Image.Image:
    """Build a supersampled rounded rect composited onto bg (RGB)."""
    width = max(2, width)
    height = max(2, height)
    radius = max(1, min(radius, width // 2, height // 2))
    scale = max(2, scale)

    W, H, R = width * scale, height * scale, radius * scale
    ow = max(scale, outline_width * scale)

    base = Image.new("RGB", (W, H), _hex_to_rgb(bg))
    # Draw on RGBA overlay for cleaner edges, then composite
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rounded_rectangle(
        [ow // 2, ow // 2, W - 1 - ow // 2, H - 1 - ow // 2],
        radius=R,
        fill=_hex_to_rgb(fill) + (255,),
        outline=_hex_to_rgb(outline) + (255,),
        width=ow,
    )
    base = base.convert("RGBA")
    base = Image.alpha_composite(base, overlay)
    base = base.convert("RGB")
    return base.resize((width, height), Image.Resampling.LANCZOS)


def rounded_photo(
    master: tk.Misc,
    width: int,
    height: int,
    radius: int,
    fill: str,
    outline: str,
    bg: str,
    outline_width: int = 1,
    scale: int = 3,
) -> ImageTk.PhotoImage:
    img = _rounded_rgba(
        int(width),
        int(height),
        int(radius),
        fill,
        outline,
        bg,
        int(outline_width),
        int(scale),
    )
    return ImageTk.PhotoImage(img, master=master)
