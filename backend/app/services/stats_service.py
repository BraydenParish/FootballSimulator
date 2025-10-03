from __future__ import annotations

from fastapi import HTTPException

from ..db import row_to_dict

STAT_FIELDS = (
    "passing_yards",
    "passing_tds",
    "interceptions",
    "rushing_yards",
    "rushing_tds",
    "receiving_yards",
    "receiving_tds",
    "tackles",
    "sacks",
    "forced_turnovers",
)


class TeamStatsService:
    """Aggregate season-to-date statistics for team starters."""

    def starters_stats(self, connection, team_id: int) -> dict:
        team = connection.execute(
            "SELECT id, name, abbreviation FROM teams WHERE id = ?",
            (team_id,),
        ).fetchone()
        if team is None:
            raise HTTPException(status_code=404, detail="Team not found")

        starters = connection.execute(
            """
            SELECT id, name, position, depth_chart_position
            FROM players
            WHERE team_id = ? AND status = 'active' AND COALESCE(depth_chart_order, 999) = 1
            ORDER BY position, name
            """,
            (team_id,),
        ).fetchall()

        aggregates = self._player_aggregates(connection, team_id)

        starter_payload: list[dict] = []
        for starter in starters:
            stats = aggregates.get(starter["id"], {})
            games_played = int(stats.get("games_played", 0) or 0)
            totals = {field: float(stats.get(field, 0) or 0) for field in STAT_FIELDS}
            per_game = {
                field: round(value / games_played, 2) if games_played else 0.0
                for field, value in totals.items()
            }

            starter_payload.append(
                {
                    "player_id": starter["id"],
                    "name": starter["name"],
                    "position": starter["position"],
                    "depth_chart_position": starter["depth_chart_position"],
                    "games_played": games_played,
                    "totals": totals,
                    "per_game": per_game,
                }
            )

        return {"team": row_to_dict(team), "starters": starter_payload}

    def _player_aggregates(self, connection, team_id: int) -> dict[int, dict]:
        rows = connection.execute(
            """
            SELECT
                player_id,
                COUNT(DISTINCT game_id) AS games_played,
                SUM(passing_yards) AS passing_yards,
                SUM(passing_tds) AS passing_tds,
                SUM(interceptions) AS interceptions,
                SUM(rushing_yards) AS rushing_yards,
                SUM(rushing_tds) AS rushing_tds,
                SUM(receiving_yards) AS receiving_yards,
                SUM(receiving_tds) AS receiving_tds,
                SUM(tackles) AS tackles,
                SUM(sacks) AS sacks,
                SUM(forced_turnovers) AS forced_turnovers
            FROM player_game_stats
            WHERE team_id = ?
            GROUP BY player_id
            """,
            (team_id,),
        ).fetchall()

        aggregates: dict[int, dict] = {}
        for row in rows:
            aggregates[row["player_id"]] = {key: row[key] for key in row.keys()}
        return aggregates
