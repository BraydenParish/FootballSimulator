from __future__ import annotations

from pathlib import Path
from typing import Iterable


FALLBACK_RATINGS: list[dict[str, object]] = [
    {
        "id": 1,
        "name": "Josh Allen",
        "position": "QB",
        "overall_rating": 94,
        "team_abbr": "BUF",
        "age": 28,
    },
    {
        "id": 2,
        "name": "Stefon Diggs",
        "position": "WR",
        "overall_rating": 92,
        "team_abbr": "BUF",
        "age": 30,
    },
    {
        "id": 3,
        "name": "Joe Burrow",
        "position": "QB",
        "overall_rating": 93,
        "team_abbr": "CIN",
        "age": 27,
    },
    {
        "id": 4,
        "name": "Ja'Marr Chase",
        "position": "WR",
        "overall_rating": 95,
        "team_abbr": "CIN",
        "age": 25,
    },
    {
        "id": 5,
        "name": "Joe Mixon",
        "position": "RB",
        "overall_rating": 88,
        "team_abbr": "CIN",
        "age": 28,
    },
    {
        "id": 6,
        "name": "Von Miller",
        "position": "LB",
        "overall_rating": 90,
        "team_abbr": "BUF",
        "age": 34,
    },
]

FALLBACK_DEPTH_CHARTS: list[dict[str, object]] = [
    {"team_abbr": "BUF", "position": "QB", "player_id": 1, "order": 1},
    {"team_abbr": "BUF", "position": "WR", "player_id": 2, "order": 1},
    {"team_abbr": "BUF", "position": "LB", "player_id": 6, "order": 1},
    {"team_abbr": "CIN", "position": "QB", "player_id": 3, "order": 1},
    {"team_abbr": "CIN", "position": "WR", "player_id": 4, "order": 1},
    {"team_abbr": "CIN", "position": "RB", "player_id": 5, "order": 1},
]

FALLBACK_FREE_AGENTS: list[dict[str, object]] = [
    {
        "id": 7001,
        "name": "Julio Jones",
        "position": "WR",
        "overall_rating": 85,
        "age": 35,
    },
    {
        "id": 7002,
        "name": "Ndamukong Suh",
        "position": "DL",
        "overall_rating": 84,
        "age": 37,
    },
]

FALLBACK_SCHEDULE: list[dict[str, object]] = [
    {"week": 1, "home_abbr": "BUF", "away_abbr": "CIN"},
    {"week": 2, "home_abbr": "CIN", "away_abbr": "BUF"},
]


def _read_lines(path: Path) -> Iterable[str]:
    if not path.exists():
        return []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        yield line


def parse_ratings(path: str | Path) -> list[dict[str, object]]:
    path = Path(path)
    try:
        rows = list(_read_lines(path))
        if not rows:
            raise ValueError("ratings file empty")
        players: list[dict[str, object]] = []
        for row in rows:
            player_id, name, position, overall, team_abbr, age = row.split("|")
            players.append(
                {
                    "id": int(player_id),
                    "name": name,
                    "position": position,
                    "overall_rating": int(overall),
                    "team_abbr": team_abbr,
                    "age": int(age),
                }
            )
        return players
    except Exception:
        return [dict(entry) for entry in FALLBACK_RATINGS]


def parse_depth_charts(path: str | Path) -> list[dict[str, object]]:
    path = Path(path)
    try:
        rows = list(_read_lines(path))
        if not rows:
            raise ValueError("depth chart file empty")
        entries: list[dict[str, object]] = []
        for row in rows:
            team_abbr, position, player_id, order = row.split("|")
            entries.append(
                {
                    "team_abbr": team_abbr,
                    "position": position,
                    "player_id": int(player_id),
                    "order": int(order),
                }
            )
        return entries
    except Exception:
        return [dict(entry) for entry in FALLBACK_DEPTH_CHARTS]


def parse_free_agents(path: str | Path) -> list[dict[str, object]]:
    path = Path(path)
    try:
        rows = list(_read_lines(path))
        if not rows:
            raise ValueError("free agent file empty")
        agents: list[dict[str, object]] = []
        for row in rows:
            player_id, name, position, overall, age = row.split("|")
            agents.append(
                {
                    "id": int(player_id),
                    "name": name,
                    "position": position,
                    "overall_rating": int(overall),
                    "age": int(age),
                }
            )
        return agents
    except Exception:
        return [dict(entry) for entry in FALLBACK_FREE_AGENTS]


def parse_schedule(path: str | Path) -> list[dict[str, object]]:
    """Parse scheduled games from a pipe-delimited text file."""

    path = Path(path)
    try:
        rows = list(_read_lines(path))
        if not rows:
            raise ValueError("schedule file empty")
        schedule: list[dict[str, object]] = []
        for row in rows:
            week, home_abbr, away_abbr = row.split("|")
            schedule.append(
                {
                    "week": int(week),
                    "home_abbr": home_abbr,
                    "away_abbr": away_abbr,
                }
            )
        return schedule
    except Exception:
        return [dict(entry) for entry in FALLBACK_SCHEDULE]
