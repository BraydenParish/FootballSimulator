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

    free_agent = api_client.get("/free-agents").json()["players"][0]
    offer_player = api_client.get(f"/teams/{buf_id}").json()["roster"][0]

    # Sign the top free agent to Cincinnati so they have an asset to trade back.
    sign_response = api_client.post(
        f"/teams/{cin_id}/sign", json={"player_id": free_agent["id"]}
    )
    assert sign_response.status_code == 200

    trade_payload = {
        "teamA": buf_id,
        "teamB": cin_id,
        "offer": [{"type": "player", "player_id": offer_player["id"]}],
        "request": [{"type": "player", "player_id": free_agent["id"]}],
    }
    trade_response = api_client.post("/trade", json=trade_payload)
    assert trade_response.status_code == 200, trade_response.text
    trade_body = trade_response.json()

    assert any(
        player["id"] == free_agent["id"]
        for player in trade_body["teamA_received"]["players"]
    )
    assert any(
        player["id"] == offer_player["id"]
        for player in trade_body["teamB_received"]["players"]
    )

    buf_roster = _roster_player_ids(api_client, buf_id)
    cin_roster = _roster_player_ids(api_client, cin_id)
    assert free_agent["id"] in buf_roster
    assert offer_player["id"] not in buf_roster
    assert offer_player["id"] in cin_roster


def test_trade_rejects_players_not_on_roster(api_client: TestClient) -> None:
    buf_id = _team_id(api_client, "BUF")
    cin_id = _team_id(api_client, "CIN")

    trade_payload = {
        "teamA": buf_id,
        "teamB": cin_id,
        "offer": [{"type": "player", "player_id": 999999}],
        "request": [{"type": "player", "player_id": 888888}],
    }
    response = api_client.post("/trade", json=trade_payload)
    assert response.status_code == 404
    assert "not on team" in response.json()["detail"]

