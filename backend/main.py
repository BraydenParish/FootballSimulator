from __future__ import annotations

from dataclasses import asdict
from typing import Literal, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.db import get_connection, row_to_dict
from backend.app.services.box_score_service import BoxScoreService
from backend.app.services.narrative_service import NarrativeService
from backend.app.services.roster_service import RosterService
from backend.app.services.simulation_service import SimulationService
from backend.app.services.stats_service import TeamStatsService
from backend.app.services.trade_service import TradeResult, TradeService
from shared.utils.rules import load_game_rules, load_simulation_rules

CURRENT_YEAR = 2025
GAME_RULES = load_game_rules()
SIMULATION_RULES = load_simulation_rules()

roster_service = RosterService(GAME_RULES)
trade_service = TradeService(GAME_RULES, roster_service, current_year=CURRENT_YEAR)
simulation_service = SimulationService(SIMULATION_RULES)
box_score_service = BoxScoreService()
narrative_service = NarrativeService()
team_stats_service = TeamStatsService()


app = FastAPI(title="NFL GM Simulator API", version="0.1.0")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize_player_row(row) -> dict:
    salary = float(row["salary"] or 0)
    contract_value = round(salary / 1_000_000, 2)
    return {
        "id": row["id"],
        "name": row["name"],
        "position": row["position"],
        "overall": row["overall_rating"],
        "age": row["age"],
        "contractValue": contract_value,
        "contractYears": row["contract_years"],
        "teamId": row["team_id"],
        "depthChartSlot": row["depth_chart_position"],
        "status": row["status"],
    }


def _serialize_team_row(row) -> dict:
    salary_spent = float(row["salary_spent"] or 0)
    return {
        "id": row["id"],
        "name": row["name"],
        "abbreviation": row["abbreviation"],
        "conference": row["conference"],
        "division": row["division"],
        "rating": round(row["rating"] or 0, 1),
        "salaryCap": GAME_RULES.salary_cap,
        "salarySpent": round(salary_spent / 1_000_000, 2),
    }


def _format_stat_line(row, stat_type: str) -> str:
    if stat_type == "passing":
        return f"{row['passing_yards']} pass yds · {row['passing_tds']} TD · {row['interceptions']} INT"
    if stat_type == "rushing":
        return f"{row['rushing_yards']} rush yds · {row['rushing_tds']} TD"
    if stat_type == "receiving":
        return f"{row['receiving_yards']} rec yds · {row['receiving_tds']} TD"
    tackles = row["tackles"] or 0
    sacks = row["sacks"] or 0
    forced = row["forced_turnovers"] or 0
    return f"{tackles} tackles · {sacks} sacks · {forced} takeaways"


def _stat_payload(row, stat_type: str) -> dict:
    return {
        "playerId": row["player_id"],
        "teamId": row["team_id"],
        "name": row["name"],
        "position": row["position"],
        "statLine": _format_stat_line(row, stat_type),
    }


def _passing_leader(connection, game_id: int) -> Optional[dict]:
    row = connection.execute(
        """
        SELECT pgs.player_id, pgs.team_id, p.name, p.position,
               pgs.passing_yards, pgs.passing_tds, pgs.interceptions
        FROM player_game_stats AS pgs
        JOIN players AS p ON p.id = pgs.player_id
        WHERE pgs.game_id = ?
        ORDER BY pgs.passing_yards DESC, pgs.passing_tds DESC
        LIMIT 1
        """,
        (game_id,),
    ).fetchone()
    if row is None or (row["passing_yards"] or 0) == 0:
        return None
    return _stat_payload(row, "passing")


def _rushing_leader(connection, game_id: int) -> Optional[dict]:
    row = connection.execute(
        """
        SELECT pgs.player_id, pgs.team_id, p.name, p.position,
               pgs.rushing_yards, pgs.rushing_tds
        FROM player_game_stats AS pgs
        JOIN players AS p ON p.id = pgs.player_id
        WHERE pgs.game_id = ?
        ORDER BY pgs.rushing_yards DESC, pgs.rushing_tds DESC
        LIMIT 1
        """,
        (game_id,),
    ).fetchone()
    if row is None or (row["rushing_yards"] or 0) == 0:
        return None
    return _stat_payload(row, "rushing")


def _receiving_leader(connection, game_id: int) -> Optional[dict]:
    row = connection.execute(
        """
        SELECT pgs.player_id, pgs.team_id, p.name, p.position,
               pgs.receiving_yards, pgs.receiving_tds
        FROM player_game_stats AS pgs
        JOIN players AS p ON p.id = pgs.player_id
        WHERE pgs.game_id = ?
        ORDER BY pgs.receiving_yards DESC, pgs.receiving_tds DESC
        LIMIT 1
        """,
        (game_id,),
    ).fetchone()
    if row is None or (row["receiving_yards"] or 0) == 0:
        return None
    return _stat_payload(row, "receiving")


def _defensive_leaders(connection, game_id: int) -> list[dict]:
    rows = connection.execute(
        """
        SELECT pgs.player_id, pgs.team_id, p.name, p.position,
               pgs.tackles, pgs.sacks, pgs.forced_turnovers,
               (pgs.tackles + (pgs.sacks * 2) + (pgs.forced_turnovers * 3)) AS impact
        FROM player_game_stats AS pgs
        JOIN players AS p ON p.id = pgs.player_id
        WHERE pgs.game_id = ?
        ORDER BY impact DESC
        LIMIT 3
        """,
        (game_id,),
    ).fetchall()
    leaders: list[dict] = []
    for row in rows:
        leaders.append(_stat_payload(row, "defense"))
    return leaders


def _injury_report(connection, game_id: int) -> list[dict]:
    rows = connection.execute(
        """
        SELECT p.id, p.name, p.position, p.team_id, t.name AS team_name, p.injury_status
        FROM players AS p
        JOIN player_game_stats AS s ON s.player_id = p.id AND s.game_id = ?
        JOIN teams AS t ON t.id = p.team_id
        WHERE p.injury_status IS NOT NULL AND p.injury_status <> 'healthy'
        """,
        (game_id,),
    ).fetchall()
    reports: list[dict] = []
    for row in rows:
        reports.append(
            {
                "playerId": row["id"],
                "name": row["name"],
                "teamId": row["team_id"],
                "teamName": row["team_name"],
                "position": row["position"],
                "status": row["injury_status"],
                "description": f"Listed as {row['injury_status']} after the game.",
                "expectedReturn": "1 week",
            }
        )
    return reports


def _weekly_results(connection, week: int) -> list[dict]:
    games = connection.execute(
        """
        SELECT g.id, g.week, g.played_at,
               ht.id AS home_id, ht.name AS home_name, ht.abbreviation AS home_abbr, g.home_score,
               at.id AS away_id, at.name AS away_name, at.abbreviation AS away_abbr, g.away_score
        FROM games AS g
        JOIN teams AS ht ON ht.id = g.home_team_id
        JOIN teams AS at ON at.id = g.away_team_id
        WHERE g.week = ?
        ORDER BY g.id
        """,
        (week,),
    ).fetchall()

    results: list[dict] = []
    for game in games:
        passing = _passing_leader(connection, game["id"])
        rushing = _rushing_leader(connection, game["id"])
        receiving = _receiving_leader(connection, game["id"])
        defenders = _defensive_leaders(connection, game["id"])
        injuries = _injury_report(connection, game["id"])

        results.append(
            {
                "gameId": game["id"],
                "week": game["week"],
                "playedAt": game["played_at"],
                "homeTeam": {
                    "id": game["home_id"],
                    "name": game["home_name"],
                    "abbreviation": game["home_abbr"],
                    "points": game["home_score"],
                },
                "awayTeam": {
                    "id": game["away_id"],
                    "name": game["away_name"],
                    "abbreviation": game["away_abbr"],
                    "points": game["away_score"],
                },
                "passingLeader": passing,
                "rushingLeader": rushing,
                "receivingLeader": receiving,
                "defensiveLeaders": defenders,
                "injuries": injuries,
            }
        )
    return results


class DepthChartEntryPayload(BaseModel):
    slot: str
    player_id: Optional[int] = Field(default=None, alias="playerId")

    model_config = ConfigDict(populate_by_name=True)


class DepthChartUpdateRequest(BaseModel):
    entries: list[DepthChartEntryPayload]


class SignFreeAgentRequest(BaseModel):
    team_id: int = Field(alias="teamId")
    player_id: int = Field(alias="playerId")


class TradeAsset(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: Literal["player", "pick"]
    player_id: Optional[int] = Field(default=None, alias="playerId")
    year: Optional[int] = None
    draft_round: Optional[int] = Field(default=None, alias="round")

    @model_validator(mode="after")
    def _validate_asset(self):
        if self.type == "player" and self.player_id is None:
            raise ValueError("Player asset requires playerId")
        if self.type == "pick" and (self.year is None or self.draft_round is None):
            raise ValueError("Pick asset requires year and round")
        return self


class TradeProposal(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    team_a: int = Field(alias="teamA")
    team_b: int = Field(alias="teamB")
    offer: list[TradeAsset]
    request: list[TradeAsset]


class WeekSimulationRequest(BaseModel):
    week: int
    mode: Literal["quick", "detailed"] = "quick"


# ---------------------------------------------------------------------------
# General endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "NFL GM Simulator backend is running"}


# ---------------------------------------------------------------------------
# Teams & players
# ---------------------------------------------------------------------------


@app.get("/teams")
def list_teams():
    query = """
        SELECT
            t.id,
            t.name,
            t.abbreviation,
            t.conference,
            t.division,
            COALESCE(AVG(CASE WHEN p.status = 'active' THEN p.overall_rating END), 0) AS rating,
            COALESCE(SUM(CASE WHEN p.status = 'active' THEN p.salary END), 0) AS salary_spent
        FROM teams AS t
        LEFT JOIN players AS p ON p.team_id = t.id
        GROUP BY t.id
        ORDER BY t.name
    """
    with get_connection() as connection:
        rows = connection.execute(query).fetchall()
    return [_serialize_team_row(row) for row in rows]


@app.get("/teams/{team_id}")
def get_team(team_id: int):
    with get_connection() as connection:
        team = connection.execute(
            "SELECT id, name, abbreviation, conference, division FROM teams WHERE id = ?",
            (team_id,),
        ).fetchone()
        if team is None:
            raise HTTPException(status_code=404, detail="Team not found")
        roster_rows = connection.execute(
            """
            SELECT id, name, position, overall_rating, age, team_id, status,
                   salary, contract_years, depth_chart_position
            FROM players
            WHERE team_id = ?
            ORDER BY COALESCE(depth_chart_order, 999), overall_rating DESC
            """,
            (team_id,),
        ).fetchall()
    return {**row_to_dict(team), "roster": [_serialize_player_row(row) for row in roster_rows]}


@app.get("/teams/{team_id}/roster")
def get_team_roster(team_id: int):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, name, position, overall_rating, age, team_id, status,
                   salary, contract_years, depth_chart_position
            FROM players
            WHERE team_id = ?
            ORDER BY COALESCE(depth_chart_order, 999), overall_rating DESC
            """,
            (team_id,),
        ).fetchall()
    return [_serialize_player_row(row) for row in rows]


@app.get("/teams/{team_id}/stats")
def get_team_stats(team_id: int):
    with get_connection() as connection:
        stats = team_stats_service.starters_stats(connection, team_id)
    return stats


@app.get("/players")
def list_players(team_id: Optional[int] = None, status: Optional[str] = None):
    clauses: list[str] = []
    params: list[object] = []
    if team_id is not None:
        clauses.append("team_id = ?")
        params.append(team_id)
    if status is not None:
        clauses.append("status = ?")
        params.append(status)
    sql = """
        SELECT id, name, position, overall_rating, age, team_id, status, salary, contract_years, depth_chart_position
        FROM players
    """
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY overall_rating DESC, name"
    with get_connection() as connection:
        rows = connection.execute(sql, params).fetchall()
    return [_serialize_player_row(row) for row in rows]


@app.get("/players/{player_id}")
def get_player(player_id: int):
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT id, name, position, overall_rating, age, team_id, status,
                   salary, contract_years, depth_chart_position
            FROM players
            WHERE id = ?
            """,
            (player_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Player not found")
    return _serialize_player_row(row)


# ---------------------------------------------------------------------------
# Depth chart management
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Free agency
# ---------------------------------------------------------------------------


@app.get("/free-agents")
def list_free_agents(year: Optional[int] = None):
    target_year = year or CURRENT_YEAR
    with get_connection() as connection:
        agents = roster_service.list_free_agents(connection, year=target_year)
    players = []
    for agent in agents:
        salary = float(agent.get("salary", 0))
        players.append(
            {
                "id": agent["id"],
                "name": agent["name"],
                "position": agent["position"],
                "overall": agent["overall_rating"],
                "age": agent["age"],
                "contractValue": round(salary / 1_000_000, 2),
                "contractYears": 1,
                "teamId": None,
                "depthChartSlot": None,
                "status": "free-agent",
            }
        )
    return {"year": target_year, "players": players}


@app.post("/free-agents/sign")
def sign_free_agent(payload: SignFreeAgentRequest):
    with get_connection() as connection:
        result = roster_service.sign_player(
            connection,
            team_id=payload.team_id,
            player_id=payload.player_id,
        )
        roster_service.validate_depth_requirements(connection, payload.team_id)
        connection.commit()
    player_payload = _serialize_player_row(result.player)
    message = f"{player_payload['name']} signed with {result.team['name']}"
    return {"status": "signed", "message": message, "player": player_payload, "team": result.team}


# ---------------------------------------------------------------------------
# Trades
# ---------------------------------------------------------------------------


def _trade_payload(proposal: TradeProposal) -> tuple[list[dict], list[dict]]:
    offer_payload = [asset.model_dump(by_alias=True, exclude_none=True) for asset in proposal.offer]
    request_payload = [asset.model_dump(by_alias=True, exclude_none=True) for asset in proposal.request]
    return offer_payload, request_payload


def _trade_response(result: TradeResult, *, message: str) -> dict:
    summary = asdict(result)
    return {
        "status": "accepted",
        "message": message,
        "offerValue": result.offer_value,
        "requestValue": result.request_value,
        "valueDelta": result.value_delta,
        "teamA": summary["team_a"],
        "teamB": summary["team_b"],
        "teamA_sent": summary["team_a_sent"],
        "teamA_received": summary["team_a_received"],
        "teamB_sent": summary["team_b_sent"],
        "teamB_received": summary["team_b_received"],
    }


@app.post("/trades/propose")
def propose_trade(proposal: TradeProposal):
    offer_payload, request_payload = _trade_payload(proposal)
    with get_connection() as connection:
        try:
            result = trade_service.execute_trade(
                connection,
                team_a_id=proposal.team_a,
                team_b_id=proposal.team_b,
                offer=offer_payload,
                request=request_payload,
            )
        except HTTPException as exc:
            connection.rollback()
            return {"status": "rejected", "message": str(exc.detail)}
        connection.rollback()
    return {
        "status": "accepted",
        "message": "Trade proposal accepted",
        "offerValue": result.offer_value,
        "requestValue": result.request_value,
        "valueDelta": result.value_delta,
    }


@app.post("/trades/execute")
def execute_trade(proposal: TradeProposal):
    offer_payload, request_payload = _trade_payload(proposal)
    with get_connection() as connection:
        result = trade_service.execute_trade(
            connection,
            team_a_id=proposal.team_a,
            team_b_id=proposal.team_b,
            offer=offer_payload,
            request=request_payload,
        )
        connection.commit()
    return _trade_response(result, message="Trade executed successfully")


# ---------------------------------------------------------------------------
# Games & simulation
# ---------------------------------------------------------------------------


@app.get("/games")
def list_games(week: Optional[int] = None, team_id: Optional[int] = None):
    clauses: list[str] = []
    params: list[object] = []
    if week is not None:
        clauses.append("g.week = ?")
        params.append(week)
    if team_id is not None:
        clauses.append("(g.home_team_id = ? OR g.away_team_id = ?)")
        params.extend([team_id, team_id])
    sql = """
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
    """
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY g.week, g.id"
    with get_connection() as connection:
        rows = connection.execute(sql, params).fetchall()
    return [row_to_dict(row) for row in rows]


@app.get("/games/{game_id}")
def get_game(game_id: int):
    with get_connection() as connection:
        row = connection.execute(
            """
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
            """,
            (game_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return row_to_dict(row)


@app.get("/games/week/{week}")
def week_results(week: int):
    with get_connection() as connection:
        results = _weekly_results(connection, week)
    return results


@app.post("/simulate-week")
def simulate_week(request: WeekSimulationRequest):
    detailed = request.mode == "detailed"
    with get_connection() as connection:
        box_scores = simulation_service.simulate_week(
            connection,
            week=request.week,
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
            entries.append(
                f"Q{play['quarter']} {play['clock']} - {play['description']} (Score {score.get('home')}-{score.get('away')})"
            )
    return entries


@app.get("/games/box-scores")
def list_box_scores(week: Optional[int] = None, team_id: Optional[int] = None):
    with get_connection() as connection:
        payload = box_score_service.box_scores(connection, week=week, team_id=team_id)
    return payload


@app.get("/games/{game_id}/box-score")
def get_box_score(game_id: int):
    with get_connection() as connection:
        payload = box_score_service.box_score(connection, game_id)
    return payload


# ---------------------------------------------------------------------------
# Narratives & standings
# ---------------------------------------------------------------------------


@app.get("/narratives")
def list_narratives(week: Optional[int] = None):
    with get_connection() as connection:
        items = narrative_service.list_narratives(connection, week=week)
    return items


@app.get("/standings")
def get_standings():
    query = """
        WITH completed AS (
            SELECT *
            FROM games
            WHERE played_at IS NOT NULL OR home_score <> 0 OR away_score <> 0
        ),
        results AS (
            SELECT
                home_team_id AS team_id,
                CASE WHEN home_score > away_score THEN 1 ELSE 0 END AS wins,
                CASE WHEN home_score < away_score THEN 1 ELSE 0 END AS losses,
                CASE WHEN home_score = away_score THEN 1 ELSE 0 END AS ties
            FROM completed
            UNION ALL
            SELECT
                away_team_id AS team_id,
                CASE WHEN away_score > home_score THEN 1 ELSE 0 END AS wins,
                CASE WHEN away_score < home_score THEN 1 ELSE 0 END AS losses,
                CASE WHEN home_score = away_score THEN 1 ELSE 0 END AS ties
            FROM completed
        )
        SELECT
            t.id AS teamId,
            t.name AS name,
            t.abbreviation AS abbreviation,
            t.conference AS conference,
            t.division AS division,
            COALESCE(SUM(r.wins), 0) AS wins,
            COALESCE(SUM(r.losses), 0) AS losses,
            COALESCE(SUM(r.ties), 0) AS ties
        FROM teams AS t
        LEFT JOIN results AS r ON r.team_id = t.id
        GROUP BY t.id
        ORDER BY t.conference, t.division, wins DESC, losses ASC, ties DESC, t.name
    """
    with get_connection() as connection:
        rows = connection.execute(query).fetchall()
    standings: list[dict] = []
    for row in rows:
        games_played = row["wins"] + row["losses"] + row["ties"]
        win_pct = round(row["wins"] / games_played, 3) if games_played else 0.0
        payload = row_to_dict(row)
        payload["winPct"] = win_pct
        standings.append(payload)
    return standings
