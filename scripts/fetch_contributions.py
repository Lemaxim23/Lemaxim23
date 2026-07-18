#!/usr/bin/env python3
"""Fetch the public GitHub contribution calendar and store normalized JSON."""

from __future__ import annotations

import datetime as dt
import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


USERNAME = os.environ.get("GH_PROFILE_USER", "Lemaxim23")
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "contributions.json"
URL = f"https://github.com/users/{USERNAME}/contributions"


def empty_calendar() -> list[dict[str, object]]:
    today = dt.date.today()
    start = today - dt.timedelta(days=370)
    return [
        {"date": (start + dt.timedelta(days=index)).isoformat(), "count": 0}
        for index in range(371)
    ]


def fetch_calendar() -> list[dict[str, object]]:
    response = requests.get(
        URL,
        headers={"User-Agent": "Lemaxim23-profile-readme/1.0"},
        timeout=30,
    )
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    cells = soup.select("td.ContributionCalendar-day[data-date], td[data-date]")
    if not cells:
        raise RuntimeError("GitHub contribution cells were not found")

    days: dict[str, int] = {}
    for cell in cells:
        date = cell.get("data-date")
        if not date:
            continue

        tooltip = ""
        cell_id = cell.get("id")
        if cell_id:
            tooltip_node = soup.find("tool-tip", attrs={"for": cell_id})
            if tooltip_node:
                tooltip = tooltip_node.get_text(" ", strip=True)

        match = re.search(r"([\d,]+)\s+contribution", tooltip, flags=re.I)
        count = int(match.group(1).replace(",", "")) if match else 0
        days[date] = count

    return [{"date": date, "count": days[date]} for date in sorted(days)]


def streaks(days: list[dict[str, object]]) -> tuple[int, int]:
    counts = [int(day["count"]) for day in days]
    current = 0
    cursor = len(counts) - 1
    if cursor >= 0 and counts[cursor] == 0:
        cursor -= 1
    while cursor >= 0 and counts[cursor] > 0:
        current += 1
        cursor -= 1

    longest = run = 0
    for count in counts:
        run = run + 1 if count > 0 else 0
        longest = max(longest, run)
    return current, longest


def main() -> None:
    try:
        days = fetch_calendar()
        source = "github"
    except Exception as error:  # Keep the artwork valid during temporary outages.
        if OUTPUT.exists():
            existing = json.loads(OUTPUT.read_text(encoding="utf-8"))
            days = existing.get("days", empty_calendar())
            source = "cached"
        else:
            days = empty_calendar()
            source = "fallback"
        print(f"warning: {error}; using {source} contribution data")

    current, longest = streaks(days)
    counts = [int(day["count"]) for day in days]
    payload = {
        "username": USERNAME,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": source,
        "total": sum(counts),
        "active_days": sum(count > 0 for count in counts),
        "current_streak": current,
        "longest_streak": longest,
        "days": days,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUTPUT}: {payload['total']} contributions")


if __name__ == "__main__":
    main()
