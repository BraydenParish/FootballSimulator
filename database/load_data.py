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
SCHEMA_PATH = BASE_DIR / "schema.sql"
CURRENT_YEAR = 2025


def init_db(connection: sqlite3.Connection) -> None:
    schema_sql = SCHEMA_PATH.read_text()
    connection.executescript(schema_sql)


def load_teams(connection: sqlite3.Connection) -> None:
    team_rows = [
        (meta["name"], abbr, meta["conference"], meta["division"])
        for abbr, meta in TEAMS.items()
    ]
    connection.executemany(
        """
        INSERT OR IGNORE INTO teams (name, abbreviation, conference, division)
        VALUES (?, ?, ?, ?)
        """,
        team_rows,
    )


def load_players(connection: sqlite3.Connection, *, rules) -> None:
    players = parse_ratings(DATA_DIR / "ratings.csv")
    if not players:
        return

    team_id_lookup = {
        row["abbreviation"]: row["id"]
        for row in connection.execute("SELECT id, abbreviation FROM teams").fetchall()
    }

    player_rows: list[dict[str, object]] = []
    for player in players:
        team_abbr = player.get("team_abbr")
        team_id = team_id_lookup.get(team_abbr) if team_abbr else None
        salary = rules.salary_base + rules.salary_per_rating * player["overall_rating"]
        player_rows.append(
            {
                "id": player["id"],
                "name": player["name"],
                "position": player["position"],
                "overall_rating": player["overall_rating"],
                "age": player["age"],
                "team_id": team_id,
                "salary": salary,
                "contract_years": rules.max_contract_years,
            }
        )

    connection.executemany(
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
        player_rows,
    )


def load_schedule(connection: sqlite3.Connection) -> None:
    games = parse_schedule(DATA_DIR / "schedule.csv")
    if not games:
        return

    team_id_lookup = {
        row["abbreviation"]: row["id"]
        for row in connection.execute("SELECT id, abbreviation FROM teams").fetchall()
    }

    game_rows: list[tuple[int, int, int]] = []
    for game in games:
        home_team_id = team_id_lookup.get(game["home_abbr"])
        away_team_id = team_id_lookup.get(game["away_abbr"])

        if home_team_id is None or away_team_id is None:
            raise ValueError(
                f"Missing team for schedule entry: {game['home_abbr']} vs {game['away_abbr']}"
            )

        game_rows.append((game["week"], home_team_id, away_team_id))

    connection.executemany(
        """
        INSERT OR IGNORE INTO games (week, home_team_id, away_team_id)
        VALUES (?, ?, ?)
        """,
        game_rows,
    )


def apply_depth_chart(connection: sqlite3.Connection) -> None:
    depth_entries = parse_depth_charts(DATA_DIR / "depth_charts.csv")
    if not depth_entries:
        return

    update_payload: list[tuple[str, int, int]] = []
    for entry in depth_entries:
        depth_position = entry["position"].upper()
        order = entry["order"]
        if not any(char.isdigit() for char in depth_position):
            depth_position = f"{depth_position}{order}"
        update_payload.append((depth_position, order, entry["player_id"]))

    connection.executemany(
        """
        UPDATE players
        SET depth_chart_position = ?, depth_chart_order = ?
        WHERE id = ?
        """,
        update_payload,
    )


def load_free_agents(connection: sqlite3.Connection, *, rules, year: int) -> None:
    agents = parse_free_agents(DATA_DIR / f"{year}_Free_Agents.csv")
    if not agents:
        return

    payload: list[dict[str, object]] = []
    for agent in agents:
        salary = rules.salary_base + rules.salary_per_rating * agent["overall_rating"]
        payload.append(
            {
                **agent,
                "salary": salary,
                "free_agent_year": year,
            }
        )

    connection.executemany(
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
        payload,
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


def resolve_db_path() -> Path:
    raw_path = os.environ.get("NFL_GM_DB_PATH")
    if raw_path:
        return Path(raw_path)
    return BASE_DIR / "nfl_gm_sim.db"


def main() -> None:
    db_path = resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        init_db(connection)
        load_teams(connection)
        rules = load_game_rules()
        load_players(connection, rules=rules)
        load_schedule(connection)
        apply_depth_chart(connection)
        load_free_agents(connection, rules=rules, year=CURRENT_YEAR)
        load_free_agents(connection, rules=rules, year=CURRENT_YEAR + 1)
        load_default_draft_picks(connection)
        connection.commit()
    print(f"Database initialized at {db_path}")


if __name__ == "__main__":
    main()
