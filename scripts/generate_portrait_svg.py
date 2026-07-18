#!/usr/bin/env python3
"""Convert the public GitHub avatar into an animated monochrome ASCII SVG."""

from __future__ import annotations

import html
import io
import os
import urllib.request
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps


USERNAME = os.environ.get("GH_PROFILE_USER", "Lemaxim23")
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "assets" / "portrait.svg"

COLS, ROWS = 64, 46
CELL_W, CELL_H = 5.4, 7.6
RAMP = "@%#*+=-:. "
STATIC = bool(os.environ.get("STATIC"))


def avatar_rows() -> list[str]:
    request = urllib.request.Request(
        f"https://github.com/{USERNAME}.png?size=512",
        headers={"User-Agent": "Lemaxim23-profile-readme/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        image = Image.open(io.BytesIO(response.read()))
    image = ImageOps.exif_transpose(image).convert("RGB")
    width, height = image.size
    image = image.crop((0, 0, int(width * 0.67), int(height * 0.68)))
    image = ImageOps.fit(image, (COLS, ROWS), method=Image.Resampling.LANCZOS, centering=(0.48, 0.34))
    image = ImageOps.autocontrast(ImageOps.grayscale(image), cutoff=1)
    image = ImageEnhance.Contrast(image).enhance(1.28)

    rows: list[str] = []
    pixels = image.load()
    for y in range(ROWS):
        chars = []
        for x in range(COLS):
            value = pixels[x, y] / 255
            index = min(len(RAMP) - 1, round(value * (len(RAMP) - 1)))
            chars.append(RAMP[index])
        rows.append("".join(chars).rstrip())
    return rows


FONT = {
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
}


def fallback_rows() -> list[str]:
    canvas = [[" " for _ in range(COLS)] for _ in range(ROWS)]
    word = "MASSIMO"
    word_width = len(word) * 5 + len(word) - 1
    start_x = (COLS - word_width) // 2
    start_y = (ROWS - 7) // 2
    for letter_index, letter in enumerate(word):
        for y, pattern in enumerate(FONT[letter]):
            for x, bit in enumerate(pattern):
                if bit == "1":
                    canvas[start_y + y][start_x + letter_index * 6 + x] = "#"
    return ["".join(row).rstrip() for row in canvas]


def main() -> None:
    try:
        rows = avatar_rows()
        command = "portrait"
    except Exception as error:
        print(f"warning: {error}; using the MASSIMO wordmark")
        rows = fallback_rows()
        command = "identity"

    pad, title_h, status_h = 18, 34, 34
    art_w, art_h = COLS * CELL_W, ROWS * CELL_H
    width = round(art_w + pad * 2)
    height = round(title_h + art_h + status_h + pad)
    art_top = title_h + 8

    clips: list[str] = []
    content: list[str] = []
    for index, line in enumerate(rows):
        row_y = art_top + index * CELL_H
        baseline = row_y + CELL_H * 0.78
        delay = index * 0.085
        if STATIC:
            clips.append(
                f'<clipPath id="row-{index}"><rect x="{pad}" y="{row_y:.1f}" width="{art_w}" height="{CELL_H}"/></clipPath>'
            )
        else:
            clips.append(
                f'<clipPath id="row-{index}"><rect x="{pad}" y="{row_y:.1f}" width="0" height="{CELL_H}">'
                f'<animate attributeName="width" from="0" to="{art_w}" begin="{delay:.3f}s" dur=".11s" fill="freeze"/>'
                f'</rect></clipPath>'
            )
        content.append(
            f'<text xml:space="preserve" x="{pad}" y="{baseline:.1f}" fill="#c9d1d9" font-size="{CELL_H * .86:.1f}" '
            f'textLength="{art_w}" lengthAdjust="spacing" clip-path="url(#row-{index})">{html.escape(line)}</text>'
        )

    status_y = title_h + art_h + 25
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/></linearGradient>{''.join(clips)}</defs>
<rect x=".5" y=".5" width="{width - 1}" height="{height - 1}" rx="14" fill="url(#bg)" stroke="#30363d"/>
<line x1="0" y1="{title_h}" x2="{width}" y2="{title_h}" stroke="#30363d"/>
<circle cx="18" cy="17" r="5" fill="#ff5f56"/><circle cx="34" cy="17" r="5" fill="#ffbd2e"/><circle cx="50" cy="17" r="5" fill="#27c93f"/>
<text x="{width / 2}" y="21" text-anchor="middle" fill="#7d8590" font-size="11">massimo@github · {command}</text>
{''.join(content)}
<line x1="0" y1="{title_h + art_h + 7}" x2="{width}" y2="{title_h + art_h + 7}" stroke="#30363d"/>
<text x="18" y="{status_y}" fill="#7d8590" font-size="11">massimo@github:~$ <tspan fill="#22d3ee">Massimo Rugolo</tspan></text>
<rect x="263" y="{status_y - 11}" width="7" height="13" fill="#22d3ee"><animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.51;1" dur="1s" repeatCount="indefinite"/></rect>
</svg>'''
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
