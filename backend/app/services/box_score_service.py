from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from fastapi import HTTPException


class BoxScoreService:
    """Build box score payloads matching the frontend summary expectations."""

    def box_scores(
        self,
        connection,
        *,
        week: int | None = None,
        team_id: int | None = None,
    ) -> list[dict[str, Any]]:
        game_rows = self._load_games(connection, week=week, team_id=team_id)
        if not game_rows:
            return []
        return [self._assemble_payload(connection, game_row) for game_row in game_rows]

    def box_score(self, connection, game_id: int) -> dict[str, Any]:
        game_row = connection.execute(
            """
            SELECT
                g.id,
                g.week,
                g.played_at,
                g.home_team_id,
                g.away_team_id,
                g.home_score,
                g.away_score,
                ht.name AS home_name,
                ht.abbreviation AS home_abbr,
                at.name AS away_name,
                at.abbreviation AS away_abbr
            FROM games AS g
            JOIN teams AS ht ON ht.id = g.home_team_id
            JOIN teams AS at ON at.id = g.away_team_id
            WHERE g.id = ?
            """,
            (game_id,),
        ).fetchone()
        if game_row is None:
            raise HTTPException(status_code=404, detail="Game not found")
        return self._assemble_payload(connection, game_row)

    # Internal helpers -------------------------------------------------

    def _load_games(self, connection, *, week: int | None, team_id: int | None):
        params: list[Any] = []
        clauses: list[str] = []

        if week is None:
            row = connection.execute(
                """
                SELECT week
                FROM games
                WHERE played_at IS NOT NULL
                ORDER BY week DESC
                LIMIT 1
                """,
            ).fetchone()
            if row is None:
                return []
            target_week = row["week"]
        else:
            target_week = week

        params.append(target_week)
        clauses.append("g.week = ?")

        if team_id is not None:
            clauses.append("(g.home_team_id = ? OR g.away_team_id = ?)")
            params.extend([team_id, team_id])

        sql = "\n".join(
            [
                "SELECT",
                "    g.id,",
                "    g.week,",
                "    g.played_at,",
                "    g.home_team_id,",
                "    g.away_team_id,",
                "    g.home_score,",
                "    g.away_score,",
                "    ht.name AS home_name,",
                "    ht.abbreviation AS home_abbr,",
                "    at.name AS away_name,",
                "    at.abbreviation AS away_abbr",
                "FROM games AS g",
                "JOIN teams AS ht ON ht.id = g.home_team_id",
                "JOIN teams AS at ON at.id = g.away_team_id",
                "WHERE " + " AND ".join(clauses),
                "ORDER BY g.week DESC, g.id",
            ]
        )

        return connection.execute(sql, params).fetchall()

    def _assemble_payload(self, connection, game_row) -> dict[str, Any]:
        home_totals, away_totals = self._team_totals(connection, game_row["id"], game_row)
        player_stats = self._player_stats(connection, game_row["id"])
        key_players = self._select_key_players(player_stats)
        plays = self._game_events(connection, game_row["id"])

        home_payload = {
            "teamId": game_row["home_team_id"],
            "name": game_row["home_name"],
            "points": game_row["home_score"],
            "yards": home_totals["yards"],
            "turnovers": home_totals["turnovers"],
        }
        away_payload = {
            "teamId": game_row["away_team_id"],
            "name": game_row["away_name"],
            "points": game_row["away_score"],
            "yards": away_totals["yards"],
            "turnovers": away_totals["turnovers"],
        }

        return {
            "gameId": game_row["id"],
            "week": game_row["week"],
            "homeTeam": home_payload,
            "awayTeam": away_payload,
            "keyPlayers": key_players,
            "plays": plays,
        }

    def _team_totals(self, connection, game_id: int, game_row) -> tuple[dict[str, int], dict[str, int]]:
        rows = connection.execute(
            """
            SELECT team_id, total_yards, turnovers
            FROM team_game_stats
            WHERE game_id = ?
            """,
            (game_id,),
        ).fetchall()

        lookup = {row["team_id"]: {"yards": row["total_yards"], "turnovers": row["turnovers"]} for row in rows}
        home = lookup.get(game_row["home_team_id"], {"yards": 0, "turnovers": 0})
        away = lookup.get(game_row["away_team_id"], {"yards": 0, "turnovers": 0})
        return home, away

    def _player_stats(self, connection, game_id: int) -> dict[int, list[dict[str, Any]]]:
        rows = connection.execute(
            """
            SELECT
                pgs.player_id,
                pgs.team_id,
                p.name,
                p.position,
                pgs.passing_yards,
                pgs.passing_tds,
                pgs.interceptions,
                pgs.rushing_yards,
                pgs.rushing_tds,
                pgs.receiving_yards,
                pgs.receiving_tds,
                pgs.tackles,
                pgs.sacks,
                pgs.forced_turnovers
            FROM player_game_stats AS pgs
            JOIN players AS p ON p.id = pgs.player_id
            WHERE pgs.game_id = ?
            ORDER BY pgs.team_id, p.position, pgs.player_id
            """,
            (game_id,),
        ).fetchall()

        groups: dict[int, list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            stat_line, weight = self._format_stat_line(row)
            groups[row["team_id"]].append(
                {
                    "playerId": row["player_id"],
                    "teamId": row["team_id"],
                    "name": row["name"],
                    "position": row["position"],
                    "statLine": stat_line,
                    "_weight": weight,
                }
            )
        for players in groups.values():
            players.sort(key=lambda item: item["_weight"], reverse=True)
        return groups

    def _select_key_players(self, player_groups: dict[int, list[dict[str, Any]]]) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        for players in player_groups.values():
            selected.extend(players[:2])
        selected.sort(key=lambda item: item["_weight"], reverse=True)
        return [
            {
                "playerId": player["playerId"],
                "teamId": player["teamId"],
                "name": player["name"],
                "position": player["position"],
                "statLine": player["statLine"],
            }
            for player in selected[:4]
        ]

    def _game_events(self, connection, game_id: int) -> list[dict[str, Any]]:
        rows = connection.execute(
            """
            SELECT sequence, quarter, clock, description, home_score_after, away_score_after
            FROM game_events
            WHERE game_id = ?
            ORDER BY sequence
            """,
            (game_id,),
        ).fetchall()

        events: list[dict[str, Any]] = []
        for row in rows:
            events.append(
                {
                    "sequence": row["sequence"],
                    "quarter": row["quarter"],
                    "clock": row["clock"],
                    "description": row["description"],
                    "score": {
                        "home": row["home_score_after"],
                        "away": row["away_score_after"],
                    },
                }
            )
        return events

    def _format_stat_line(self, row) -> tuple[str, float]:
        parts: list[str] = []
        weight = 0.0
        passing_yards = row["passing_yards"]
        passing_tds = row["passing_tds"]
        interceptions = row["interceptions"]
        rushing_yards = row["rushing_yards"]
        rushing_tds = row["rushing_tds"]
        receiving_yards = row["receiving_yards"]
        receiving_tds = row["receiving_tds"]
        tackles = row["tackles"]
        sacks = row["sacks"]
        forced = row["forced_turnovers"]

        if passing_yards:
            parts.append(f"{passing_yards} PY")
            weight += passing_yards
        if passing_tds:
            parts.append(f"{passing_tds} PTD")
            weight += passing_tds * 40
        if interceptions:
            parts.append(f"{interceptions} INT")
            weight -= interceptions * 20
        if rushing_yards:
            parts.append(f"{rushing_yards} RY")
            weight += rushing_yards * 1.2
        if rushing_tds:
            parts.append(f"{rushing_tds} RTD")
            weight += rushing_tds * 40
        if receiving_yards:
            parts.append(f"{receiving_yards} RecY")
            weight += receiving_yards
        if receiving_tds:
            parts.append(f"{receiving_tds} RecTD")
            weight += receiving_tds * 40
        if tackles:
            parts.append(f"{tackles} TKL")
            weight += tackles * 5
        if sacks:
            parts.append(f"{sacks} SCK")
            weight += sacks * 25
        if forced:
            parts.append(f"{forced} TO")
            weight += forced * 35

        if not parts:
            parts.append("No impact stats recorded")
        return ", ".join(parts), weight

    def _game_events(self, connection, game_id: int) -> list[dict[str, Any]]:
        rows = connection.execute(
            """
            SELECT
                sequence,
                quarter,
                clock,
                team_id,
                player_id,
                description,
                highlight_type,
                impact,
                points,
                home_score_after,
                away_score_after
            FROM game_events
            WHERE game_id = ?
            ORDER BY sequence
            """,
            (game_id,),
        ).fetchall()

        plays: list[dict[str, Any]] = []
        for row in rows:
            plays.append(
                {
                    "sequence": row["sequence"],
                    "quarter": row["quarter"],
                    "clock": row["clock"],
                    "teamId": row["team_id"],
                    "playerId": row["player_id"],
                    "description": row["description"],
                    "type": row["highlight_type"],
                    "impact": row["impact"],
                    "points": row["points"],
                    "score": {
                        "home": row["home_score_after"],
                        "away": row["away_score_after"],
                    },
                }
            )
        return plays


