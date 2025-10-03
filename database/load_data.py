from __future__ import annotations

import csv
import sys
from pathlib import Path

from sqlalchemy import delete, select, text
from sqlalchemy.orm import Session

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import backend.app.db as db  # noqa: E402
from backend.app.models import (  # noqa: E402
    DepthChart,
    FreeAgent,
    Player,
    Schedule,
    Team,
)
from shared.constants.teams import TEAMS  # noqa: E402
from shared.utils.rules import load_game_rules  # noqa: E402

DATA_DIR = REPO_ROOT / "shared" / "data"
SCHEMA_PATH = BASE_DIR / "schema.sql"
CURRENT_YEAR = 2025


def _read_csv(name: str) -> list[dict[str, str]]:
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def init_schema() -> None:
    schema_sql = SCHEMA_PATH.read_text()
    with db.ENGINE.begin() as connection:
        raw_connection = connection.connection
        raw_connection.executescript(schema_sql)


def seed_teams(session: Session) -> dict[str, int]:
    session.execute(delete(Team))
    teams: list[Team] = []
    for abbr, meta in TEAMS.items():
        teams.append(
            Team(
                name=meta["name"],
                abbreviation=abbr,
                conference=meta["conference"],
                division=meta["division"],
            )
        )
    session.bulk_save_objects(teams)
    session.flush()
    mapping: dict[str, int] = {}
    for team in session.execute(select(Team.abbreviation, Team.id)):
        mapping[team.abbreviation] = team.id
    return mapping


def seed_players(session: Session, *, team_map: dict[str, int]) -> None:
    rules = load_game_rules()
    session.execute(delete(Player))
    players_csv = _read_csv("ratings.csv")
    player_objects: list[Player] = []
    for row in players_csv:
        team_abbr = row["team"].strip()
        ovr = int(row["ovr"])
        salary = rules.salary_base + rules.salary_per_rating * ovr
        player_objects.append(
            Player(
                id=int(row["id"]),
                name=row["name"].strip(),
                position=row["position"].strip(),
                team=team_abbr,
                team_id=team_map.get(team_abbr),
                ovr=ovr,
                overall_rating=ovr,
                spd=int(row.get("spd") or 0) or None,
                str=int(row.get("str") or row.get("strength") or 0) or None,
                agi=int(row.get("agi") or 0) or None,
                cod=int(row.get("cod") or 0) or None,
                inj=int(row.get("inj") or 0) or None,
                awr=int(row.get("awr") or 0) or None,
                age=int(row.get("age") or 25),
                salary=int(salary),
                contract_years=rules.max_contract_years,
                status="active",
                injury_status="healthy",
            )
        )
    session.add_all(player_objects)


def seed_depth_chart(session: Session) -> None:
    session.execute(delete(DepthChart))
    entries = _read_csv("depth_charts.csv")
    depth_objects: list[DepthChart] = []
    for row in entries:
        team = row["team"].strip()
        position = row["position"].strip()
        player_name = row["player_name"].strip()
        depth = int(row["depth"])
        player_id = session.execute(
            select(Player.id).where(Player.name == player_name)
        ).scalar_one_or_none()
        slot = f"{position}{depth}"
        if player_id is not None:
            session.execute(
                text(
                    "UPDATE players SET depth_chart_position = :slot, depth_chart_order = :depth WHERE id = :player_id"
                ),
                {"slot": slot, "depth": depth, "player_id": player_id},
            )
        depth_objects.append(
            DepthChart(
                team=team,
                position=position,
                player_name=player_name,
                depth=depth,
                player_id=player_id,
            )
        )
    session.add_all(depth_objects)


def seed_free_agents(session: Session, *, year: int) -> None:
    agents = _read_csv(f"{year}_free_agents.csv")
    rules = load_game_rules()
    session.execute(delete(FreeAgent).where(FreeAgent.year == year))
    for row in agents:
        player_id = int(row["id"])
        ovr = int(row["ovr"])
        salary = rules.salary_base + rules.salary_per_rating * ovr
        player = Player(
            id=player_id,
            name=row["name"].strip(),
            position=row["position"].strip(),
            team="FA",
            team_id=None,
            ovr=ovr,
            overall_rating=ovr,
            spd=None,
            str=None,
            agi=None,
            cod=None,
            inj=None,
            awr=None,
            age=int(row.get("age") or 25),
            salary=int(salary),
            contract_years=1,
            status="free_agent",
            free_agent_year=year,
            injury_status="healthy",
        )
        session.add(player)
        session.flush()
        session.merge(
            FreeAgent(
                id=player_id,
                name=row["name"].strip(),
                position=row["position"].strip(),
                age=float(row.get("age") or 0) or None,
                yoe=int(row.get("yoe") or 0) or None,
                prev_team=row.get("prev_team") or None,
                prev_aav=float(row.get("prev_aav") or 0) or None,
                contract_type=row.get("contract_type") or None,
                market_value=float(row.get("market_value") or 0) or None,
                year=year,
                player_id=player_id,
            )
        )


def seed_schedule(session: Session) -> None:
    session.execute(delete(Schedule))
    rows = _read_csv("schedule.csv")
    schedule_objects: list[Schedule] = []
    for row in rows:
        schedule_objects.append(
            Schedule(
                team=row["team"].strip(),
                week=int(row["week"]),
                opponent=row["opponent"].strip(),
                home_game=bool(int(row["home_game"])),
            )
        )
    session.add_all(schedule_objects)

    # Populate the games table from schedule rows (home team entries only).
    home_rows = [r for r in schedule_objects if r.home_game]
    session.execute(text("DELETE FROM games"))
    for entry in home_rows:
        home_team_id = session.execute(
            select(Team.id).where(Team.abbreviation == entry.team)
        ).scalar_one_or_none()
        away_team_id = session.execute(
            select(Team.id).where(Team.abbreviation == entry.opponent)
        ).scalar_one_or_none()
        if home_team_id is None or away_team_id is None:
            continue
        session.execute(
            text(
                """
                INSERT INTO games (week, home_team_id, away_team_id, home_score, away_score)
                VALUES (:week, :home_team_id, :away_team_id, 0, 0)
                """
            ),
            {
                "week": entry.week,
                "home_team_id": home_team_id,
                "away_team_id": away_team_id,
            },
        )


def seed_default_draft_picks(session: Session) -> None:
    session.execute(text("DELETE FROM draft_picks"))
    team_ids = [row.id for row in session.execute(select(Team.id))]
    for year in (2025, 2026):
        for draft_round in range(1, 4):
            for team_id in team_ids:
                session.execute(
                    text(
                        """
                        INSERT INTO draft_picks (team_id, year, round, original_team_id)
                        VALUES (:team_id, :year, :round, :team_id)
                        """
                    ),
                    {"team_id": team_id, "year": year, "round": draft_round},
                )


def main() -> None:
    db.configure_engine()
    db.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    init_schema()
    with db.SessionLocal() as session:
        team_map = seed_teams(session)
        seed_players(session, team_map=team_map)
        seed_depth_chart(session)
        seed_free_agents(session, year=CURRENT_YEAR)
        seed_free_agents(session, year=CURRENT_YEAR + 1)
        seed_schedule(session)
        seed_default_draft_picks(session)
        session.commit()
    print(f"Database initialized at {db.DB_PATH}")


if __name__ == "__main__":
    main()
