from __future__ import annotations

from fastapi.testclient import TestClient


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
    response = api_client.post("/trades/propose", json=trade_payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "rejected"
    assert "Team" in body["message"]

