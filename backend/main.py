from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Dict

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
    # TODO: Load from database
    return [{"id": 1, "name": "Team A"}, {"id": 2, "name": "Team B"}]

@app.get("/teams/{team_id}")
def get_team(team_id: int):
    # TODO: Query DB for team + depth chart
    return {"id": team_id, "name": f"Team {team_id}", "roster": []}

# ---- Players ----
@app.get("/players/{player_id}")
def get_player(player_id: int):
    # TODO: Query DB for player
    return {"id": player_id, "name": f"Player {player_id}", "ovr": 80, "pos": "QB"}

# ---- Games ----
class GameRequest(BaseModel):
    home_team: int
    away_team: int
    week: int

@app.post("/simulate-game")
def simulate_game(request: GameRequest):
    # TODO: implement simulation logic using ratings & rules
    return {
        "week": request.week,
        "home_team": request.home_team,
        "away_team": request.away_team,
        "final_score": f"{request.home_team} 27 - {request.away_team} 24",
        "narrative": "It was a close battle decided in overtime!"
    }

@app.post("/simulate-week")
def simulate_week(week: int):
    # TODO: simulate all games for this week
    return {"week": week, "results": []}

# ---- Standings ----
@app.get("/standings")
def get_standings():
    # TODO: Query DB for team records
    return [
        {"team": "Team A", "wins": 3, "losses": 1},
        {"team": "Team B", "wins": 2, "losses": 2}
    ]
