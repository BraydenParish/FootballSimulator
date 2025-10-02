from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.db import get_connection, row_to_dict
from backend.app.services.roster_service import RosterService
from backend.app.services.box_score_service import BoxScoreService
from backend.app.services.narrative_service import NarrativeService
from backend.app.services.simulation_service import GameBoxScore, SimulationService
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

    return {"team": result.team, "player": result.player}


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

    games_payload = [_serialize_simulation_game(box, include_plays=detailed) for box in box_scores]

    return {
        "week": request.week,
        "mode": request.mode,
        "summaries": summaries,
        "games": games_payload,
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


def _serialize_simulation_game(box: GameBoxScore, *, include_plays: bool) -> dict:
    team_stats_payload: list[dict] = []
    player_stats_payload: list[dict] = []
    for team_id, stats in box.team_stats.items():
        team_stats_payload.append(
            {
                "teamId": team_id,
                "totalYards": stats.get("total_yards", 0),
                "turnovers": stats.get("turnovers", 0),
            }
        )
        player_stats_payload.append(
            {
                "teamId": team_id,
                "players": [dict(player) for player in stats.get("players", [])],
            }
        )

    injuries_payload = [dict(injury) for injury in box.injuries]

    return {
        "gameId": box.game_id,
        "week": box.week,
        "playedAt": box.played_at,
        "homeTeam": box.home_team,
        "awayTeam": box.away_team,
        "teamStats": team_stats_payload,
        "playerStats": player_stats_payload,
        "injuries": injuries_payload,
        "plays": box.plays if include_plays else [],
    }

@app.get("/games/week/{week}")
def list_week_box_scores(week: int):
    with get_connection() as connection:
        box_scores = box_score_service.box_scores(connection, week=week)
    return box_scores


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


@app.get("/standings")
def league_standings():
    with get_connection() as connection:
        teams = connection.execute(
            """
            SELECT id, name, abbreviation, conference, division
            FROM teams
            ORDER BY conference, division, name
            """
        ).fetchall()

        results = connection.execute(
            """
            SELECT week, home_team_id, away_team_id, home_score, away_score
            FROM games
            WHERE played_at IS NOT NULL
            ORDER BY week
            """
        ).fetchall()

    latest_week = max((row["week"] for row in results), default=0)

    records: dict[int, dict[str, float]] = {
        team["id"]: {
            "wins": 0,
            "losses": 0,
            "ties": 0,
            "points_for": 0,
            "points_against": 0,
        }
        for team in teams
    }

    for row in results:
        home = records[row["home_team_id"]]
        away = records[row["away_team_id"]]

        home_score = int(row["home_score"] or 0)
        away_score = int(row["away_score"] or 0)

        home["points_for"] += home_score
        home["points_against"] += away_score
        away["points_for"] += away_score
        away["points_against"] += home_score

        if home_score > away_score:
            home["wins"] += 1
            away["losses"] += 1
        elif away_score > home_score:
            away["wins"] += 1
            home["losses"] += 1
        else:
            home["ties"] += 1
            away["ties"] += 1

    by_division: dict[tuple[str, str], list[dict]] = defaultdict(list)

    standings: list[dict] = []
    for team in teams:
        record = records[team["id"]]
        games_played = record["wins"] + record["losses"] + record["ties"]
        win_pct = (
            (record["wins"] + 0.5 * record["ties"]) / games_played
            if games_played
            else 0.0
        )
        payload = {
            "teamId": team["id"],
            "name": team["name"],
            "abbreviation": team["abbreviation"],
            "conference": team["conference"],
            "division": team["division"],
            "wins": int(record["wins"]),
            "losses": int(record["losses"]),
            "ties": int(record["ties"]),
            "winPct": round(win_pct, 3),
            "pointsFor": int(record["points_for"]),
            "pointsAgainst": int(record["points_against"]),
            "pointDiff": int(record["points_for"] - record["points_against"]),
        }
        standings.append(payload)
        by_division[(team["conference"], team["division"])].append(payload)

    division_order = sorted(by_division.keys(), key=lambda key: (key[0], key[1]))
    divisions: list[dict] = []
    for key in division_order:
        teams_in_division = sorted(
            by_division[key],
            key=lambda item: (item["winPct"], item["pointDiff"], item["pointsFor"]),
            reverse=True,
        )
        divisions.append(
            {
                "conference": key[0],
                "division": key[1],
                "teams": teams_in_division,
            }
        )

    return {
        "updatedThroughWeek": latest_week,
        "divisions": divisions,
        "teams": standings,
    }


@app.get("/narratives")
def list_narratives(week: Optional[int] = None):
    with get_connection() as connection:
        items = narrative_service.list_narratives(connection, week=week)
    return items




