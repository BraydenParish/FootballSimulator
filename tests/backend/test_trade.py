from __future__ import annotations

import os
import sqlite3

from fastapi.testclient import TestClient

from shared.utils.rules import load_game_rules


def _team_id(client: TestClient, abbr: str) -> int:
    response = client.get("/teams")
    response.raise_for_status()
    for team in response.json():
        if team["abbreviation"] == abbr:
            return team["id"]
    raise AssertionError(f"Team {abbr} not found")


def _roster_player_ids(client: TestClient, team_id: int) -> set[int]:
    roster = client.get(f"/teams/{team_id}").json()["roster"]
    return {player["id"] for player in roster}


def _db_connection() -> sqlite3.Connection:
    path = os.environ["NFL_GM_DB_PATH"]
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def test_trade_swaps_players_and_updates_rosters(api_client: TestClient) -> None:
    buf_id = _team_id(api_client, "BUF")
    cin_id = _team_id(api_client, "CIN")

    free_agents = api_client.get("/free-agents").json()["players"]
    julio_id = next(player["id"] for player in free_agents if player["name"] == "Julio Jones")

    # Sign Julio Jones to Cincinnati so they have an asset to trade back.
    sign_response = api_client.post(
        "/free-agents/sign",
        json={"teamId": cin_id, "playerId": julio_id},
    )
    assert sign_response.status_code == 200

    trade_payload = {
        "teamA": buf_id,
        "teamB": cin_id,
        "offer": [{"type": "player", "playerId": 2}],
        "request": [{"type": "player", "playerId": julio_id}],
    }
    proposal = api_client.post("/trades/propose", json=trade_payload)
    assert proposal.status_code == 200
    assert proposal.json()["status"] == "accepted"

    trade_response = api_client.post("/trades/execute", json=trade_payload)
    assert trade_response.status_code == 200, trade_response.text
    trade_body = trade_response.json()

    assert any(player["id"] == julio_id for player in trade_body["teamA_received"]["players"])
    assert any(player["id"] == 2 for player in trade_body["teamB_received"]["players"])

    buf_roster = _roster_player_ids(api_client, buf_id)
    cin_roster = _roster_player_ids(api_client, cin_id)
    assert julio_id in buf_roster
    assert 2 not in buf_roster
    assert 2 in cin_roster


def test_trade_blocks_duplicate_elite_qbs(api_client: TestClient) -> None:
    buf_id = _team_id(api_client, "BUF")
    cin_id = _team_id(api_client, "CIN")

    trade_payload = {
        "teamA": buf_id,
        "teamB": cin_id,
        "offer": [{"type": "player", "playerId": 2}],
        "request": [{"type": "player", "playerId": 3}],
    }
    response = api_client.post("/trade", json=trade_payload)
    assert response.status_code == 400
    assert "elite qb" in response.json()["detail"].lower()


def test_trade_prevents_roster_overflow(api_client: TestClient) -> None:
    rules = load_game_rules()
    buf_id = _team_id(api_client, "BUF")
    cin_id = _team_id(api_client, "CIN")

    # Ensure Cincinnati hits the roster ceiling by adding depth players.
    current_roster = len(_roster_player_ids(api_client, cin_id))
    needed = max(0, rules.roster_max - current_roster)
    if needed:
        with _db_connection() as connection:
            max_id_row = connection.execute("SELECT MAX(id) AS max_id FROM players").fetchone()
            next_id = (max_id_row["max_id"] or 0) + 1
            for index in range(needed):
                connection.execute(
                    """
                    INSERT INTO players (
                        id,
                        name,
                        position,
                        overall_rating,
                        age,
                        team_id,
                        salary,
                        contract_years,
                        status
                    )
                    VALUES (?, ?, 'LB', 60, 24, ?, 1000000, 1, 'active')
                    """,
                    (
                        next_id + index,
                        f"Depth Reserve {index + 1}",
                        cin_id,
                    ),
                )
            connection.commit()

    assert len(_roster_player_ids(api_client, cin_id)) >= rules.roster_max

    buf_roster = api_client.get(f"/teams/{buf_id}").json()["roster"]
    cin_roster = api_client.get(f"/teams/{cin_id}").json()["roster"]

    offer_players = [buf_roster[0]["id"], buf_roster[1]["id"]]
    request_player = cin_roster[0]["id"]

    trade_payload = {
        "teamA": buf_id,
        "teamB": cin_id,
        "offer": [{"type": "player", "player_id": pid} for pid in offer_players],
        "request": [{"type": "player", "player_id": request_player}],
    }

    response = api_client.post("/trade", json=trade_payload)
    assert response.status_code == 400
    assert "roster limit" in response.json()["detail"].lower()

