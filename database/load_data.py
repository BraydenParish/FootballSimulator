from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.constants.teams import TEAMS  # noqa: E402
from shared.utils.parsers import (
    parse_depth_charts,
    parse_free_agents,
    parse_ratings,
    parse_schedule,
)  # noqa: E402

DATA_DIR = REPO_ROOT / "shared" / "data"
DB_PATH = BASE_DIR / "nfl_gm_sim.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"


def init_db(connection: sqlite3.Connection) -> None:
    schema_sql = SCHEMA_PATH.read_text()
    connection.executescript(schema_sql)


def load_teams(connection: sqlite3.Connection) -> None:
    for abbr, meta in TEAMS.items():
        connection.execute(
            """
            INSERT OR IGNORE INTO teams (name, abbreviation, conference, division)
            VALUES (?, ?, ?, ?)
            """,
            (meta["name"], abbr, meta["conference"], meta["division"]),
        )


def load_players(connection: sqlite3.Connection) -> None:
    players = parse_ratings(DATA_DIR / "ratings.txt")
    for player in players:
        team_abbr = player.pop("team_abbr")
        team_id_row = connection.execute(
            "SELECT id FROM teams WHERE abbreviation = ?",
            (team_abbr,),
        ).fetchone()
        team_id = team_id_row[0] if team_id_row else None
        connection.execute(
            """
            INSERT OR REPLACE INTO players (id, name, position, overall_rating, age, team_id)
            VALUES (:id, :name, :position, :overall_rating, :age, :team_id)
            """,
            {**player, "team_id": team_id},
        )


def load_schedule(connection: sqlite3.Connection) -> None:
    games = parse_schedule(DATA_DIR / "schedule.txt")
    for game in games:
        home_team_row = connection.execute(
            "SELECT id FROM teams WHERE abbreviation = ?",
            (game["home_abbr"],),
        ).fetchone()
        away_team_row = connection.execute(
            "SELECT id FROM teams WHERE abbreviation = ?",
            (game["away_abbr"],),
        ).fetchone()

        if home_team_row is None or away_team_row is None:
            raise ValueError(
                f"Missing team for schedule entry: {game['home_abbr']} vs {game['away_abbr']}"
            )

        existing = connection.execute(
            """
            SELECT id FROM games
            WHERE week = ? AND home_team_id = ? AND away_team_id = ?
            """,
            (game["week"], home_team_row[0], away_team_row[0]),
        ).fetchone()

        if existing:
            continue

        connection.execute(
            """
            INSERT INTO games (week, home_team_id, away_team_id)
            VALUES (?, ?, ?)
            """,
            (game["week"], home_team_row[0], away_team_row[0]),
        )


def apply_depth_chart(connection: sqlite3.Connection) -> None:
    depth_entries = parse_depth_charts(DATA_DIR / "depth_charts.txt")
    for entry in depth_entries:
        connection.execute(
            """
            UPDATE players
            SET depth_chart_position = :position
            WHERE id = :player_id
            """,
            entry,
        )


def load_free_agents(connection: sqlite3.Connection) -> None:
    agents = parse_free_agents(DATA_DIR / "free_agents.txt")
    for agent in agents:
        connection.execute(
            """
            INSERT OR REPLACE INTO players (id, name, position, overall_rating, age, status)
            VALUES (:id, :name, :position, :overall_rating, :age, 'free_agent')
            """,
            agent,
        )


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        init_db(connection)
        load_teams(connection)
        load_players(connection)
        load_schedule(connection)
        apply_depth_chart(connection)
        load_free_agents(connection)
        connection.commit()
    print(f"Database initialized at {DB_PATH}")


if __name__ == "__main__":
    main()
