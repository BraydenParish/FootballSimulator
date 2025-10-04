from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from fastapi import HTTPException

from ..db import row_to_dict
from .roster_service import RosterService
from shared.utils.rules import GameRules


@dataclass(slots=True)
class TradeResult:
    team_a: dict
    team_b: dict
    team_a_sent: dict
    team_a_received: dict
    team_b_sent: dict
    team_b_received: dict
    offer_value: float
    request_value: float
    value_delta: float


class TradeService:
    """Coordinates validating and executing player/draft pick trades."""

    _PICK_VALUE_BY_ROUND = {1: 20.0, 2: 12.0, 3: 7.0, 4: 4.0, 5: 2.5, 6: 1.5, 7: 1.0}

    def __init__(
        self,
        rules: GameRules,
        roster_service: RosterService,
        *,
        current_year: int = 2025,
        fairness_tolerance: float = 8.0,
    ) -> None:
        self.rules = rules
        self.roster_service = roster_service
        self.current_year = current_year
        self.fairness_tolerance = fairness_tolerance

    def execute_trade(
        self,
        connection,
        *,
        team_a_id: int,
        team_b_id: int,
        offer: list[dict],
        request: list[dict],
    ) -> TradeResult:
        if team_a_id == team_b_id:
            raise HTTPException(status_code=400, detail="Teams must be different for a trade")

        team_a = self._get_team(connection, team_a_id)
        team_b = self._get_team(connection, team_b_id)

        offer_assets = self._gather_assets(connection, team_a_id, offer)
        request_assets = self._gather_assets(connection, team_b_id, request)

        offer_player_ids = [player["id"] for player in offer_assets["players"]]
        request_player_ids = [player["id"] for player in request_assets["players"]]
        offer_pick_ids = [pick["id"] for pick in offer_assets["picks"]]
        request_pick_ids = [pick["id"] for pick in request_assets["picks"]]

        team_a_sent_players = [row_to_dict(player) for player in offer_assets["players"]]
        team_b_sent_players = [row_to_dict(player) for player in request_assets["players"]]
        team_a_sent_picks = [row_to_dict(pick) for pick in offer_assets["picks"]]
        team_b_sent_picks = [row_to_dict(pick) for pick in request_assets["picks"]]

        self._validate_roster_sizes(
            connection,
            team_a_id,
            team_b_id,
            offer_assets,
            request_assets,
            team_a,
            team_b,
        )
        self._validate_salary_caps(connection, team_a_id, team_b_id, offer_assets, request_assets)

        try:
            self._apply_assets(connection, offer_assets, team_b_id)
            self._apply_assets(connection, request_assets, team_a_id)

            self._validate_depth(connection, team_a_id, team_b_id)
            self._validate_elite_qbs(connection, (team_a_id, team_b_id))
        except Exception:
            connection.rollback()
            raise

        team_a_received = {
            "players": self._fetch_players_by_ids(connection, request_player_ids),
            "picks": self._fetch_picks_by_ids(connection, request_pick_ids),
        }
        team_b_received = {
            "players": self._fetch_players_by_ids(connection, offer_player_ids),
            "picks": self._fetch_picks_by_ids(connection, offer_pick_ids),
        }

        team_a_sent = {"players": team_a_sent_players, "picks": team_a_sent_picks}
        team_b_sent = {"players": team_b_sent_players, "picks": team_b_sent_picks}

        value_delta = request_value - offer_value

        return TradeResult(
            team_a=row_to_dict(team_a),
            team_b=row_to_dict(team_b),
            team_a_sent=team_a_sent,
            team_a_received=team_a_received,
            team_b_sent=team_b_sent,
            team_b_received=team_b_received,
            offer_value=offer_value,
            request_value=request_value,
            value_delta=value_delta,
        )

    def _apply_assets(self, connection, assets: dict[str, list], destination_team_id: int) -> None:
        for player in assets["players"]:
            order, label = self.roster_service.next_depth_slot(
                connection, destination_team_id, player["position"]
            )
            connection.execute(
                """
                UPDATE players
                SET team_id = ?,
                    status = 'active',
                    depth_chart_order = ?,
                    depth_chart_position = ?,
                    free_agent_year = NULL
                WHERE id = ?
                """,
                (destination_team_id, order, label, player["id"]),
            )

        for pick in assets["picks"]:
            connection.execute(
                """
                UPDATE draft_picks
                SET team_id = ?
                WHERE id = ?
                """,
                (destination_team_id, pick["id"]),
            )

    def _gather_assets(self, connection, team_id: int, assets: Iterable[dict]) -> dict[str, list]:
        players = []
        picks = []

        for asset in assets:
            asset_type = asset.get("type")
            if asset_type == "player":
                player_id = asset.get("player_id") or asset.get("playerId")
                if player_id is None:
                    raise HTTPException(status_code=400, detail="Player asset missing player_id")
                player = connection.execute(
                    "SELECT * FROM players WHERE id = ? AND team_id = ?",
                    (player_id, team_id),
                ).fetchone()
                if player is None:
                    raise HTTPException(status_code=404, detail=f"Player {player_id} not on team {team_id}")
                players.append(player)
            elif asset_type == "pick":
                year = asset.get("year")
                draft_round = asset.get("round") or asset.get("draft_round")
                if year is None or draft_round is None:
                    raise HTTPException(status_code=400, detail="Pick asset missing year or round")
                pick = connection.execute(
                    """
                    SELECT * FROM draft_picks
                    WHERE team_id = ? AND year = ? AND round = ?
                    """,
                    (team_id, year, draft_round),
                ).fetchone()
                if pick is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Team {team_id} does not own {year} round {draft_round} pick",
                    )
                picks.append(pick)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported asset type: {asset_type}")

        return {"players": players, "picks": picks}

    def _trade_value(self, assets: dict[str, list]) -> float:
        player_value = sum(player["overall_rating"] for player in assets["players"])
        pick_value = sum(self._pick_value(pick) for pick in assets["picks"])
        return float(player_value + pick_value)

    def _pick_value(self, pick_row) -> float:
        round_value = self._PICK_VALUE_BY_ROUND.get(int(pick_row["round"]), 0.5)
        years_out = max(0, int(pick_row["year"]) - self.current_year)
        decay = 0.85 ** years_out
        return round_value * decay

    def _validate_fairness(self, offer_value: float, request_value: float) -> None:
        gap = abs(request_value - offer_value)
        if gap > self.fairness_tolerance:
            direction = "more" if request_value > offer_value else "less"
            raise HTTPException(
                status_code=400,
                detail=(
                    "Trade rejected: value gap is too large. "
                    f"Team A would send {gap:.1f} {direction} value than it receives."
                ),
            )

    def _fetch_players_by_ids(self, connection, player_ids: Iterable[int]) -> list[dict]:
        ids = list(player_ids)
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        rows = connection.execute(
            f"SELECT * FROM players WHERE id IN ({placeholders})",
            ids,
        ).fetchall()
        lookup = {row["id"]: row_to_dict(row) for row in rows}
        return [lookup[player_id] for player_id in ids if player_id in lookup]

    def _fetch_picks_by_ids(self, connection, pick_ids: Iterable[int]) -> list[dict]:
        ids = list(pick_ids)
        if not ids:
            return []
        placeholders = ",".join("?" for _ in ids)
        rows = connection.execute(
            f"SELECT * FROM draft_picks WHERE id IN ({placeholders})",
            ids,
        ).fetchall()
        lookup = {row["id"]: row_to_dict(row) for row in rows}
        return [lookup[pick_id] for pick_id in ids if pick_id in lookup]

    def _get_team(self, connection, team_id: int):
        team = connection.execute(
            "SELECT id, name, abbreviation FROM teams WHERE id = ?",
            (team_id,),
        ).fetchone()
        if team is None:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
        return team

    def _validate_roster_sizes(
        self,
        connection,
        team_a_id: int,
        team_b_id: int,
        offer_assets: dict[str, list],
        request_assets: dict[str, list],
        team_a,
        team_b,
    ) -> None:
        team_a_total = self.roster_service.roster_size(connection, team_a_id)
        team_b_total = self.roster_service.roster_size(connection, team_b_id)

        team_a_after = team_a_total - len(offer_assets["players"]) + len(request_assets["players"])
        team_b_after = team_b_total - len(request_assets["players"]) + len(offer_assets["players"])

        if team_a_after > self.rules.roster_max and team_a_after > team_a_total:
            raise HTTPException(
                status_code=400,
                detail=f"{team_a['name']} would exceed the roster limit",
            )
        if team_b_after > self.rules.roster_max and team_b_after > team_b_total:
            raise HTTPException(
                status_code=400,
                detail=f"{team_b['name']} would exceed the roster limit",
            )
        if team_a_after < self.rules.roster_min and team_a_after < team_a_total:
            raise HTTPException(
                status_code=400,
                detail=f"{team_a['name']} would fall below the roster minimum",
            )
        if team_b_after < self.rules.roster_min and team_b_after < team_b_total:
            raise HTTPException(
                status_code=400,
                detail=f"{team_b['name']} would fall below the roster minimum",
            )

    def _validate_salary_caps(
        self,
        connection,
        team_a_id: int,
        team_b_id: int,
        offer_assets: dict[str, list],
        request_assets: dict[str, list],
    ) -> None:
        def cap_total(team_id: int) -> int:
            row = connection.execute(
                "SELECT COALESCE(SUM(salary), 0) AS cap FROM players WHERE team_id = ? AND status = 'active'",
                (team_id,),
            ).fetchone()
            return row["cap"] if row else 0

        team_a_cap = cap_total(team_a_id)
        team_b_cap = cap_total(team_b_id)

        team_a_out = sum(player["salary"] for player in offer_assets["players"])
        team_b_out = sum(player["salary"] for player in request_assets["players"])

        team_a_in = sum(player["salary"] for player in request_assets["players"])
        team_b_in = sum(player["salary"] for player in offer_assets["players"])

        if (team_a_cap - team_a_out + team_a_in) > self.rules.salary_cap:
            raise HTTPException(status_code=400, detail="Team A would exceed salary cap")
        if (team_b_cap - team_b_out + team_b_in) > self.rules.salary_cap:
            raise HTTPException(status_code=400, detail="Team B would exceed salary cap")

    def _validate_depth(self, connection, team_a_id: int, team_b_id: int) -> None:
        for team_id in (team_a_id, team_b_id):
            self.roster_service.validate_depth_requirements(connection, team_id)

    def _validate_elite_qbs(self, connection, team_ids: Iterable[int]) -> None:
        for team_id in team_ids:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM players
                WHERE team_id = ? AND position = 'QB' AND overall_rating >= ?
                """,
                (team_id, self.rules.elite_qb_rating),
            ).fetchone()
            if row and row["total"] > self.rules.max_elite_qbs:
                raise HTTPException(
                    status_code=400,
                    detail=f"Team {team_id} would exceed elite QB limit",
                )

