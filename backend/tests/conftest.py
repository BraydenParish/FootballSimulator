from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    abbreviation TEXT NOT NULL UNIQUE,
    conference TEXT NOT NULL,
    division TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    position TEXT NOT NULL,
    overall_rating INTEGER NOT NULL,
    age INTEGER DEFAULT 25,
    team_id INTEGER,
    depth_chart_position TEXT,
    depth_chart_order INTEGER,
    status TEXT DEFAULT 'active',
    salary INTEGER DEFAULT 0,
    contract_years INTEGER DEFAULT 0,
    free_agent_year INTEGER,
    injury_status TEXT DEFAULT 'healthy',
    FOREIGN KEY (team_id) REFERENCES teams (id)
);

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY,
    week INTEGER NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,
    played_at TEXT,
    FOREIGN KEY (home_team_id) REFERENCES teams (id),
    FOREIGN KEY (away_team_id) REFERENCES teams (id)
);

CREATE TABLE IF NOT EXISTS draft_picks (
    id INTEGER PRIMARY KEY,
    team_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    round INTEGER NOT NULL,
    original_team_id INTEGER NOT NULL,
    FOREIGN KEY (team_id) REFERENCES teams (id),
    FOREIGN KEY (original_team_id) REFERENCES teams (id)
);

CREATE TABLE IF NOT EXISTS team_game_stats (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    total_yards INTEGER DEFAULT 0,
    turnovers INTEGER DEFAULT 0,
    FOREIGN KEY (game_id) REFERENCES games (id),
    FOREIGN KEY (team_id) REFERENCES teams (id)
);

CREATE TABLE IF NOT EXISTS player_game_stats (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    passing_yards INTEGER DEFAULT 0,
    passing_tds INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    rushing_yards INTEGER DEFAULT 0,
    rushing_tds INTEGER DEFAULT 0,
    receiving_yards INTEGER DEFAULT 0,
    receiving_tds INTEGER DEFAULT 0,
    tackles INTEGER DEFAULT 0,
    sacks REAL DEFAULT 0,
    forced_turnovers INTEGER DEFAULT 0,
    FOREIGN KEY (game_id) REFERENCES games (id),
    FOREIGN KEY (player_id) REFERENCES players (id),
    FOREIGN KEY (team_id) REFERENCES teams (id)
);

CREATE TABLE IF NOT EXISTS game_events (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    sequence INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    clock TEXT NOT NULL,
    team_id INTEGER,
    player_id INTEGER,
    description TEXT NOT NULL,
    highlight_type TEXT NOT NULL,
    impact TEXT,
    points INTEGER NOT NULL,
    home_score_after INTEGER NOT NULL,
    away_score_after INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (game_id) REFERENCES games (id),
    FOREIGN KEY (team_id) REFERENCES teams (id),
    FOREIGN KEY (player_id) REFERENCES players (id)
);

CREATE TABLE IF NOT EXISTS week_narratives (
    id INTEGER PRIMARY KEY,
    week INTEGER NOT NULL,
    headline TEXT NOT NULL,
    body TEXT,
    game_id INTEGER,
    tags TEXT,
    sequence INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (game_id) REFERENCES games (id)
);
"""

TEAM_ROWS = [
    (1, "Buffalo Bills", "BUF", "AFC", "East"),
    (2, "Cincinnati Bengals", "CIN", "AFC", "North"),
]

PLAYER_ROWS = [
    (1, "Josh Allen", "QB", 95, 28, 1, "QB1", 1, "active", 43000000, 6, None, "healthy"),
    (2, "James Cook", "RB", 85, 25, 1, "RB1", 1, "active", 2000000, 3, None, "healthy"),
    (3, "Stefon Diggs", "WR", 93, 30, 1, "WR1", 1, "active", 25000000, 4, None, "healthy"),
    (4, "Von Miller", "EDGE", 91, 34, 1, "EDGE1", 1, "active", 20000000, 2, None, "healthy"),
    (5, "Joe Burrow", "QB", 95, 27, 2, "QB1", 1, "active", 45000000, 5, None, "healthy"),
    (6, "Joe Mixon", "RB", 88, 28, 2, "RB1", 1, "active", 12000000, 3, None, "healthy"),
    (7, "Ja'Marr Chase", "WR", 96, 24, 2, "WR1", 1, "active", 5000000, 3, None, "healthy"),
    (8, "Trey Hendrickson", "EDGE", 90, 29, 2, "EDGE1", 1, "active", 15000000, 3, None, "healthy"),
    (9, "Kyle Allen", "QB", 68, 27, 1, "QB2", 2, "active", 1500000, 1, None, "healthy"),
    (10, "Jake Browning", "QB", 70, 27, 2, "QB2", 2, "active", 1500000, 1, None, "healthy"),
    (11, "Jarvis Landry", "WR", 80, 31, None, None, None, "free_agent", 3000000, 1, 2025, "healthy"),
]

DRAFT_PICK_ROWS = [
    (1, 1, 2025, 1, 1),
    (2, 2, 2025, 2, 2),
]

GAME_ROWS = [
    (1, 1, 1, 2, 0, 0, None),
]


def initialize_database(db_path: Path) -> None:
    connection = sqlite3.connect(db_path)
    try:
        connection.executescript(SCHEMA_SQL)
        connection.executemany(
            "INSERT INTO teams (id, name, abbreviation, conference, division) VALUES (?, ?, ?, ?, ?)",
            TEAM_ROWS,
        )
        connection.executemany(
            """
            INSERT INTO players (
                id,
                name,
                position,
                overall_rating,
                age,
                team_id,
                depth_chart_position,
                depth_chart_order,
                status,
                salary,
                contract_years,
                free_agent_year,
                injury_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            PLAYER_ROWS,
        )
        connection.executemany(
            """
            INSERT INTO draft_picks (
                id,
                team_id,
                year,
                round,
                original_team_id
            ) VALUES (?, ?, ?, ?, ?)
            """,
            DRAFT_PICK_ROWS,
        )
        connection.executemany(
            """
            INSERT INTO games (
                id,
                week,
                home_team_id,
                away_team_id,
                home_score,
                away_score,
                played_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            GAME_ROWS,
        )
        connection.commit()
    finally:
        connection.close()


@pytest.fixture(scope="function")
def seeded_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    db_path = tmp_path / "test.db"
    initialize_database(db_path)

    monkeypatch.setenv("NFL_GM_DB_PATH", str(db_path))
    for module in ("backend.main", "backend.app.db"):
        sys.modules.pop(module, None)

    import backend.app.db  # noqa: F401
    import backend.main  # noqa: F401

    yield db_path


@pytest.fixture(scope="function")
def api_client(seeded_database: Path) -> Iterator[TestClient]:
    from backend import main as main_module

    with TestClient(main_module.app) as client:
        yield client


@pytest.fixture(scope="function")
def db_connection(seeded_database: Path) -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(seeded_database)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
    finally:
        connection.close()


__all__ = ["initialize_database"]
