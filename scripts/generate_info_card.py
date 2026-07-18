#!/usr/bin/env python3
"""Generate Massimo's animated neofetch-style profile card."""

from __future__ import annotations

import html
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "assets" / "info-card.svg"
WIDTH, HEIGHT = 500, 438
PAD, TITLE_H = 20, 34
STATIC = bool(os.environ.get("STATIC"))

ROWS = [
    ("host", "massimo@github"),
    ("kv", "Role", "AI Developer · UX/UI Designer"),
    ("kv", "Team", "Co-founder @ FAM Vision"),
    ("kv", "Base", "Bologna · Italy"),
    ("kv", "Focus", "AI products & agentic workflows"),
    ("gap", ""),
    ("section", "Stack"),
    ("kv", "AI", "Python · LLMs · Agents · n8n"),
    ("kv", "Frontend", "Angular · React · TypeScript"),
    ("kv", "Backend", "Spring Boot · NestJS · Flask"),
    ("kv", "Cloud", "AWS · Docker · PostgreSQL · Redis"),
    ("gap", ""),
    ("section", "Working principles"),
    ("bullet", "Evidence-first AI systems"),
    ("bullet", "Design and engineering in one loop"),
    ("bullet", "Automation with measurable impact"),
]


def reveal(markup: str, index: int) -> str:
    if STATIC:
        return f"<g>{markup}</g>"
    delay = 0.14 + index * 0.065
    return (
        f'<g opacity="0" transform="translate(0,5)">{markup}'
        f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur=".38s" fill="freeze"/>'
        f'<animateTransform attributeName="transform" type="translate" from="0 5" to="0 0" begin="{delay:.2f}s" dur=".38s" fill="freeze"/>'
        f'</g>'
    )


def main() -> None:
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/></linearGradient></defs>
<rect x=".5" y=".5" width="499" height="437" rx="14" fill="url(#bg)" stroke="#30363d"/>
<line x1="0" y1="{TITLE_H}" x2="500" y2="{TITLE_H}" stroke="#30363d"/>
<circle cx="18" cy="17" r="5" fill="#ff5f56"/><circle cx="34" cy="17" r="5" fill="#ffbd2e"/><circle cx="50" cy="17" r="5" fill="#27c93f"/>
<text x="250" y="21" text-anchor="middle" fill="#7d8590" font-size="11">massimo@github: ~$ neofetch</text>''']

    y = TITLE_H + 31
    line_height = 22
    for index, row in enumerate(ROWS):
        kind, value = row[0], row[1]
        if kind == "gap":
            y += 10
            continue
        if kind == "host":
            markup = (
                f'<text x="{PAD}" y="{y}" font-size="14" font-weight="700">'
                f'<tspan fill="#3fb950">massimo</tspan><tspan fill="#7d8590">@</tspan><tspan fill="#22d3ee">github</tspan></text>'
                f'<line x1="148" y1="{y - 5}" x2="480" y2="{y - 5}" stroke="#30363d"/>'
            )
        elif kind == "section":
            safe = html.escape(value)
            markup = (
                f'<text x="{PAD}" y="{y}" fill="#58a6ff" font-size="12" font-weight="700">— {safe}</text>'
                f'<line x1="{PAD + 28 + len(value) * 8}" y1="{y - 4}" x2="480" y2="{y - 4}" stroke="#30363d"/>'
            )
        elif kind == "kv":
            key, text = value, row[2]
            markup = (
                f'<text x="{PAD}" y="{y}" fill="#ffa657" font-size="12" font-weight="700">{html.escape(key)}</text>'
                f'<text x="112" y="{y}" fill="#c9d1d9" font-size="12">{html.escape(text)}</text>'
            )
        else:
            markup = (
                f'<circle cx="{PAD + 3}" cy="{y - 4}" r="2.5" fill="#3fb950"/>'
                f'<text x="{PAD + 14}" y="{y}" fill="#c9d1d9" font-size="12">{html.escape(value)}</text>'
            )
        parts.append(reveal(markup, index))
        y += line_height

    parts.append("</svg>")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("".join(parts), encoding="utf-8")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
