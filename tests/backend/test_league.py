from fastapi.testclient import TestClient


def test_week_box_scores_and_standings(api_client: TestClient) -> None:
    simulation = api_client.post("/simulate-week", json={"week": 1})
    assert simulation.status_code == 200
    sim_payload = simulation.json()
    summary_count = len(sim_payload["summaries"])

    week_box_scores = api_client.get("/games/week/1")
    assert week_box_scores.status_code == 200
    weekly = week_box_scores.json()
    assert isinstance(weekly, list)
    assert len(weekly) == summary_count

    standings_response = api_client.get("/standings")
    assert standings_response.status_code == 200
    standings = standings_response.json()

    assert standings["updatedThroughWeek"] >= 1
    assert len(standings["divisions"]) > 0
    assert len(standings["teams"]) > 0

    total_results = sum(
        entry["wins"] + entry["losses"] + entry["ties"] for entry in standings["teams"]
    )
    assert total_results > 0
    first_division = standings["divisions"][0]
    assert "conference" in first_division and "teams" in first_division
    assert len(first_division["teams"]) >= 1
