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
    game_id: int
    week: int
    played_at: str
    home_team: dict
    away_team: dict
    team_stats: dict
    injuries: list[dict]


class SimulationService:
    """Simulate scheduled games and persist box scores/statistics."""

    def __init__(self, rules: SimulationRules) -> None:
        self.rules = rules

    def simulate_week(self, connection, week: int) -> list[GameBoxScore]:
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

            result = self._simulate_game(connection, game)
            results.append(result)

        return results

    # Internal helpers -------------------------------------------------

    def _simulate_game(self, connection, game_row) -> GameBoxScore:
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

        home_stats = self._generate_team_stats(connection, rng, home_team, home_score, away_score)
        away_stats = self._generate_team_stats(connection, rng, away_team, away_score, home_score)

        injuries = home_stats.pop("injuries") + away_stats.pop("injuries")

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

        box = {
            "home_team": {**row_to_dict(home_team), "score": home_score},
            "away_team": {**row_to_dict(away_team), "score": away_score},
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
            injuries=injuries,
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

    def _apply_injuries(self, connection, rng, candidates: Iterable) -> list[dict]:
        injuries: list[dict] = []
        for player in candidates:
            if not player:
                continue
            if rng.random() < self.rules.injury_probability:
                injuries.append({"player_id": player["id"], "name": player["name"], "status": "questionable"})
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
