#!/usr/bin/env python3
"""Render an animated terminal-style contribution heatmap from local JSON."""

from __future__ import annotations

import calendar
import datetime as dt
import html
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "contributions.json"
OUTPUT = ROOT / "assets" / "contributions.svg"

WIDTH, HEIGHT = 900, 224
LEFT, TOP = 70, 67
CELL, GAP = 11, 3
WEEKS = 53
COLORS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
STATIC = bool(os.environ.get("STATIC"))


def load_data() -> dict[str, object]:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {
        "total": 0,
        "active_days": 0,
        "current_streak": 0,
        "longest_streak": 0,
        "days": [],
    }


def levels(counts: list[int]) -> tuple[int, int, int]:
    active = sorted(count for count in counts if count > 0)
    if not active:
        return 1, 2, 3

    def percentile(fraction: float) -> int:
        return active[min(len(active) - 1, round((len(active) - 1) * fraction))]

    return percentile(0.25), percentile(0.50), percentile(0.75)


def level_for(count: int, thresholds: tuple[int, int, int]) -> int:
    if count <= 0:
        return 0
    if count <= thresholds[0]:
        return 1
    if count <= thresholds[1]:
        return 2
    if count <= thresholds[2]:
        return 3
    return 4


def main() -> None:
    data = load_data()
    by_date = {str(day["date"]): int(day["count"]) for day in data.get("days", [])}
    thresholds = levels(list(by_date.values()))

    today = dt.date.today()
    this_sunday = today - dt.timedelta(days=(today.weekday() + 1) % 7)
    start = this_sunday - dt.timedelta(weeks=WEEKS - 1)

    month_labels: list[str] = []
    last_month = None
    for week in range(WEEKS):
        date = start + dt.timedelta(weeks=week)
        if date.month != last_month:
            last_month = date.month
            x = LEFT + week * (CELL + GAP)
            month_labels.append(
                f'<text class="label" x="{x}" y="{TOP - 12}">{calendar.month_abbr[date.month]}</text>'
            )

    cells: list[str] = []
    for week in range(WEEKS):
        for row in range(7):
            date = start + dt.timedelta(days=week * 7 + row)
            if date > today:
                continue
            count = by_date.get(date.isoformat(), 0)
            level = level_for(count, thresholds)
            x = LEFT + week * (CELL + GAP)
            y = TOP + row * (CELL + GAP)
            delay = (week * 7 + row) / (WEEKS * 7) * 3.2
            title = html.escape(f"{date.isoformat()}: {count} contributions")
            cells.append(
                f'<rect class="cell level-{level}" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="2.5" style="animation-delay:{delay:.3f}s"><title>{title}</title></rect>'
            )

    total = int(data.get("total", 0))
    active = int(data.get("active_days", 0))
    current = int(data.get("current_streak", 0))
    longest = int(data.get("longest_streak", 0))
    summary = f"{total:,} contributions  ·  {active} active days  ·  {current} day streak  ·  best {longest} days"

    cell_animation = "opacity:1;" if STATIC else "transform-box:fill-box; transform-origin:center; opacity:0; animation:pop .5s cubic-bezier(.2,.8,.2,1) forwards;"
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
<style>
  .label {{ fill:#7d8590; font-size:11px; font-weight:600; }}
  .day {{ fill:#7d8590; font-size:10px; }}
  .summary {{ fill:#c9d1d9; font-size:13px; font-weight:600; }}
  .muted {{ fill:#7d8590; font-size:11px; }}
  .cell {{ {cell_animation} }}
  .level-0 {{ fill:{COLORS[0]}; }} .level-1 {{ fill:{COLORS[1]}; }}
  .level-2 {{ fill:{COLORS[2]}; }} .level-3 {{ fill:{COLORS[3]}; }} .level-4 {{ fill:{COLORS[4]}; }}
  @keyframes pop {{ 0% {{ opacity:0; transform:scale(.25); }} 70% {{ opacity:1; transform:scale(1.12); }} 100% {{ opacity:1; transform:scale(1); }} }}
  @media (prefers-reduced-motion: reduce) {{ .cell {{ opacity:1; animation:none; }} }}
</style>
<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#111722"/><stop offset="1" stop-color="#0d1117"/></linearGradient></defs>
<rect x="0.5" y="0.5" width="899" height="223" rx="14" fill="url(#bg)" stroke="#30363d"/>
<line x1="0" y1="35" x2="900" y2="35" stroke="#30363d"/>
<circle cx="19" cy="18" r="5" fill="#ff5f56"/><circle cx="35" cy="18" r="5" fill="#ffbd2e"/><circle cx="51" cy="18" r="5" fill="#27c93f"/>
<text x="450" y="22" text-anchor="middle" fill="#7d8590" font-size="12">massimo@github · activity · last 12 months</text>
{''.join(month_labels)}
<text class="day" x="39" y="{TOP + 1 * (CELL + GAP) + 9}">Mon</text>
<text class="day" x="39" y="{TOP + 3 * (CELL + GAP) + 9}">Wed</text>
<text class="day" x="39" y="{TOP + 5 * (CELL + GAP) + 9}">Fri</text>
{''.join(cells)}
<text class="summary" x="70" y="190">{summary}</text>
<text class="muted" x="830" y="190" text-anchor="end">refreshed daily</text>
</svg>'''

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
