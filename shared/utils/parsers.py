from __future__ import annotations

from pathlib import Path
from typing import Iterable


def _read_lines(path: Path) -> Iterable[str]:
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        yield line


def parse_ratings(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    players: list[dict[str, str]] = []
    for row in _read_lines(path):
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


def parse_depth_charts(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    entries: list[dict[str, str]] = []
    for row in _read_lines(path):
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


def parse_free_agents(path: str | Path) -> list[dict[str, str]]:
    path = Path(path)
    agents: list[dict[str, str]] = []
    for row in _read_lines(path):
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


def parse_schedule(path: str | Path) -> list[dict[str, str]]:
    """Parse scheduled games from a pipe-delimited text file."""

    path = Path(path)
    schedule: list[dict[str, str]] = []
    for row in _read_lines(path):
        week, home_abbr, away_abbr = row.split("|")
        schedule.append(
            {
                "week": int(week),
                "home_abbr": home_abbr,
                "away_abbr": away_abbr,
            }
        )
    return schedule
