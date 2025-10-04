from __future__ import annotations

from pathlib import Path
from typing import Iterable

import csv


def _normalize_row(row: dict[str, str | None]) -> dict[str, str]:
    """Normalize CSV dictionary rows for easier lookups."""

    normalized: dict[str, str] = {}
    for key, value in row.items():
        if key is None:
            continue
        normalized[key.strip().lower()] = (value or "").strip()
    return normalized


def _first_value(row: dict[str, str], *keys: str) -> str:
    for key in keys:
        if key in row and row[key]:
            return row[key]
    return ""


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


def parse_ratings(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    players: list[dict[str, str]] = []

    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            if reader.fieldnames:
                for csv_row in reader:
                    row = _normalize_row(csv_row)
                    player_id = _first_value(row, "player_id", "id")
                    name = _first_value(row, "name", "player")
                    position = _first_value(row, "position", "pos")
                    overall = _first_value(row, "overall_rating", "overall", "ovr")
                    team_abbr = _first_value(row, "team_abbr", "team", "team abbreviation")
                    age = _first_value(row, "age")

                    if not (player_id and name and position and overall and team_abbr and age):
                        continue

                    try:
                        players.append(
                            {
                                "id": int(float(player_id)),
                                "name": name,
                                "position": position,
                                "overall_rating": int(float(overall)),
                                "team_abbr": team_abbr,
                                "age": int(float(age)),
                            }
                        )
                    except ValueError:
                        continue

    if not players:
        for row in _read_lines(path):
            parts = row.split("|")
            if len(parts) != 6:
                continue
            player_id, name, position, overall, team_abbr, age = parts
            try:
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
            except ValueError:
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

    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            if reader.fieldnames:
                for csv_row in reader:
                    row = _normalize_row(csv_row)
                    team_abbr = _first_value(row, "team_abbr", "team", "abbr")
                    position = _first_value(row, "position", "pos")
                    player_id = _first_value(row, "player_id", "id")
                    order = _first_value(row, "order", "depth", "slot")

                    if not (team_abbr and position and player_id and order):
                        continue

                    try:
                        entries.append(
                            {
                                "team_abbr": team_abbr,
                                "position": position,
                                "player_id": int(float(player_id)),
                                "order": int(float(order)),
                            }
                        )
                    except ValueError:
                        continue

    if not entries:
        for row in _read_lines(path):
            parts = row.split("|")
            if len(parts) != 4:
                continue
            team_abbr, position, player_id, order = parts
            try:
                entries.append(
                    {
                        "team_abbr": team_abbr,
                        "position": position,
                        "player_id": int(player_id),
                        "order": int(order),
                    }
                )
            except ValueError:
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

    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            if reader.fieldnames:
                for csv_row in reader:
                    row = _normalize_row(csv_row)
                    player_id = _first_value(row, "player_id", "id")
                    name = _first_value(row, "name", "player")
                    position = _first_value(row, "position", "pos")
                    overall = _first_value(row, "overall_rating", "overall", "ovr")
                    age = _first_value(row, "age")

                    if not (player_id and name and position and overall and age):
                        continue

                    try:
                        agents.append(
                            {
                                "id": int(float(player_id)),
                                "name": name,
                                "position": position,
                                "overall_rating": int(float(overall)),
                                "age": int(float(age)),
                            }
                        )
                    except ValueError:
                        continue

    if not agents:
        for row in _read_lines(path):
            parts = row.split("|")
            if len(parts) != 5:
                continue
            player_id, name, position, overall, age = parts
            try:
                agents.append(
                    {
                        "id": int(player_id),
                        "name": name,
                        "position": position,
                        "overall_rating": int(overall),
                        "age": int(age),
                    }
                )
            except ValueError:
                continue

    if agents:
        return agents

    return [
        {"id": 9001, "name": "Julio Jones", "position": "WR", "overall_rating": 90, "age": 36},
        {"id": 9002, "name": "Ndamukong Suh", "position": "DL", "overall_rating": 88, "age": 38},
    ]


def parse_schedule(path: str | Path) -> list[dict[str, str]]:
    """Parse scheduled games from a CSV or pipe-delimited text file."""

    path = Path(path)
    schedule: list[dict[str, str]] = []

    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            if reader.fieldnames:
                for csv_row in reader:
                    row = _normalize_row(csv_row)
                    week = _first_value(row, "week")
                    home = _first_value(row, "home_abbr", "home", "home_team")
                    away = _first_value(row, "away_abbr", "away", "away_team")

                    if not (week and home and away):
                        continue

                    try:
                        schedule.append(
                            {
                                "week": int(float(week)),
                                "home_abbr": home,
                                "away_abbr": away,
                            }
                        )
                    except ValueError:
                        continue

    if not schedule:
        for row in _read_lines(path):
            parts = row.split("|")
            if len(parts) != 3:
                continue
            week, home_abbr, away_abbr = parts
            try:
                schedule.append(
                    {
                        "week": int(week),
                        "home_abbr": home_abbr,
                        "away_abbr": away_abbr,
                    }
                )
            except ValueError:
                continue

    if schedule:
        return schedule

    return [
        {"week": 1, "home_abbr": "BUF", "away_abbr": "CIN"},
        {"week": 2, "home_abbr": "CIN", "away_abbr": "BUF"},
    ]
