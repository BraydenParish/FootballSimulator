from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Iterable, Sequence

from ..db import row_to_dict


class NarrativeService:
    """Derive and persist weekly league narratives from simulation outputs."""

    def record_week(self, connection, *, week: int, box_scores: Sequence[Any]) -> list[dict[str, Any]]:
        narratives = self._build_narratives(week, box_scores)
        connection.execute("DELETE FROM week_narratives WHERE week = ?", (week,))
        timestamp = datetime.now(UTC).isoformat(timespec="seconds")
        for order, narrative in enumerate(narratives, start=1):
            tags = ",".join(narrative.get("tags", [])) or None
            connection.execute(
                """
                INSERT INTO week_narratives (week, headline, body, game_id, tags, sequence, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    week,
                    narrative["headline"],
                    narrative.get("body"),
                    narrative.get("gameId"),
                    tags,
                    order,
                    timestamp,
                ),
            )
        return narratives

    def list_narratives(self, connection, week: int | None = None) -> list[dict[str, Any]]:
        params: list[Any] = []
        where: list[str] = []
        if week is not None:
            where.append("week = ?")
            params.append(week)

        sql_parts = [
            "SELECT id, week, headline, body, game_id, tags, sequence, created_at",
            "FROM week_narratives",
        ]
        if where:
            sql_parts.append("WHERE " + " AND ".join(where))
        sql_parts.append("ORDER BY week DESC, sequence ASC")
        rows = connection.execute("\n".join(sql_parts), params).fetchall()
        payload: list[dict[str, Any]] = []
        for row in rows:
            item = row_to_dict(row)
            tags_raw = item.get("tags")
            item["tags"] = tags_raw.split(",") if tags_raw else []
            payload.append(
                {
                    "id": item["id"],
                    "week": item["week"],
                    "headline": item["headline"],
                    "body": item.get("body"),
                    "gameId": item.get("game_id"),
                    "tags": item["tags"],
                    "createdAt": item["created_at"],
                }
            )
        return payload

    # Narrative heuristics --------------------------------------------

    def _build_narratives(self, week: int, box_scores: Sequence[Any]) -> list[dict[str, Any]]:
        if not box_scores:
            return []

        narratives: list[dict[str, Any]] = []
        blowout = max(box_scores, key=self._margin, default=None)
        if blowout and self._margin(blowout) >= 14:
            winner, loser = self._winner_loser(blowout)
            narratives.append(
                {
                    "gameId": blowout.game_id,
                    "headline": f"{winner['name']} rout {loser['name']} {winner['score']}-{loser['score']}",
                    "body": (
                        f"{winner['name']} dominated from start to finish, piling up {winner['total_yards']} yards "
                        f"while holding {loser['name']} to {loser['total_yards']}.")
                    if winner.get("total_yards") is not None and loser.get("total_yards") is not None
                    else None,
                    "tags": ["blowout", "momentum"],
                }
            )

        thriller = min(box_scores, key=self._margin, default=None)
        if thriller and self._margin(thriller) <= 3:
            winner, loser = self._winner_loser(thriller)
            narratives.append(
                {
                    "gameId": thriller.game_id,
                    "headline": f"{winner['name']} edge {loser['name']} in Week {week} thriller",
                    "body": "The decisive score came late as both teams traded punches all night.",
                    "tags": ["thriller", "clutch"],
                }
            )

        star = self._find_star_performance(box_scores)
        if star is not None:
            narratives.append(star)

        injury_story = self._major_injury(box_scores, week)
        if injury_story is not None:
            narratives.append(injury_story)

        return narratives[:4]

    def _margin(self, box_score) -> int:
        return abs(box_score.home_team.get("score", 0) - box_score.away_team.get("score", 0))

    def _winner_loser(self, box_score) -> tuple[dict[str, Any], dict[str, Any]]:
        home_id = box_score.home_team["id"]
        away_id = box_score.away_team["id"]
        home_totals = box_score.team_stats.get(home_id, {})
        away_totals = box_score.team_stats.get(away_id, {})
        home = {
            "name": box_score.home_team["name"],
            "score": box_score.home_team["score"],
            "total_yards": home_totals.get("total_yards"),
        }
        away = {
            "name": box_score.away_team["name"],
            "score": box_score.away_team["score"],
            "total_yards": away_totals.get("total_yards"),
        }
        if home["score"] >= away["score"]:
            return home, away
        return away, home

    def _find_star_performance(self, box_scores: Sequence[Any]) -> dict[str, Any] | None:
        top_entry: dict[str, Any] | None = None
        best_score = 0
        for box in box_scores:
            for team_id, stats in box.team_stats.items():
                for player in stats.get("players", []):
                    weighted = (
                        player.get("passing_yards", 0)
                        + player.get("rushing_yards", 0) * 1.2
                        + player.get("receiving_yards", 0)
                        + player.get("tackles", 0) * 5
                        + player.get("sacks", 0) * 20
                        + player.get("forced_turnovers", 0) * 30
                    )
                    if weighted > best_score:
                        best_score = weighted
                        top_entry = {
                            "gameId": box.game_id,
                            "headline": f"{player['name']} shines with all-around performance",
                            "body": self._format_player_line(player),
                            "tags": ["star", player.get("position", "player")],
                        }
        if best_score >= 150 and top_entry:
            return top_entry
        return None

    def _format_player_line(self, player: dict[str, Any]) -> str:
        parts: list[str] = []
        if player.get("passing_yards"):
            parts.append(f"{player['passing_yards']} pass yds")
        if player.get("passing_tds"):
            parts.append(f"{player['passing_tds']} pass TDs")
        if player.get("rushing_yards"):
            parts.append(f"{player['rushing_yards']} rush yds")
        if player.get("rushing_tds"):
            parts.append(f"{player['rushing_tds']} rush TDs")
        if player.get("receiving_yards"):
            parts.append(f"{player['receiving_yards']} rec yds")
        if player.get("receiving_tds"):
            parts.append(f"{player['receiving_tds']} rec TDs")
        if player.get("tackles"):
            parts.append(f"{player['tackles']} tackles")
        if player.get("sacks"):
            parts.append(f"{player['sacks']} sacks")
        if player.get("forced_turnovers"):
            parts.append(f"{player['forced_turnovers']} takeaways")
        return ", ".join(parts)

    def _major_injury(self, box_scores: Sequence[Any], week: int) -> dict[str, Any] | None:
        for box in box_scores:
            if not box.injuries:
                continue
            injury = box.injuries[0]
            home_ids = {player.get("player_id") for player in box.team_stats.get(box.home_team["id"], {}).get("players", [])}
            team = box.home_team if injury.get("player_id") in home_ids else box.away_team
            return {
                "gameId": box.game_id,
                "headline": f"{team['name']} face setback as {injury['name']} leaves injured",
                "body": f"Week {week} showdown saw {injury['name']} exit with a {injury['status']} designation.",
                "tags": ["injury", "health"],
            }
        return None
