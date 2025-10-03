from __future__ import annotations

from fastapi.testclient import TestClient


def _get_team_id(client: TestClient, abbreviation: str) -> int:
    response = client.get("/teams")
    response.raise_for_status()
    for team in response.json():
        if team["abbreviation"] == abbreviation:
            return team["id"]
    raise AssertionError(f"Team {abbreviation} not found in response")


def test_free_agents_list_current_year(api_client: TestClient) -> None:
    response = api_client.get("/free-agents")
    assert response.status_code == 200
    payload = response.json()
    assert payload["year"] == 2025
    players = payload["players"]
    assert len(players) == 25
    assert all(player["name"].startswith("Free Agent 2025-") for player in players[:3])
    assert all(player["free_agent_year"] == 2025 for player in players)


def test_sign_free_agent_moves_player(api_client: TestClient) -> None:
    team_id = _get_team_id(api_client, "BUF")
    free_agents = api_client.get("/free-agents").json()["players"]
    player_id = free_agents[0]["id"]

    response = api_client.post(f"/teams/{team_id}/sign", json={"player_id": player_id})
    assert response.status_code == 200
    signed = response.json()["player"]
    assert signed["team_id"] == team_id
    assert signed["status"] == "active"

    # Player should no longer be in free agent pool
    updated_agents = api_client.get("/free-agents").json()["players"]
    assert all(agent["id"] != player_id for agent in updated_agents)

    # Signing again should fail because player is no longer a free agent
    repeat_response = api_client.post(
        f"/teams/{team_id}/sign", json={"player_id": player_id}
    )
    assert repeat_response.status_code == 404
    assert repeat_response.json()["detail"] == "Free agent not found"

