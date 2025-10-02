from __future__ import annotations

from dataclasses import asdict
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.db import get_connection, row_to_dict
from backend.app.services.roster_service import RosterService
from backend.app.services.simulation_service import SimulationService
from backend.app.services.stats_service import TeamStatsService
from backend.app.services.trade_service import TradeService
from shared.utils.rules import load_game_rules, load_simulation_rules

CURRENT_YEAR = 2025
GAME_RULES = load_game_rules()
SIMULATION_RULES = load_simulation_rules()

roster_service = RosterService(GAME_RULES)
trade_service = TradeService(GAME_RULES, roster_service)
simulation_service = SimulationService(SIMULATION_RULES)
team_stats_service = TeamStatsService()


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


@app.get("/teams/{team_id}/stats")
def get_team_stats(team_id: int):
    with get_connection() as connection:
        stats = team_stats_service.starters_stats(connection, team_id)
    return stats

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

# ---- Free agency ----


class SignPlayerRequest(BaseModel):
    player_id: int


@app.get("/free-agents")
def list_free_agents(year: Optional[int] = None):
    target_year = year if year is not None else CURRENT_YEAR
    with get_connection() as connection:
        free_agents = roster_service.list_free_agents(connection, year=target_year)
    return {"year": target_year, "players": free_agents}


@app.post("/teams/{team_id}/sign")
def sign_free_agent(team_id: int, payload: SignPlayerRequest):
    with get_connection() as connection:
        result = roster_service.sign_player(
            connection,
            team_id=team_id,
            player_id=payload.player_id,
        )
        roster_service.validate_depth_requirements(connection, team_id)
        connection.commit()

    return {"team": result.team, "player": result.player}


class TradeAsset(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: Literal["player", "pick"]
    player_id: Optional[int] = None
    year: Optional[int] = None
    draft_round: Optional[int] = Field(default=None, alias="round")

    @model_validator(mode="after")
    def _validate_asset(self):
        if self.type == "player" and self.player_id is None:
            raise ValueError("player asset requires player_id")
        if self.type == "pick" and (self.year is None or self.draft_round is None):
            raise ValueError("pick asset requires year and round")
        return self


class TradeProposal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    team_a: int = Field(alias="teamA")
    team_b: int = Field(alias="teamB")
    offer: list[TradeAsset]
    request: list[TradeAsset]


@app.post("/trade")
def submit_trade(proposal: TradeProposal):
    offer_payload = [asset.model_dump(by_alias=True, exclude_none=True) for asset in proposal.offer]
    request_payload = [asset.model_dump(by_alias=True, exclude_none=True) for asset in proposal.request]

    with get_connection() as connection:
        result = trade_service.execute_trade(
            connection,
            team_a_id=proposal.team_a,
            team_b_id=proposal.team_b,
            offer=offer_payload,
            request=request_payload,
        )
        connection.commit()

    summary = asdict(result)
    return {
        "teamA": summary["team_a"],
        "teamB": summary["team_b"],
        "teamA_sent": summary["team_a_sent"],
        "teamA_received": summary["team_a_received"],
        "teamB_sent": summary["team_b_sent"],
        "teamB_received": summary["team_b_received"],
    }

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


class WeekSimulationRequest(BaseModel):
    week: int


@app.post("/simulate-week")
def simulate_week(request: WeekSimulationRequest):
    with get_connection() as connection:
        box_scores = simulation_service.simulate_week(connection, request.week)
        connection.commit()

    results = [
        {
            "game_id": box.game_id,
            "week": box.week,
            "played_at": box.played_at,
            "home_team": box.home_team,
            "away_team": box.away_team,
            "team_stats": box.team_stats,
            "injuries": box.injuries,
        }
        for box in box_scores
    ]
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
