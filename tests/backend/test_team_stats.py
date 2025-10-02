from __future__ import annotations

from fastapi.testclient import TestClient


def _team_id(client: TestClient, abbreviation: str) -> int:
    response = client.get("/teams")
    response.raise_for_status()
    for team in response.json():
        if team["abbreviation"] == abbreviation:
            return team["id"]
    raise AssertionError(f"Team {abbreviation} not found")


def test_team_stats_returns_starter_aggregates(api_client: TestClient) -> None:
    buf_id = _team_id(api_client, "BUF")

    sim_response = api_client.post("/simulate-week", json={"week": 1})
    assert sim_response.status_code == 200

    stats_response = api_client.get(f"/teams/{buf_id}/stats")
    assert stats_response.status_code == 200
    payload = stats_response.json()
    assert payload["team"]["id"] == buf_id

    starters = payload["starters"]
    assert starters, "Expected starters to be returned"

    qb_stats = next((starter for starter in starters if starter["position"] == "QB"), None)
    assert qb_stats is not None
    assert qb_stats["games_played"] >= 1
    assert qb_stats["totals"]["passing_yards"] >= 0
    assert qb_stats["per_game"]["passing_yards"] >= 0

