from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.constants.teams import TEAMS  # noqa: E402
from shared.utils.parsers import (  # noqa: E402
    parse_depth_charts,
    parse_free_agents,
    parse_ratings,
    parse_schedule,
)
from shared.utils.rules import load_game_rules  # noqa: E402

DATA_DIR = REPO_ROOT / "shared" / "data"
DB_PATH = Path(os.environ.get("NFL_GM_DB_PATH", BASE_DIR / "nfl_gm_sim.db"))
SCHEMA_PATH = BASE_DIR / "schema.sql"
CURRENT_YEAR = 2025


def _resolve_data_file(*names: str) -> Path:
    for name in names:
        for extension in (".csv", ".txt"):
            candidate = DATA_DIR / f"{name}{extension}"
            if candidate.exists():
                return candidate
    # Fall back to the first name with the legacy .txt extension.
    return DATA_DIR / f"{names[0]}.txt"


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


def load_players(connection: sqlite3.Connection, *, rules) -> None:
    ratings_path = _resolve_data_file("ratings")
    players = parse_ratings(ratings_path)
    for player in players:
        team_abbr = player.pop("team_abbr")
        team_id_row = connection.execute(
            "SELECT id FROM teams WHERE abbreviation = ?",
            (team_abbr,),
        ).fetchone()
        team_id = team_id_row[0] if team_id_row else None
        salary = rules.salary_base + rules.salary_per_rating * player["overall_rating"]
        connection.execute(
            """
            INSERT OR REPLACE INTO players (
                id,
                name,
                position,
                overall_rating,
                age,
                team_id,
                salary,
                contract_years,
                status,
                injury_status
            )
            VALUES (
                :id,
                :name,
                :position,
                :overall_rating,
                :age,
                :team_id,
                :salary,
                :contract_years,
                'active',
                'healthy'
            )
            """,
            {
                **player,
                "team_id": team_id,
                "salary": salary,
                "contract_years": rules.max_contract_years,
            },
        )


def load_schedule(connection: sqlite3.Connection) -> None:
    schedule_path = _resolve_data_file("schedule")
    games = parse_schedule(schedule_path)
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
    depth_entries = parse_depth_charts(
        _resolve_data_file("NFL_Depth_Charts", "depth_charts")
    )
    for entry in depth_entries:
        depth_position = entry["position"].upper()
        order = entry["order"]
        if not any(char.isdigit() for char in depth_position):
            depth_position = f"{depth_position}{order}"
        connection.execute(
            """
            UPDATE players
            SET depth_chart_position = ?, depth_chart_order = ?
            WHERE id = ?
            """,
            (depth_position, order, entry["player_id"]),
        )


def load_free_agents(connection: sqlite3.Connection, *, rules, year: int) -> None:
    agents = parse_free_agents(
        _resolve_data_file(f"{year}_Free_Agents", f"{year}_free_agents")
    )
    for agent in agents:
        salary = rules.salary_base + rules.salary_per_rating * agent["overall_rating"]
        connection.execute(
            """
            INSERT OR REPLACE INTO players (
                id,
                name,
                position,
                overall_rating,
                age,
                status,
                salary,
                contract_years,
                free_agent_year,
                injury_status
            )
            VALUES (
                :id,
                :name,
                :position,
                :overall_rating,
                :age,
                'free_agent',
                :salary,
                1,
                :free_agent_year,
                'healthy'
            )
            """,
            {
                **agent,
                "salary": salary,
                "free_agent_year": year,
            },
        )


def load_default_draft_picks(connection: sqlite3.Connection) -> None:
    teams = connection.execute("SELECT id FROM teams").fetchall()
    for year in (2025, 2026):
        for draft_round in range(1, 4):
            for team in teams:
                team_id = team[0] if isinstance(team, tuple) else team["id"]
                connection.execute(
                    """
                    INSERT OR IGNORE INTO draft_picks (team_id, year, round, original_team_id)
                    VALUES (?, ?, ?, ?)
                    """,
                    (team_id, year, draft_round, team_id),
                )


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        init_db(connection)
        load_teams(connection)
        rules = load_game_rules()
        load_players(connection, rules=rules)
        load_schedule(connection)
        apply_depth_chart(connection)
        load_free_agents(connection, rules=rules, year=CURRENT_YEAR)
        load_default_draft_picks(connection)
        connection.commit()
    print(f"Database initialized at {DB_PATH}")


if __name__ == "__main__":
    main()
