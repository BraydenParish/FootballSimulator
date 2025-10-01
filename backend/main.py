from __future__ import annotations

from datetime import datetime
from typing import Optional

import random

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.app.db import get_connection, row_to_dict


def _get_team(connection, team_id: int):
    team = connection.execute(
        """
        SELECT id, name, abbreviation, conference, division
        FROM teams
        WHERE id = ?
        """,
        (team_id,),
    ).fetchone()
    if team is None:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    return team


def _team_strength(connection, team_id: int) -> float:
    rating_row = connection.execute(
        """
        SELECT AVG(overall_rating) AS avg_rating
        FROM players
        WHERE team_id = ?
        """,
        (team_id,),
    ).fetchone()
    avg_rating = rating_row["avg_rating"] if rating_row and rating_row["avg_rating"] is not None else 60.0
    return float(avg_rating)


def _simulate_scores(home_rating: float, away_rating: float, seed: int) -> tuple[int, int]:
    rng = random.Random(seed)
    rating_diff = home_rating - away_rating
    base_total = 42 + rng.uniform(-8, 8)
    home_share = 0.5 + rating_diff * 0.008
    home_points = base_total * max(0.2, min(0.8, home_share))
    away_points = base_total - home_points
    home_score = max(0, int(round(home_points + rng.gauss(0, 3))))
    away_score = max(0, int(round(away_points + rng.gauss(0, 3))))
    if home_score == away_score:
        adjustment = 1 if rng.random() > 0.5 else -1
        home_score = max(0, home_score + adjustment)
    return home_score, away_score


def _build_narrative(home_team: dict, away_team: dict, home_score: int, away_score: int) -> str:
    if home_score > away_score:
        margin = home_score - away_score
        return (
            f"{home_team['name']} protected home field with a {home_score}-{away_score} win over "
            f"{away_team['name']}, pulling away by {margin} in the final quarter."
        )
    if away_score > home_score:
        margin = away_score - home_score
        return (
            f"{away_team['name']} stunned {home_team['name']} on the road, leaving with a {away_score}-{home_score}"
            f" victory and a {margin}-point cushion."
        )
    return (
        f"{home_team['name']} and {away_team['name']} traded blows all afternoon, settling for a "
        f"{home_score}-{away_score} tie after overtime."
    )


def _persist_simulation(
    connection,
    *,
    week: int,
    home_team_id: int,
    away_team_id: int,
    home_score: int,
    away_score: int,
    played_at: str,
):
    existing = connection.execute(
        """
        SELECT id, played_at
        FROM games
        WHERE week = ? AND home_team_id = ? AND away_team_id = ?
        """,
        (week, home_team_id, away_team_id),
    ).fetchone()

    if existing:
        if existing["played_at"]:
            raise HTTPException(status_code=400, detail="Game has already been simulated")
        game_id = existing["id"]
        connection.execute(
            """
            UPDATE games
            SET home_score = ?, away_score = ?, played_at = ?
            WHERE id = ?
            """,
            (home_score, away_score, played_at, game_id),
        )
        return game_id

    cursor = connection.execute(
        """
        INSERT INTO games (week, home_team_id, away_team_id, home_score, away_score, played_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (week, home_team_id, away_team_id, home_score, away_score, played_at),
    )
    return cursor.lastrowid


app = FastAPI()

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"message": "NFL GM Simulator backend is running"}

# ---- Teams ----
@app.get("/teams")
def get_teams():
    with get_connection() as connection:
        teams = connection.execute(
            """
            SELECT id, name, abbreviation, conference, division
            FROM teams
            ORDER BY name
            """
        ).fetchall()
    return [row_to_dict(team) for team in teams]


@app.get("/teams/{team_id}")
def get_team(team_id: int):
    with get_connection() as connection:
        team = connection.execute(
            """
            SELECT id, name, abbreviation, conference, division
            FROM teams
            WHERE id = ?
            """,
            (team_id,),
        ).fetchone()
        if team is None:
            raise HTTPException(status_code=404, detail="Team not found")

        roster = connection.execute(
            """
            SELECT id, name, position, overall_rating, age, depth_chart_position, status
            FROM players
            WHERE team_id = ?
            ORDER BY position, overall_rating DESC
            """,
            (team_id,),
        ).fetchall()

    return {**row_to_dict(team), "roster": [row_to_dict(player) for player in roster]}

# ---- Players ----
@app.get("/players")
def get_players(team_id: Optional[int] = None, status: Optional[str] = None):
    query = [
        "SELECT id, name, position, overall_rating, age, team_id, depth_chart_position, status",
        "FROM players",
    ]
    clauses: list[str] = []
    params: list[object] = []

    if team_id is not None:
        clauses.append("team_id = ?")
        params.append(team_id)

    if status is not None:
        clauses.append("status = ?")
        params.append(status)

    if clauses:
        query.append("WHERE " + " AND ".join(clauses))

    query.append("ORDER BY overall_rating DESC, name")

    sql = "\n".join(query)

    with get_connection() as connection:
        players = connection.execute(sql, params).fetchall()

    return [row_to_dict(player) for player in players]


@app.get("/players/{player_id}")
def get_player(player_id: int):
    with get_connection() as connection:
        player = connection.execute(
            """
            SELECT id, name, position, overall_rating, age, team_id, depth_chart_position, status
            FROM players
            WHERE id = ?
            """,
            (player_id,),
        ).fetchone()

    if player is None:
        raise HTTPException(status_code=404, detail="Player not found")

    return row_to_dict(player)

# ---- Games ----
@app.get("/games")
def get_games(week: Optional[int] = None, team_id: Optional[int] = None):
    select_clause = """
        SELECT
            g.id,
            g.week,
            g.home_team_id,
            g.away_team_id,
            g.home_score,
            g.away_score,
            g.played_at,
            ht.name AS home_team_name,
            ht.abbreviation AS home_team_abbreviation,
            at.name AS away_team_name,
            at.abbreviation AS away_team_abbreviation
        FROM games AS g
        JOIN teams AS ht ON ht.id = g.home_team_id
        JOIN teams AS at ON at.id = g.away_team_id
    """

    clauses: list[str] = []
    params: list[object] = []

    if week is not None:
        clauses.append("g.week = ?")
        params.append(week)

    if team_id is not None:
        clauses.append("(g.home_team_id = ? OR g.away_team_id = ?)")
        params.extend([team_id, team_id])

    query_parts = [select_clause]
    if clauses:
        query_parts.append("WHERE " + " AND ".join(clauses))

    query_parts.append("ORDER BY g.week, g.id")
    sql = "\n".join(query_parts)

    with get_connection() as connection:
        games = connection.execute(sql, params).fetchall()

    return [row_to_dict(game) for game in games]


@app.get("/games/{game_id}")
def get_game(game_id: int):
    query = """
        SELECT
            g.id,
            g.week,
            g.home_team_id,
            g.away_team_id,
            g.home_score,
            g.away_score,
            g.played_at,
            ht.name AS home_team_name,
            ht.abbreviation AS home_team_abbreviation,
            at.name AS away_team_name,
            at.abbreviation AS away_team_abbreviation
        FROM games AS g
        JOIN teams AS ht ON ht.id = g.home_team_id
        JOIN teams AS at ON at.id = g.away_team_id
        WHERE g.id = ?
    """

    with get_connection() as connection:
        game = connection.execute(query, (game_id,)).fetchone()

    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")

    return row_to_dict(game)


# ---- Simulation ----
class GameRequest(BaseModel):
    home_team: int
    away_team: int
    week: int

class WeekRequest(BaseModel):
    week: int


def _simulate_and_store(
    connection,
    *,
    week: int,
    home_team_id: int,
    away_team_id: int,
) -> dict:
    if home_team_id == away_team_id:
        raise HTTPException(status_code=400, detail="A team cannot play against itself")

    home_team = _get_team(connection, home_team_id)
    away_team = _get_team(connection, away_team_id)
    home_team_data = row_to_dict(home_team)
    away_team_data = row_to_dict(away_team)
    home_rating = _team_strength(connection, home_team_id)
    away_rating = _team_strength(connection, away_team_id)

    seed = (week << 20) ^ (home_team_id << 10) ^ away_team_id
    home_score, away_score = _simulate_scores(home_rating, away_rating, seed)
    played_at = datetime.utcnow().isoformat(timespec="seconds")
    game_id = _persist_simulation(
        connection,
        week=week,
        home_team_id=home_team_id,
        away_team_id=away_team_id,
        home_score=home_score,
        away_score=away_score,
        played_at=played_at,
    )

    narrative = _build_narrative(home_team_data, away_team_data, home_score, away_score)

    return {
        "game_id": game_id,
        "week": week,
        "played_at": played_at,
        "home_team": {**home_team_data, "score": home_score},
        "away_team": {**away_team_data, "score": away_score},
        "narrative": narrative,
    }


@app.post("/simulate-game")
def simulate_game(request: GameRequest):
    with get_connection() as connection:
        result = _simulate_and_store(
            connection,
            week=request.week,
            home_team_id=request.home_team,
            away_team_id=request.away_team,
        )
        connection.commit()
    return result


@app.post("/simulate-week")
def simulate_week(request: WeekRequest):
    with get_connection() as connection:
        scheduled_games = connection.execute(
            """
            SELECT id, home_team_id, away_team_id, played_at
            FROM games
            WHERE week = ?
            """,
            (request.week,),
        ).fetchall()

        if not scheduled_games:
            raise HTTPException(status_code=404, detail="No games scheduled for this week")

        results = []
        for scheduled in scheduled_games:
            results.append(
                _simulate_and_store(
                    connection,
                    week=request.week,
                    home_team_id=scheduled["home_team_id"],
                    away_team_id=scheduled["away_team_id"],
                )
            )

        connection.commit()

    return {"week": request.week, "results": results}

# ---- Standings ----
@app.get("/standings")
def get_standings():
    query = """
        WITH completed_games AS (
            SELECT *
            FROM games
            WHERE played_at IS NOT NULL OR home_score <> 0 OR away_score <> 0
        ),
        game_results AS (
            SELECT
                home_team_id AS team_id,
                CASE WHEN home_score > away_score THEN 1 ELSE 0 END AS wins,
                CASE WHEN home_score < away_score THEN 1 ELSE 0 END AS losses,
                CASE WHEN home_score = away_score THEN 1 ELSE 0 END AS ties
            FROM completed_games
            UNION ALL
            SELECT
                away_team_id AS team_id,
                CASE WHEN away_score > home_score THEN 1 ELSE 0 END AS wins,
                CASE WHEN away_score < home_score THEN 1 ELSE 0 END AS losses,
                CASE WHEN home_score = away_score THEN 1 ELSE 0 END AS ties
            FROM completed_games
        )
        SELECT
            t.id,
            t.name,
            t.abbreviation,
            t.conference,
            t.division,
            COALESCE(SUM(gr.wins), 0) AS wins,
            COALESCE(SUM(gr.losses), 0) AS losses,
            COALESCE(SUM(gr.ties), 0) AS ties
        FROM teams AS t
        LEFT JOIN game_results AS gr ON gr.team_id = t.id
        GROUP BY t.id
        ORDER BY t.conference, t.division, wins DESC, losses ASC, t.name
    """

    with get_connection() as connection:
        standings = connection.execute(query).fetchall()

    return [row_to_dict(row) for row in standings]
