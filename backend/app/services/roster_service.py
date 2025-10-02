from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from fastapi import HTTPException

from ..db import row_to_dict
from shared.utils.rules import GameRules


@dataclass(slots=True)
class SignResult:
    player: dict
    team: dict


class RosterService:
    """Roster management helpers for free agents and depth chart maintenance."""

    def __init__(self, rules: GameRules) -> None:
        self.rules = rules

    def list_free_agents(self, connection, *, year: int | None = None) -> list[dict]:
        params: list[object] = ['free_agent']
        where: list[str] = ["status = ?"]

        if year is not None:
            where.append("(free_agent_year IS NULL OR free_agent_year = ?)")
            params.append(year)

        sql = "\n".join(
            [
                "SELECT id, name, position, overall_rating, age, salary, free_agent_year",
                "FROM players",
                "WHERE " + " AND ".join(where),
                "ORDER BY overall_rating DESC, name",
            ]
        )

        rows = connection.execute(sql, params).fetchall()
        return [row_to_dict(row) for row in rows]

    def sign_player(self, connection, *, team_id: int, player_id: int) -> SignResult:
        team_row = connection.execute(
            "SELECT id, name, abbreviation FROM teams WHERE id = ?",
            (team_id,),
        ).fetchone()
        if team_row is None:
            raise HTTPException(status_code=404, detail="Team not found")

        player_row = connection.execute(
            """
            SELECT id, name, position, overall_rating, salary, free_agent_year
            FROM players
            WHERE id = ? AND status = 'free_agent'
            """,
            (player_id,),
        ).fetchone()
        if player_row is None:
            raise HTTPException(status_code=404, detail="Free agent not found")

        roster_count = connection.execute(
            "SELECT COUNT(*) AS total FROM players WHERE team_id = ? AND status = 'active'",
            (team_id,),
        ).fetchone()["total"]
        if roster_count >= self.rules.roster_max:
            raise HTTPException(status_code=400, detail="Roster limit reached")

        current_cap = connection.execute(
            "SELECT COALESCE(SUM(salary), 0) AS cap FROM players WHERE team_id = ? AND status = 'active'",
            (team_id,),
        ).fetchone()["cap"]
        projected_cap = current_cap + player_row["salary"]
        if projected_cap > self.rules.salary_cap:
            raise HTTPException(status_code=400, detail="Signing would exceed salary cap")

        depth_order, depth_label = self.next_depth_slot(
            connection, team_id, player_row["position"]
        )

        connection.execute(
            """
            UPDATE players
            SET team_id = ?,
                status = 'active',
                free_agent_year = NULL,
                depth_chart_order = ?,
                depth_chart_position = ?,
                contract_years = ?
            WHERE id = ?
            """,
            (
                team_id,
                depth_order,
                depth_label,
                self.rules.max_contract_years,
                player_id,
            ),
        )

        signed_player = connection.execute(
            "SELECT * FROM players WHERE id = ?",
            (player_id,),
        ).fetchone()

        return SignResult(player=row_to_dict(signed_player), team=row_to_dict(team_row))

    def next_depth_slot(self, connection, team_id: int, position: str) -> tuple[int, str]:
        order = self._next_depth_order(connection, team_id, position)
        label = f"{position}{order}"
        return order, label

    def _next_depth_order(self, connection, team_id: int, position: str) -> int:
        row = connection.execute(
            """
            SELECT COALESCE(MAX(depth_chart_order), 0) + 1 AS next_order
            FROM players
            WHERE team_id = ? AND position = ?
            """,
            (team_id, position),
        ).fetchone()
        next_order = row["next_order"] if row else 1
        return max(1, int(next_order))

    def validate_depth_requirements(self, connection, team_id: int) -> None:
        """Ensure minimum depth chart counts after roster moves."""

        for position, minimum in self.rules.min_position_depth.items():
            total = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM players
                WHERE team_id = ? AND status = 'active' AND UPPER(position) = ?
                """,
                (team_id, position.upper()),
            ).fetchone()["total"]
            if total < minimum:
                raise HTTPException(
                    status_code=400,
                    detail=f"Team would fall below required depth at {position}",
                )


def ensure_depth_after_moves(connection, service: RosterService, team_ids: Iterable[int]) -> None:
    """Utility to re-check roster depth after a transaction."""

    for team_id in team_ids:
        service.validate_depth_requirements(connection, team_id)

