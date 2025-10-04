from __future__ import annotations

import os
import sqlite3
from typing import Any, Dict, Iterable, Optional

from fastapi.testclient import TestClient
from typing import Any, Dict, Iterable, Optional


def _k(d: Dict[str, Any], *keys: str, default=None):
    for k in keys:
        if k in d:
            return d[k]
    return default


def _json(client: TestClient, path: str) -> Dict[str, Any]:
    response = client.get(path)
    assert response.status_code == 200, f"GET {path} failed: {response.text}"
    return response.json()

from shared.utils.rules import load_game_rules


def _k(d: Dict[str, Any], *keys: str, default=None):
    for key in keys:
        if key in d:
            return d[key]
    return default


def _json(client: TestClient, path: str) -> Dict[str, Any]:
    response = client.get(path)
    assert response.status_code == 200, f"GET {path} failed: {response.text}"
    return response.json()

from shared.utils.rules import load_game_rules


def _team_id(client: TestClient, abbr: str) -> int:
    teams = _json(client, "/teams")
    for team in teams:
        if _k(team, "abbreviation", "abbr") == abbr:
            return int(_k(team, "id", "teamId"))
    raise AssertionError(f"Team {abbr} not found")


def _roster(client: TestClient, team_id: int) -> Iterable[Dict[str, Any]]:
    team_data = _json(client, f"/teams/{team_id}")
    roster = _k(team_data, "roster", "players")
    assert isinstance(roster, list), f"Unexpected team payload: {team_data}"
    return roster


def _roster_player_ids(client: TestClient, team_id: int) -> set[int]:
    return {int(_k(player, "id", "playerId")) for player in _roster(client, team_id)}


def _player_id(
    client: TestClient,
    team_id: int,
    name: str,
    position: Optional[str] = None,
) -> int:
    matches = [
        player
        for player in _roster(client, team_id)
        if _k(player, "name", "playerName") == name
        and (position is None or _k(player, "position", "pos") == position)
    ]
    if not matches:
        raise AssertionError(
            f"Player {name} (pos={position}) not found on team {team_id}"
        )
    if len(matches) > 1:
        raise AssertionError(
            f"Player {name} is ambiguous on team {team_id}; pass position=..."
        )
    return int(_k(matches[0], "id", "playerId"))


def _roster_size(client: TestClient, team_id: int) -> int:
    return len(list(_roster(client, team_id)))


def _free_agent_id_by_name(
    client: TestClient, name: str, position: Optional[str] = None
) -> tuple[int, Dict[str, Any]]:
    payload = _json(client, "/free-agents")
    players = _k(payload, "players", "freeAgents", default=[])
    matches = [
        player
        for player in players
        if _k(player, "name", "playerName") == name
        and (position is None or _k(player, "position", "pos") == position)
    ]
    assert matches, f"Free agent {name} (pos={position}) not found"
    if len(matches) > 1:
        raise AssertionError(
            f"Free agent {name} is ambiguous; pass position=..."
        )
    player = matches[0]
    return int(_k(player, "id", "playerId")), player


def _db_connection() -> sqlite3.Connection:
    path = os.environ["NFL_GM_DB_PATH"]
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def _db_connection() -> sqlite3.Connection:
    path = os.environ["NFL_GM_DB_PATH"]
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def test_trade_swaps_players_and_updates_rosters(api_client: TestClient) -> None:
    buf_id = _team_id(api_client, "BUF")
    cin_id = _team_id(api_client, "CIN")

    allen_id = _player_id(api_client, buf_id, "Josh Allen", position="QB")
    burrow_id = _player_id(api_client, cin_id, "Joe Burrow", position="QB")
    diggs_id = _player_id(api_client, buf_id, "Stefon Diggs", position="WR")

    assert allen_id in _roster_player_ids(api_client, buf_id), "BUF should already roster Josh Allen"

    julio_rating = float(_k(julio_payload, "overall", "rating", default=75))
    buf_roster = list(_roster(api_client, buf_id))
    offer_player = min(
        buf_roster,
        key=lambda player: abs(float(_k(player, "overall", "rating", default=70)) - julio_rating),
    )
    offer_id = int(_k(offer_player, "id", "playerId"))

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


def test_trade_preserves_combined_roster_sizes(api_client: TestClient) -> None:
    buf_id = _team_id(api_client, "BUF")
    cin_id = _team_id(api_client, "CIN")

    julio_id = _free_agent_id_by_name(api_client, "Julio Jones", position="WR")
    sign_response = api_client.post(
        "/free-agents/sign",
        json={"teamId": cin_id, "playerId": julio_id},
    )
    assert sign_response.status_code == 200

    total_before = _roster_size(api_client, buf_id) + _roster_size(api_client, cin_id)

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

    total_after = _roster_size(api_client, buf_id) + _roster_size(api_client, cin_id)
    assert total_after == total_before
