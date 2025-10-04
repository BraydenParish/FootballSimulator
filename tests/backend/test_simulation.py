from __future__ import annotations

import os
import sqlite3

from fastapi.testclient import TestClient


def _db_connection() -> sqlite3.Connection:
    path = os.environ["NFL_GM_DB_PATH"]
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def test_simulate_week_quick_mode(api_client: TestClient) -> None:
    response = api_client.post("/simulate-week", json={"week": 1})
    assert response.status_code == 200
    data = response.json()

    assert data["week"] == 1
    assert data["mode"] == "quick"
    assert len(data["summaries"]) >= 1
    assert len(data["games"]) >= 1
    assert isinstance(data["playByPlay"], list)

    first_summary = data["summaries"][0]
    assert "homeTeam" in first_summary and "awayTeam" in first_summary
    assert first_summary["homeTeam"]["points"] >= 0
    assert isinstance(first_summary["keyPlayers"], list)

    first_game = data["games"][0]
    assert "teamStats" in first_game and "playerStats" in first_game
    assert isinstance(first_game["injuries"], list)
    assert first_game["plays"] == []

    for stat_block in first_game["playerStats"]:
        for stat in stat_block.get("players", []):
            assert stat["passing_yards"] >= 0
            assert stat["rushing_yards"] >= 0
            assert stat["receiving_yards"] >= 0
            assert stat["passing_tds"] >= 0
            assert stat["rushing_tds"] >= 0
            assert stat["receiving_tds"] >= 0
            assert stat["sacks"] >= 0

    for injury in first_game["injuries"]:
        assert injury["duration_weeks"] >= 1
        assert injury["games_missed"] >= 0

    game_id = first_summary["gameId"]
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
        event_count = connection.execute(
            "SELECT COUNT(*) AS total FROM game_events WHERE game_id = ?",
            (game_id,),
        ).fetchone()["total"]
        assert team_stats == 2
        assert player_stats >= 2
        assert event_count == 0

    second = api_client.post("/simulate-week", json={"week": 1})
    assert second.status_code == 400
    assert "already simulated" in second.json()["detail"]


def test_simulate_week_detailed_mode_creates_play_log(api_client: TestClient) -> None:
    response = api_client.post("/simulate-week", json={"week": 1, "mode": "detailed"})
    assert response.status_code == 200

    data = response.json()
    assert data["mode"] == "detailed"
    assert len(data["summaries"]) >= 1
    assert len(data["playByPlay"]) > 0
    assert len(data["games"]) >= 1

    first_summary = data["summaries"][0]
    game_id = first_summary["gameId"]
    detailed_game = next(game for game in data["games"] if game["gameId"] == game_id)
    assert len(detailed_game["plays"]) > 0

    with _db_connection() as connection:
        event_rows = connection.execute(
            """
            SELECT sequence, home_score_after, away_score_after
            FROM game_events
            WHERE game_id = ?
            ORDER BY sequence
            """,
            (game_id,),
        ).fetchall()
        assert len(event_rows) > 0
        assert len(data["playByPlay"]) >= len(event_rows)

        last_event = event_rows[-1]
        assert last_event["home_score_after"] == first_summary["homeTeam"]["points"]
        assert last_event["away_score_after"] == first_summary["awayTeam"]["points"]
