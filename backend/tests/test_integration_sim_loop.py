"""Integration tests for the end-to-end simulation loop."""

from __future__ import annotations

import pytest


@pytest.mark.integration
def test_simulation_flow_across_weeks(api_client, db_connection):
    # Ensure a week two matchup exists so we can simulate back-to-back weeks.
    db_connection.execute(
        """
        INSERT INTO games (id, week, home_team_id, away_team_id, home_score, away_score, played_at)
        VALUES (?, ?, ?, ?, 0, 0, NULL)
        """,
        (2, 2, 2, 1),
    )
    db_connection.commit()

    first_week = api_client.post("/simulate-week", json={"week": 1, "mode": "quick"})
    assert first_week.status_code == 200
    first_payload = first_week.json()
    assert first_payload["week"] == 1
    assert first_payload["summaries"], "Expected week one summaries to be generated"

    week_one_results = api_client.get("/games/week/1").json()
    assert week_one_results, "Week one results should be available after simulation"
    for result in week_one_results:
        assert result["homeTeam"]["points"] >= 0
        assert result["awayTeam"]["points"] >= 0

    second_week = api_client.post("/simulate-week", json={"week": 2, "mode": "quick"})
    assert second_week.status_code == 200
    second_payload = second_week.json()
    assert second_payload["week"] == 2
    assert second_payload["summaries"], "Expected week two summaries to be generated"

    week_two_results = api_client.get("/games/week/2").json()
    assert week_two_results, "Week two results should be available after simulation"
    for result in week_two_results:
        assert result["homeTeam"]["points"] >= 0
        assert result["awayTeam"]["points"] >= 0

    # No negative yardage or impossible stats recorded in player box scores.
    player_stats = db_connection.execute(
        """
        SELECT passing_yards, rushing_yards, receiving_yards, tackles, sacks, forced_turnovers
        FROM player_game_stats
        """
    ).fetchall()
    assert player_stats, "Simulation should record player stats across games"
    for line in player_stats:
        assert line["passing_yards"] >= 0
        assert line["rushing_yards"] >= 0
        assert line["receiving_yards"] >= 0
        assert line["tackles"] >= 0
        assert line["sacks"] >= 0
        assert line["forced_turnovers"] >= 0

    team_stats = db_connection.execute(
        "SELECT total_yards, turnovers FROM team_game_stats"
    ).fetchall()
    assert team_stats, "Team totals should be recorded for each simulated game"
    for totals in team_stats:
        assert totals["total_yards"] >= 0
        assert totals["turnovers"] >= 0

    completed_weeks = db_connection.execute(
        "SELECT COUNT(DISTINCT week) AS weeks FROM games WHERE played_at IS NOT NULL"
    ).fetchone()["weeks"]
    assert completed_weeks >= 2, "State should persist across multiple simulated weeks"

