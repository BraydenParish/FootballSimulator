from __future__ import annotations

import sqlite3

import pytest

from database import load_data


@pytest.fixture()
def seeded_connection(tmp_path, monkeypatch):
    db_path = tmp_path / "seed.db"
    monkeypatch.setenv("NFL_GM_DB_PATH", str(db_path))
    load_data.main()
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


def test_team_count(seeded_connection: sqlite3.Connection) -> None:
    cur = seeded_connection.execute("SELECT COUNT(*) AS count FROM teams")
    assert cur.fetchone()["count"] == 32


def test_player_population(seeded_connection: sqlite3.Connection) -> None:
    roster_count = seeded_connection.execute(
        "SELECT COUNT(*) AS count FROM players WHERE status = 'active'"
    ).fetchone()["count"]
    assert roster_count == 576

    free_agents = seeded_connection.execute(
        "SELECT free_agent_year, COUNT(*) AS count FROM players WHERE status = 'free_agent' GROUP BY free_agent_year"
    ).fetchall()
    counts = {row["free_agent_year"]: row["count"] for row in free_agents}
    assert counts.get(2025) == 25
    assert counts.get(2026) == 25


def test_schedule_coverage(seeded_connection: sqlite3.Connection) -> None:
    games = seeded_connection.execute("SELECT COUNT(*) AS count FROM games").fetchone()["count"]
    assert games == 272

    unique_weeks = seeded_connection.execute(
        "SELECT COUNT(DISTINCT week) AS count FROM games"
    ).fetchone()["count"]
    assert unique_weeks == 17


def test_depth_chart_assignments(seeded_connection: sqlite3.Connection) -> None:
    assignments = seeded_connection.execute(
        "SELECT COUNT(*) AS count FROM players WHERE depth_chart_position IS NOT NULL"
    ).fetchone()["count"]
    assert assignments == 576
