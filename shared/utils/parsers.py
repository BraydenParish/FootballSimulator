from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable


def _read_lines(path: Path) -> Iterable[str]:
    if not path.exists():
        return []

    lines: list[str] = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        rows: list[dict[str, str]] = []
        for row in reader:
            if not row:
                continue
            cleaned = {key: (value.strip() if isinstance(value, str) else value) for key, value in row.items()}
            if any(cleaned.values()):
                rows.append(cleaned)
    return rows


def parse_ratings(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    players: list[dict[str, str]] = []
    for row in _read_csv(path):
        try:
            players.append(
                {
                    "id": int(row["id"]),
                    "name": row["name"],
                    "position": row["position"],
                    "overall_rating": int(row["overall_rating"]),
                    "team_abbr": row["team_abbr"],
                    "age": int(row.get("age", 0) or 0) or 25,
                }
            )
        except (KeyError, TypeError, ValueError):
            continue

    if players:
        return players

    # Fallback data used when the ratings feed has not been prepared yet.
    return [
        {"id": 1, "name": "Josh Allen", "position": "QB", "overall_rating": 96, "team_abbr": "BUF", "age": 28},
        {"id": 2, "name": "Stefon Diggs", "position": "WR", "overall_rating": 94, "team_abbr": "BUF", "age": 30},
        {"id": 3, "name": "James Cook", "position": "RB", "overall_rating": 84, "team_abbr": "BUF", "age": 25},
        {"id": 4, "name": "Joe Burrow", "position": "QB", "overall_rating": 95, "team_abbr": "CIN", "age": 28},
        {"id": 5, "name": "Ja'Marr Chase", "position": "WR", "overall_rating": 93, "team_abbr": "CIN", "age": 25},
        {"id": 6, "name": "Tee Higgins", "position": "WR", "overall_rating": 90, "team_abbr": "CIN", "age": 26},
        {"id": 7, "name": "Joe Mixon", "position": "RB", "overall_rating": 88, "team_abbr": "CIN", "age": 28},
        {"id": 8, "name": "Dawson Knox", "position": "TE", "overall_rating": 82, "team_abbr": "BUF", "age": 27},
        {"id": 9, "name": "Von Miller", "position": "EDGE", "overall_rating": 88, "team_abbr": "BUF", "age": 35},
        {"id": 10, "name": "Logan Wilson", "position": "LB", "overall_rating": 85, "team_abbr": "CIN", "age": 26},
    ]


def parse_depth_charts(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    entries: list[dict[str, str]] = []
    for row in _read_csv(path):
        try:
            entries.append(
                {
                    "team_abbr": row["team_abbr"],
                    "position": row["position"],
                    "player_id": int(row["player_id"]),
                    "order": int(row["order"]),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue

    if entries:
        return entries

    return [
        {"team_abbr": "BUF", "position": "QB", "player_id": 1, "order": 1},
        {"team_abbr": "BUF", "position": "RB", "player_id": 3, "order": 1},
        {"team_abbr": "BUF", "position": "WR", "player_id": 2, "order": 1},
        {"team_abbr": "BUF", "position": "TE", "player_id": 8, "order": 1},
        {"team_abbr": "BUF", "position": "EDGE", "player_id": 9, "order": 1},
        {"team_abbr": "CIN", "position": "QB", "player_id": 4, "order": 1},
        {"team_abbr": "CIN", "position": "RB", "player_id": 7, "order": 1},
        {"team_abbr": "CIN", "position": "WR", "player_id": 5, "order": 1},
        {"team_abbr": "CIN", "position": "WR", "player_id": 6, "order": 2},
        {"team_abbr": "CIN", "position": "LB", "player_id": 10, "order": 1},
    ]


def parse_free_agents(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    agents: list[dict[str, str]] = []
    for row in _read_csv(path):
        try:
            agents.append(
                {
                    "id": int(row["id"]),
                    "name": row["name"],
                    "position": row["position"],
                    "overall_rating": int(row["overall_rating"]),
                    "age": int(row["age"]),
                }
            )
        except (KeyError, TypeError, ValueError):
            continue

    if agents:
        return agents

    return [
        {"id": 9001, "name": "Julio Jones", "position": "WR", "overall_rating": 90, "age": 36},
        {"id": 9002, "name": "Ndamukong Suh", "position": "DL", "overall_rating": 88, "age": 38},
    ]


def parse_schedule(path: str | Path) -> list[dict[str, str]]:
    """Parse scheduled games from a comma-delimited export."""

    path = Path(path)
    schedule: list[dict[str, str]] = []
    for row in _read_csv(path):
        try:
            schedule.append(
                {
                    "week": int(row["week"]),
                    "home_abbr": row["home_abbr"],
                    "away_abbr": row["away_abbr"],
                }
            )
        except (KeyError, TypeError, ValueError):
            continue

    if schedule:
        return schedule

    return [
        {"week": 1, "home_abbr": "BUF", "away_abbr": "CIN"},
        {"week": 2, "home_abbr": "CIN", "away_abbr": "BUF"},
    ]
