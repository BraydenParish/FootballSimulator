from __future__ import annotations

import sqlite3

import pytest

from backend.app.services.simulation_service import SimulationService
from backend.tests.conftest import initialize_database
from shared.utils.rules import load_simulation_rules


@pytest.fixture()
def simulation_service() -> SimulationService:
    rules = load_simulation_rules()
    return SimulationService(rules)


def test_simulate_game_produces_reasonable_scores(db_connection: sqlite3.Connection, simulation_service: SimulationService) -> None:
    game_row = db_connection.execute("SELECT * FROM games WHERE id = 1").fetchone()
    result = simulation_service._simulate_game(db_connection, game_row, detailed=False)

    assert 10 <= result.home_team["score"] <= 60
    assert 10 <= result.away_team["score"] <= 60

    for team_stats in result.team_stats.values():
        assert team_stats["total_yards"] >= 0
        assert team_stats["turnovers"] >= 0
        for player in team_stats["players"]:
            for key in ("passing_yards", "passing_tds", "interceptions", "rushing_yards", "rushing_tds", "receiving_yards", "receiving_tds", "tackles", "sacks", "forced_turnovers"):
                value = player.get(key, 0) or 0
                assert value >= 0


def test_simulate_game_is_deterministic_with_seed(tmp_path, simulation_service: SimulationService) -> None:
    db_path = tmp_path / "repro.db"
    if db_path.exists():
        db_path.unlink()
    initialize_database(db_path)

    first_connection = sqlite3.connect(db_path)
    first_connection.row_factory = sqlite3.Row
    game = first_connection.execute("SELECT * FROM games WHERE id = 1").fetchone()
    first_result = simulation_service._simulate_game(first_connection, game, detailed=False)
    first_payload = {
        "home": first_result.home_team["score"],
        "away": first_result.away_team["score"],
        "stats": first_result.team_stats,
    }
    first_connection.close()

    if db_path.exists():
        db_path.unlink()
    initialize_database(db_path)

    second_connection = sqlite3.connect(db_path)
    second_connection.row_factory = sqlite3.Row
    repeat_game = second_connection.execute("SELECT * FROM games WHERE id = 1").fetchone()
    second_result = simulation_service._simulate_game(second_connection, repeat_game, detailed=False)
    second_payload = {
        "home": second_result.home_team["score"],
        "away": second_result.away_team["score"],
        "stats": second_result.team_stats,
    }
    second_connection.close()

    assert second_payload == first_payload
