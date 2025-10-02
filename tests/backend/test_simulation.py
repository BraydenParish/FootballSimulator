from __future__ import annotations

import os
import sqlite3

from fastapi.testclient import TestClient


def _db_connection() -> sqlite3.Connection:
    path = os.environ["NFL_GM_DB_PATH"]
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def test_simulate_week_creates_box_scores(api_client: TestClient) -> None:
    response = api_client.post("/simulate-week", json={"week": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["week"] == 1
    assert len(data["results"]) >= 1

    first_result = data["results"][0]
    assert "home_team" in first_result and "away_team" in first_result
    assert "team_stats" in first_result
    assert isinstance(first_result["injuries"], list)

    game_id = first_result["game_id"]
    with _db_connection() as connection:
        game_row = connection.execute(
            "SELECT played_at, home_score, away_score FROM games WHERE id = ?",
            (game_id,),
        ).fetchone()
        assert game_row["played_at"] is not None
        assert game_row["home_score"] >= 0

        team_stats = connection.execute(
            "SELECT COUNT(*) AS total FROM team_game_stats WHERE game_id = ?",
            (game_id,),
        ).fetchone()["total"]
        player_stats = connection.execute(
            "SELECT COUNT(*) AS total FROM player_game_stats WHERE game_id = ?",
            (game_id,),
        ).fetchone()["total"]
        assert team_stats == 2
        assert player_stats >= 2

    # Simulating again should fail because games are already marked as played.
    second = api_client.post("/simulate-week", json={"week": 1})
    assert second.status_code == 400
    assert "already simulated" in second.json()["detail"]

