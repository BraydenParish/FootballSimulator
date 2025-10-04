from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import backend.app.db as db  # noqa: E402
from database import load_data  # noqa: E402

DATA_DIR = ROOT_DIR / "shared" / "data"


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


@pytest.fixture()
def seeded_db(tmp_path, monkeypatch):
    db_path = tmp_path / "seeded.db"
    monkeypatch.setenv("NFL_GM_DB_PATH", str(db_path))
    load_data.main()
    try:
        yield db_path
    finally:
        monkeypatch.delenv("NFL_GM_DB_PATH", raising=False)
        db.configure_engine()


def test_players_table_matches_ratings_csv(seeded_db: Path) -> None:
    ratings = _read_csv(DATA_DIR / "ratings.csv")
    expected_names = {row["name"] for row in ratings}
    with sqlite3.connect(seeded_db) as connection:
        rows = connection.execute(
            "SELECT name, team, ovr FROM players WHERE status = 'active' ORDER BY name"
        ).fetchall()
    assert {row[0] for row in rows} == expected_names
    assert all(row[2] >= 60 for row in rows)


def test_free_agent_pool_matches_csvs(seeded_db: Path) -> None:
    csv_entries = []
    for filename, year in (("2025_free_agents.csv", 2025), ("2026_free_agents.csv", 2026)):
        for row in _read_csv(DATA_DIR / filename):
            csv_entries.append((row["name"], year))
    with sqlite3.connect(seeded_db) as connection:
        rows = connection.execute(
            "SELECT name, year FROM free_agents ORDER BY year, name"
        ).fetchall()
    assert len(rows) == len(csv_entries)
    assert {(row[0], row[1]) for row in rows} == set(csv_entries)


def test_schedule_and_games_seeded(seeded_db: Path) -> None:
    schedule_rows = _read_csv(DATA_DIR / "schedule.csv")
    with sqlite3.connect(seeded_db) as connection:
        schedule_count = connection.execute("SELECT COUNT(*) FROM schedule").fetchone()[0]
        games_count = connection.execute("SELECT COUNT(*) FROM games").fetchone()[0]
    assert schedule_count == len(schedule_rows)
    expected_games = sum(1 for row in schedule_rows if int(row["home_game"]) == 1)
    assert games_count == expected_games
