from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db import get_connection

app = FastAPI(title="NFL GM Simulator API", version="0.1.0")

# --- Allow frontend (localhost:5173 or 5174) to access backend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}

# --- Core data endpoints ---

@app.get("/players")
def get_players(limit: int = 50):
    """Return players from the ratings table."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM ratings LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

@app.get("/teams")
def get_teams():
    """Return unique teams derived from ratings table."""
    with get_connection() as conn:
        rows = conn.execute("SELECT DISTINCT team FROM ratings ORDER BY team;").fetchall()
        return [r["team"] for r in rows]

@app.get("/depth_chart")
def get_depth_chart():
    """Return depth chart entries."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM depth_charts;").fetchall()
        return [dict(r) for r in rows]

@app.get("/schedule")
def get_schedule():
    """Return full season schedule."""
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM schedule;").fetchall()
        return [dict(r) for r in rows]

@app.get("/free_agents")
def get_free_agents(year: int | None = None):
    """Return free agents for a given year or all if unspecified."""
    table = f"free_agents_{year}" if year else "free_agents_2025"
    with get_connection() as conn:
        try:
            rows = conn.execute(f"SELECT * FROM {table};").fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            return {"error": str(e), "table": table}

