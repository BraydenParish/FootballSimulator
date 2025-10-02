from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Iterable

from fastapi import HTTPException

from ..db import row_to_dict
from shared.utils.rules import SimulationRules


@dataclass(slots=True)
class GameBoxScore:
    """Lightweight representation of a simulated game's results."""

    game_id: int
    week: int
    played_at: str
    home_team: dict
    away_team: dict
    team_stats: dict
    player_stats: dict[int, list[dict]]
    injuries: list[dict]
    plays: list[dict]


class SimulationService:
    """Simulate scheduled games and persist box scores/statistics."""

    def __init__(self, rules: SimulationRules) -> None:
        self.rules = rules

    def simulate_week(self, connection, week: int, *, detailed: bool = False) -> list[GameBoxScore]:
        games = connection.execute(
            """
            SELECT id, week, home_team_id, away_team_id, played_at
            FROM games
            WHERE week = ?
            ORDER BY id
            """,
            (week,),
        ).fetchall()

        if not games:
            raise HTTPException(status_code=404, detail="No games scheduled for this week")

        results: list[GameBoxScore] = []
        for game in games:
            if game["played_at"]:
                raise HTTPException(status_code=400, detail=f"Game {game['id']} already simulated")

            result = self._simulate_game(connection, game, detailed=detailed)
            results.append(result)

        return results

    # Internal helpers -------------------------------------------------

    def _simulate_game(self, connection, game_row, *, detailed: bool) -> GameBoxScore:
        home_team = self._get_team(connection, game_row["home_team_id"])
        away_team = self._get_team(connection, game_row["away_team_id"])

        home_rating = self._team_rating(connection, home_team["id"])
        away_rating = self._team_rating(connection, away_team["id"])

        seed = (game_row["week"] << 20) ^ (home_team["id"] << 10) ^ away_team["id"]
        rng = random.Random(seed)

        home_score, away_score = self._generate_scores(rng, home_rating, away_rating)

        played_at = datetime.now(UTC).isoformat(timespec="seconds")

        connection.execute(
            """
            UPDATE games
            SET home_score = ?,
                away_score = ?,
                played_at = ?
            WHERE id = ?
            """,
            (home_score, away_score, played_at, game_row["id"]),
        )

        connection.execute("DELETE FROM team_game_stats WHERE game_id = ?", (game_row["id"],))
        connection.execute("DELETE FROM player_game_stats WHERE game_id = ?", (game_row["id"],))
        connection.execute("DELETE FROM game_events WHERE game_id = ?", (game_row["id"],))

        home_stats = self._generate_team_stats(connection, rng, home_team, home_score, away_score)
        away_stats = self._generate_team_stats(connection, rng, away_team, away_score, home_score)

        injuries = home_stats.pop("injuries") + away_stats.pop("injuries")

        player_stats = {
            home_team["id"]: [dict(player) for player in home_stats["players"]],
            away_team["id"]: [dict(player) for player in away_stats["players"]],
        }

        for entry in (home_stats, away_stats):
            connection.execute(
                """
                INSERT INTO team_game_stats (game_id, team_id, total_yards, turnovers)
                VALUES (?, ?, ?, ?)
                """,
                (game_row["id"], entry["team_id"], entry["total_yards"], entry["turnovers"]),
            )

        for player_stat in home_stats["players"] + away_stats["players"]:
            connection.execute(
                """
                INSERT INTO player_game_stats (
                    game_id,
                    player_id,
                    team_id,
                    passing_yards,
                    passing_tds,
                    interceptions,
                    rushing_yards,
                    rushing_tds,
                    receiving_yards,
                    receiving_tds,
                    tackles,
                    sacks,
                    forced_turnovers
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    game_row["id"],
                    player_stat["player_id"],
                    player_stat["team_id"],
                    player_stat["passing_yards"],
                    player_stat["passing_tds"],
                    player_stat["interceptions"],
                    player_stat["rushing_yards"],
                    player_stat["rushing_tds"],
                    player_stat["receiving_yards"],
                    player_stat["receiving_tds"],
                    player_stat["tackles"],
                    player_stat["sacks"],
                    player_stat["forced_turnovers"],
                ),
            )

        home_payload = row_to_dict(home_team)
        away_payload = row_to_dict(away_team)

        plays: list[dict] = []
        if detailed:
            plays = self._generate_play_log(
                rng=rng,
                home_team=home_payload,
                away_team=away_payload,
                home_score=home_score,
                away_score=away_score,
                home_stats=home_stats,
                away_stats=away_stats,
            )
            if plays:
                self._persist_play_log(connection, game_row["id"], plays)

        box = {
            "home_team": {**home_payload, "score": home_score},
            "away_team": {**away_payload, "score": away_score},
            "team_stats": {
                home_team["id"]: self._format_team_stats(home_stats),
                away_team["id"]: self._format_team_stats(away_stats),
            },
        }

        return GameBoxScore(
            game_id=game_row["id"],
            week=game_row["week"],
            played_at=played_at,
            home_team=box["home_team"],
            away_team=box["away_team"],
            team_stats=box["team_stats"],
            player_stats=player_stats,
            injuries=injuries,
            plays=plays,
        )

    def _generate_scores(self, rng: random.Random, home_rating: float, away_rating: float) -> tuple[int, int]:
        diff = (home_rating - away_rating) * self.rules.rating_factor + self.rules.home_field_advantage
        home_points = self.rules.base_points + diff + rng.gauss(0, self.rules.random_variance)
        away_points = self.rules.base_points - diff + rng.gauss(0, self.rules.random_variance)

        home_score = self._clamp_score(home_points)
        away_score = self._clamp_score(away_points)

        if home_score == away_score:
            home_score += 3 if rng.random() > 0.5 else -3
            home_score = self._clamp_score(home_score)
        return home_score, away_score

    def _clamp_score(self, value: float) -> int:
        score = int(round(value))
        score = max(self.rules.min_score, score)
        score = min(self.rules.max_score, score)
        return score

    def _generate_team_stats(self, connection, rng, team, team_points: int, opponent_points: int) -> dict:
        qb = self._depth_chart_player(connection, team["id"], "QB")
        rb = self._depth_chart_player(connection, team["id"], "RB") or self._depth_chart_player(connection, team["id"], "WR")
        wr = self._depth_chart_player(connection, team["id"], "WR") or self._depth_chart_player(connection, team["id"], "TE")
        defender = (
            self._depth_chart_player(connection, team["id"], "EDGE")
            or self._depth_chart_player(connection, team["id"], "LB")
            or self._depth_chart_player(connection, team["id"], "CB")
        )

        players_stats: list[dict] = []
        total_yards = 0
        turnovers = max(0, int(abs(rng.gauss(0, 1))))

        if qb:
            passing_yards = int(qb["overall_rating"] * self.rules.passing_yards_per_rating + rng.gauss(0, 35))
            passing_tds = max(0, int(round(team_points / 14 + rng.random())))
            interceptions = min(3, max(0, int(rng.gauss(0.5, 0.8))))
            players_stats.append(
                self._player_stat_template(
                    qb,
                    passing_yards=passing_yards,
                    passing_tds=passing_tds,
                    interceptions=interceptions,
                )
            )
            total_yards += passing_yards

        if rb:
            rushing_yards = int(rb["overall_rating"] * self.rules.rushing_yards_per_rating + rng.gauss(0, 20))
            rushing_tds = max(0, int(round(team_points / 21 + rng.random() - 0.3)))
            players_stats.append(
                self._player_stat_template(
                    rb,
                    rushing_yards=rushing_yards,
                    rushing_tds=rushing_tds,
                )
            )
            total_yards += rushing_yards

        if wr:
            receiving_yards = int(wr["overall_rating"] * self.rules.receiving_yards_per_rating + rng.gauss(0, 25))
            receiving_tds = max(0, int(round(team_points / 21 + rng.random() - 0.4)))
            players_stats.append(
                self._player_stat_template(
                    wr,
                    receiving_yards=receiving_yards,
                    receiving_tds=receiving_tds,
                )
            )
            total_yards += receiving_yards

        if defender:
            tackles = max(2, int(rng.gauss(6, 2)))
            sacks = max(0.0, round(rng.random() * self.rules.defense_big_play_factor * 10, 1))
            forced = 1 if rng.random() < self.rules.defense_big_play_factor else 0
            players_stats.append(
                self._player_stat_template(
                    defender,
                    tackles=tackles,
                    sacks=sacks,
                    forced_turnovers=forced,
                )
            )

        injuries = self._apply_injuries(connection, rng, [qb, rb, wr, defender])

        return {
            "team_id": team["id"],
            "players": players_stats,
            "total_yards": total_yards,
            "turnovers": turnovers,
            "injuries": injuries,
        }

    def _format_team_stats(self, stats: dict) -> dict:
        return {
            "total_yards": stats["total_yards"],
            "turnovers": stats["turnovers"],
            "players": stats["players"],
        }

    def _generate_play_log(
        self,
        *,
        rng: random.Random,
        home_team: dict,
        away_team: dict,
        home_score: int,
        away_score: int,
        home_stats: dict,
        away_stats: dict,
    ) -> list[dict]:
        home_events = [
            {"team": "home", "points": value, "marker": rng.uniform(0, 59.9)}
            for value in self._score_breakdown(rng, home_score)
        ]
        away_events = [
            {"team": "away", "points": value, "marker": rng.uniform(0, 59.9)}
            for value in self._score_breakdown(rng, away_score)
        ]
        timeline = home_events + away_events
        if not timeline:
            return []

        timeline.sort(key=lambda item: item["marker"])

        plays: list[dict] = []
        home_running = 0
        away_running = 0

        for sequence, event in enumerate(timeline, start=1):
            quarter, clock = self._time_from_marker(event["marker"])
            pre_home = home_running
            pre_away = away_running

            if event["team"] == "home":
                home_running += event["points"]
                team_payload = home_team
                team_stats = home_stats
            else:
                away_running += event["points"]
                team_payload = away_team
                team_stats = away_stats

            description, player_payload, play_type = self._describe_play(
                rng,
                team_payload,
                team_stats,
                event["points"],
            )

            impact = self._impact_label(
                pre_home,
                pre_away,
                home_running,
                away_running,
                event["team"],
            )

            plays.append(
                {
                    "sequence": sequence,
                    "quarter": quarter,
                    "clock": clock,
                    "team": {
                        "id": team_payload["id"],
                        "name": team_payload["name"],
                        "abbreviation": team_payload["abbreviation"],
                    },
                    "player": player_payload,
                    "description": description,
                    "type": play_type,
                    "impact": impact,
                    "points": event["points"],
                    "score": {"home": home_running, "away": away_running},
                }
            )

        return plays

    def _score_breakdown(self, rng: random.Random, score: int) -> list[int]:
        if score <= 0:
            return []
        breakdown: list[int] = []
        remaining = score
        while remaining > 13:
            breakdown.append(7)
            remaining -= 7
        tail_map = {
            0: [],
            2: [2],
            3: [3],
            4: [2, 2],
            5: [3, 2],
            6: [3, 3],
            7: [7],
            8: [8],
            9: [7, 2],
            10: [7, 3],
            11: [8, 3],
            12: [7, 3, 2],
            13: [7, 3, 3],
        }
        tail = tail_map.get(remaining)
        if tail is None:
            breakdown.append(remaining)
        else:
            breakdown.extend(tail)
        rng.shuffle(breakdown)
        return breakdown

    def _time_from_marker(self, marker: float) -> tuple[int, str]:
        total_seconds = int(marker * 60)
        max_seconds = 15 * 4 * 60 - 1
        total_seconds = max(0, min(total_seconds, max_seconds))
        quarter_index = min(total_seconds // (15 * 60), 3)
        quarter = quarter_index + 1
        seconds_into_quarter = total_seconds - quarter_index * 15 * 60
        remaining_seconds = 15 * 60 - seconds_into_quarter
        minutes = remaining_seconds // 60
        seconds = remaining_seconds % 60
        return quarter, f"{minutes:02}:{seconds:02}"

    def _describe_play(
        self,
        rng: random.Random,
        team: dict,
        team_stats: dict,
        points: int,
    ) -> tuple[str, dict | None, str]:
        players = team_stats.get("players", [])
        qb = self._top_player(players, "passing_yards")
        rb = self._top_player(players, "rushing_yards")
        receiving_candidates = [
            player
            for player in players
            if (player.get("receiving_yards", 0) or player.get("receiving_tds", 0))
        ]
        wr = self._top_player(receiving_candidates, "receiving_yards")
        defender_candidates = [
            player
            for player in players
            if (player.get("tackles", 0) or player.get("sacks", 0) or player.get("forced_turnovers", 0))
        ]
        defender = self._top_player(defender_candidates, "tackles")

        abbr = team["abbreviation"]
        highlight_type = "score"
        player_payload = None

        if points >= 7:
            highlight_type = "touchdown"
            if qb and wr and rng.random() < 0.6:
                yards = max(8, int(rng.gauss(24, 12)))
                description = f"{abbr} QB {qb.get('name', 'QB')} finds {wr.get('name', 'receiver')} for a {yards}-yard touchdown."
                player_payload = self._player_payload(wr)
            elif rb:
                yards = max(1, int(rng.gauss(8, 4)))
                description = f"{abbr} RB {rb.get('name', 'RB')} powers in from {yards} yards out."
                player_payload = self._player_payload(rb)
            elif defender:
                description = f"{abbr} defense cashes in as {defender.get('name', 'defender')} scores on a takeaway."
                player_payload = self._player_payload(defender)
            else:
                description = f"{team['name']} finds the end zone."
            if points == 8:
                description += " They convert the two-point try."
        elif points == 3:
            highlight_type = "field_goal"
            distance = max(28, min(54, int(rng.gauss(42, 6))))
            description = f"{team['name']} drills a {distance}-yard field goal."
        elif points == 2:
            highlight_type = "safety"
            if defender:
                description = f"{abbr} defense swarms as {defender.get('name', 'defender')} records a safety."
                player_payload = self._player_payload(defender)
            else:
                description = f"{team['name']} records a safety."
        else:
            description = f"{team['name']} adds {points} points."

        return description, player_payload, highlight_type

    def _player_payload(self, player: dict | None) -> dict | None:
        if not player:
            return None
        return {
            "id": player.get("player_id"),
            "name": player.get("name"),
            "position": player.get("position"),
        }

    def _top_player(self, players: list[dict], metric: str):
        best = None
        best_value = float("-inf")
        for player in players:
            value = player.get(metric, 0) or 0
            if value > best_value:
                best_value = value
                best = player
        return best

    def _impact_label(
        self,
        home_before: int,
        away_before: int,
        home_after: int,
        away_after: int,
        scoring_team: str,
    ) -> str:
        if home_after == away_after:
            return "ties_game"

        if scoring_team == "home":
            before_margin = home_before - away_before
            after_margin = home_after - away_after
        else:
            before_margin = away_before - home_before
            after_margin = away_after - home_after

        if before_margin <= 0 < after_margin:
            return "takes_lead"
        if before_margin > 0 and after_margin > before_margin:
            return "extends_lead"
        if before_margin < 0 and after_margin < 0:
            return "cuts_deficit"
        if before_margin < 0 <= after_margin:
            return "ties_game"
        return "keeps_pressure"

    def _persist_play_log(self, connection, game_id: int, plays: list[dict]) -> None:
        for play in plays:
            player_id = None
            if play.get("player"):
                player_id = play["player"].get("id")
            connection.execute(
                """
                INSERT INTO game_events (
                    game_id,
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
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    game_id,
                    play["sequence"],
                    play["quarter"],
                    play["clock"],
                    play["team"]["id"],
                    player_id,
                    play["description"],
                    play["type"],
                    play.get("impact"),
                    play["points"],
                    play["score"]["home"],
                    play["score"]["away"],
                ),
            )

    def _apply_injuries(self, connection, rng, candidates: Iterable) -> list[dict]:
        injuries: list[dict] = []
        for player in candidates:
            if not player:
                continue
            if rng.random() < self.rules.injury_probability:
                injuries.append(
                    {
                        "player_id": player["id"],
                        "team_id": player["team_id"],
                        "name": player["name"],
                        "status": "questionable",
                    }
                )
                connection.execute(
                    "UPDATE players SET injury_status = 'questionable' WHERE id = ?",
                    (player["id"],),
                )
            else:
                connection.execute(
                    "UPDATE players SET injury_status = 'healthy' WHERE id = ?",
                    (player["id"],),
                )
        return injuries

    def _player_stat_template(self, player, **overrides) -> dict:
        base = {
            "player_id": player["id"],
            "team_id": player["team_id"],
            "name": player["name"],
            "position": player["position"],
            "passing_yards": 0,
            "passing_tds": 0,
            "interceptions": 0,
            "rushing_yards": 0,
            "rushing_tds": 0,
            "receiving_yards": 0,
            "receiving_tds": 0,
            "tackles": 0,
            "sacks": 0.0,
            "forced_turnovers": 0,
        }
        base.update(overrides)
        return base

    def _depth_chart_player(self, connection, team_id: int, position: str):
        return connection.execute(
            """
            SELECT *
            FROM players
            WHERE team_id = ? AND position = ? AND status = 'active'
            ORDER BY COALESCE(depth_chart_order, 999)
            LIMIT 1
            """,
            (team_id, position),
        ).fetchone()

    def _team_rating(self, connection, team_id: int) -> float:
        row = connection.execute(
            """
            SELECT AVG(overall_rating) AS avg_rating
            FROM players
            WHERE team_id = ? AND status = 'active'
            """,
            (team_id,),
        ).fetchone()
        return float(row["avg_rating"] or 60.0)

    def _get_team(self, connection, team_id: int):
        team = connection.execute(
            "SELECT id, name, abbreviation FROM teams WHERE id = ?",
            (team_id,),
        ).fetchone()
        if team is None:
            raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
        return team


