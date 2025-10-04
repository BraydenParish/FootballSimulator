"""Integration tests covering roster management endpoints."""

from __future__ import annotations

import pytest

from shared.utils.rules import load_game_rules


@pytest.mark.integration
def test_sign_free_agent(api_client, db_connection):
    free_agents = api_client.get("/free-agents").json()["players"]
    assert free_agents, "Expected seeded free agent pool to be non-empty"

    target_agent = next(
        (agent for agent in free_agents if agent["status"] == "free-agent"),
        None,
    )
    assert target_agent is not None, "Seed data should expose at least one free agent"

    response = api_client.post(
        "/free-agents/sign",
        json={"teamId": 1, "playerId": target_agent["id"]},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "signed"
    assert payload["player"]["id"] == target_agent["id"]
    assert payload["player"]["teamId"] == 1

    player_row = db_connection.execute(
        "SELECT team_id, status, depth_chart_position FROM players WHERE id = ?",
        (target_agent["id"],),
    ).fetchone()
    assert player_row is not None
    assert player_row["team_id"] == 1
    assert player_row["status"] == "active"
    assert player_row["depth_chart_position"] is not None

    refreshed_pool = api_client.get("/free-agents").json()["players"]
    assert target_agent["id"] not in {agent["id"] for agent in refreshed_pool}

    team_roster = api_client.get("/teams/1").json()["roster"]
    assert any(player["id"] == target_agent["id"] for player in team_roster)


@pytest.mark.integration
def test_trade_proposal_and_execution(api_client, db_connection):
    proposal = {
        "teamA": 1,
        "teamB": 2,
        "offer": [
            {"type": "player", "playerId": 4},  # Von Miller
            {"type": "pick", "year": 2025, "round": 1},
        ],
        "request": [
            {"type": "player", "playerId": 7},  # Ja'Marr Chase
            {"type": "pick", "year": 2025, "round": 2},
        ],
    }

    preview = api_client.post("/trades/propose", json=proposal)
    assert preview.status_code == 200
    preview_payload = preview.json()
    assert preview_payload["status"] == "accepted"

    execution = api_client.post("/trades/execute", json=proposal)
    assert execution.status_code == 200
    execution_payload = execution.json()
    assert execution_payload["status"] == "accepted"

    chase_row = db_connection.execute(
        "SELECT team_id FROM players WHERE id = ?",
        (7,),
    ).fetchone()
    miller_row = db_connection.execute(
        "SELECT team_id FROM players WHERE id = ?",
        (4,),
    ).fetchone()
    assert chase_row is not None
    assert miller_row is not None
    assert chase_row["team_id"] == 1
    assert miller_row["team_id"] == 2

    round_one = db_connection.execute(
        "SELECT team_id FROM draft_picks WHERE year = 2025 AND round = 1",
    ).fetchone()
    round_two = db_connection.execute(
        "SELECT team_id FROM draft_picks WHERE year = 2025 AND round = 2",
    ).fetchone()
    assert round_one is not None
    assert round_two is not None
    assert round_one["team_id"] == 2
    assert round_two["team_id"] == 1

    rules = load_game_rules()
    for team_id in (1, 2):
        total_salary = db_connection.execute(
            "SELECT COALESCE(SUM(salary), 0) AS total FROM players WHERE team_id = ?",
            (team_id,),
        ).fetchone()["total"]
        assert total_salary <= rules.salary_cap


@pytest.mark.integration
def test_depth_chart_update(api_client, db_connection):
    depth_chart = api_client.get("/teams/1/depth-chart").json()["entries"]
    current_qb1 = next(entry for entry in depth_chart if entry["slot"] == "QB1")
    backup_qb = next(entry for entry in depth_chart if entry["slot"] == "QB2")

    swap_payload = {
        "entries": [
            {"slot": "QB1", "playerId": backup_qb["playerId"]},
            {"slot": "QB2", "playerId": current_qb1["playerId"]},
        ]
    }

    response = api_client.post("/teams/1/depth-chart", json=swap_payload)
    assert response.status_code == 200
    assert response.json()["updated"] == 2

    promoted = db_connection.execute(
        "SELECT depth_chart_position, depth_chart_order FROM players WHERE id = ?",
        (backup_qb["playerId"],),
    ).fetchone()
    demoted = db_connection.execute(
        "SELECT depth_chart_position, depth_chart_order FROM players WHERE id = ?",
        (current_qb1["playerId"],),
    ).fetchone()
    assert promoted is not None
    assert demoted is not None
    assert promoted["depth_chart_position"] == "QB1"
    assert promoted["depth_chart_order"] == 1
    assert demoted["depth_chart_position"] == "QB2"
    assert demoted["depth_chart_order"] == 2

    refreshed = api_client.get("/teams/1/depth-chart").json()["entries"]
    qb1_entry = next(entry for entry in refreshed if entry["slot"] == "QB1")
    qb2_entry = next(entry for entry in refreshed if entry["slot"] == "QB2")
    assert qb1_entry["playerId"] == backup_qb["playerId"]
    assert qb2_entry["playerId"] == current_qb1["playerId"]

