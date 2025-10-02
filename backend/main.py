from __future__ import annotations

from dataclasses import asdict
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.db import get_connection, row_to_dict
from backend.app.services.roster_service import RosterService
from backend.app.services.box_score_service import BoxScoreService
from backend.app.services.narrative_service import NarrativeService
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
box_score_service = BoxScoreService()
narrative_service = NarrativeService()
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



class DepthChartEntryPayload(BaseModel):
    slot: str
    player_id: Optional[int] = Field(default=None, alias="playerId")


class DepthChartUpdateRequest(BaseModel):
    entries: list[DepthChartEntryPayload]


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


@app.get("/teams/{team_id}/depth-chart")
def get_depth_chart(team_id: int):
    with get_connection() as connection:
        entries = roster_service.get_depth_chart(connection, team_id)
    return {"teamId": team_id, "entries": entries}


@app.post("/teams/{team_id}/depth-chart")
def update_depth_chart(team_id: int, payload: DepthChartUpdateRequest):
    entry_payload = [entry.model_dump(by_alias=True) for entry in payload.entries]
    with get_connection() as connection:
        roster_service.update_depth_chart(connection, team_id, entry_payload)
        connection.commit()
    return {"teamId": team_id, "updated": len(payload.entries)}
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



@app.post("/trade/validate")
def validate_trade(proposal: TradeProposal):
    offer_payload = [asset.model_dump(by_alias=True, exclude_none=True) for asset in proposal.offer]
    request_payload = [asset.model_dump(by_alias=True, exclude_none=True) for asset in proposal.request]

    with get_connection() as connection:
        try:
            trade_service.execute_trade(
                connection,
                team_a_id=proposal.team_a,
                team_b_id=proposal.team_b,
                offer=offer_payload,
                request=request_payload,
            )
        except HTTPException as exc:
            connection.rollback()
            return {"success": False, "message": exc.detail}
        connection.rollback()

    return {"success": True, "message": "Trade passes validation"}

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
        "success": True,
        "message": "Trade executed successfully",
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
    clauses: list[str] = []
    params: list[object] = []

    sql_parts = [
        "SELECT",
        "    g.id AS id,",
        "    g.week AS week,",
        "    g.home_team_id AS homeTeamId,",
        "    g.away_team_id AS awayTeamId,",
        "    g.home_score AS homeScore,",
        "    g.away_score AS awayScore,",
        "    g.played_at AS playedAt,",
        "    ht.name AS homeTeamName,",
        "    ht.abbreviation AS homeTeamAbbreviation,",
        "    at.name AS awayTeamName,",
        "    at.abbreviation AS awayTeamAbbreviation",
        "FROM games AS g",
        "JOIN teams AS ht ON ht.id = g.home_team_id",
        "JOIN teams AS at ON at.id = g.away_team_id",
    ]

    if week is not None:
        clauses.append("g.week = ?")
        params.append(week)

    if team_id is not None:
        clauses.append("(g.home_team_id = ? OR g.away_team_id = ?)")
        params.extend([team_id, team_id])

    if clauses:
        sql_parts.append("WHERE " + " AND ".join(clauses))

    sql_parts.append("ORDER BY g.week, g.id")
    sql = "\n".join(sql_parts)

    with get_connection() as connection:
        games = connection.execute(sql, params).fetchall()

    return [row_to_dict(game) for game in games]

@app.get("/games/{game_id}")
def get_game(game_id: int):
    query = """
        SELECT
            g.id AS id,
            g.week AS week,
            g.home_team_id AS homeTeamId,
            g.away_team_id AS awayTeamId,
            g.home_score AS homeScore,
            g.away_score AS awayScore,
            g.played_at AS playedAt,
            ht.name AS homeTeamName,
            ht.abbreviation AS homeTeamAbbreviation,
            at.name AS awayTeamName,
            at.abbreviation AS awayTeamAbbreviation
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
    mode: Literal["quick", "detailed"] = "quick"


@app.post("/simulate-week")
def simulate_week(request: WeekSimulationRequest):
    detailed = request.mode == "detailed"
    with get_connection() as connection:
        box_scores = simulation_service.simulate_week(
            connection,
            request.week,
            detailed=detailed,
        )
        narratives = narrative_service.record_week(
            connection,
            week=request.week,
            box_scores=box_scores,
        )
        connection.commit()

    with get_connection() as connection:
        summaries = box_score_service.box_scores(connection, week=request.week)

    play_by_play: list[str] = []
    if detailed:
        play_by_play = _format_play_log(box_scores)

    return {
        "week": request.week,
        "mode": request.mode,
        "summaries": summaries,
        "playByPlay": play_by_play,
        "narratives": narratives,
    }


def _format_play_log(box_scores) -> list[str]:
    entries: list[str] = []
    for box in box_scores:
        for play in box.plays:
            score = play.get("score", {})
            home_score = score.get("home")
            away_score = score.get("away")
            entries.append(
                f"Q{play['quarter']} {play['clock']} - {play['description']} (Score {home_score}-{away_score})"
            )
    return entries

@app.get("/games/box-scores")
def list_box_scores(week: Optional[int] = None, team_id: Optional[int] = None):
    with get_connection() as connection:
        box_scores = box_score_service.box_scores(connection, week=week, team_id=team_id)
    return box_scores


@app.get("/games/{game_id}/box-score")
def get_box_score(game_id: int):
    with get_connection() as connection:
        payload = box_score_service.box_score(connection, game_id)
    return payload


@app.get("/narratives")
def list_narratives(week: Optional[int] = None):
    with get_connection() as connection:
        items = narrative_service.list_narratives(connection, week=week)
    return items


# ---- Standings ----
@app.get("/standings")
def get_standings():
    query = """
        WITH played_games AS (
            SELECT *
            FROM games
            WHERE played_at IS NOT NULL OR home_score <> 0 OR away_score <> 0
        ),
        team_results AS (
            SELECT
                home_team_id AS team_id,
                home_score AS points_for,
                away_score AS points_against,
                CASE WHEN home_score > away_score THEN 1 ELSE 0 END AS wins,
                CASE WHEN home_score < away_score THEN 1 ELSE 0 END AS losses,
                CASE WHEN home_score = away_score THEN 1 ELSE 0 END AS ties
            FROM played_games
            UNION ALL
            SELECT
                away_team_id AS team_id,
                away_score AS points_for,
                home_score AS points_against,
                CASE WHEN away_score > home_score THEN 1 ELSE 0 END AS wins,
                CASE WHEN away_score < home_score THEN 1 ELSE 0 END AS losses,
                CASE WHEN away_score = home_score THEN 1 ELSE 0 END AS ties
            FROM played_games
        )
        SELECT
            t.id AS teamId,
            t.name AS name,
            t.abbreviation AS abbreviation,
            t.conference AS conference,
            t.division AS division,
            COALESCE(SUM(tr.wins), 0) AS wins,
            COALESCE(SUM(tr.losses), 0) AS losses,
            COALESCE(SUM(tr.ties), 0) AS ties,
            COALESCE(SUM(tr.points_for), 0) AS pointsFor,
            COALESCE(SUM(tr.points_against), 0) AS pointsAgainst
        FROM teams AS t
        LEFT JOIN team_results AS tr ON tr.team_id = t.id
        GROUP BY t.id
        ORDER BY t.conference, t.division, wins DESC, losses ASC, pointsFor DESC
    """

    with get_connection() as connection:
        standings = connection.execute(query).fetchall()

    return [row_to_dict(row) for row in standings]

@app.post("/simulate-week")
def simulate_week(request: WeekSimulationRequest):
    detailed = request.mode == "detailed"
    with get_connection() as connection:
        box_scores = simulation_service.simulate_week(
            connection, request.week, detailed=detailed
        )
        connection.commit()

    results = [
        {
            "game_id": box.game_id,
            "week": box.week,
            "played_at": box.played_at,
            "mode": request.mode,
            "home_team": box.home_team,
            "away_team": box.away_team,
            "team_stats": box.team_stats,
            "injuries": box.injuries,
            "plays": box.plays if detailed else [],
            "play_count": len(box.plays),
        }
        for box in box_scores
    ]
    return {"week": request.week, "mode": request.mode, "results": results}

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





