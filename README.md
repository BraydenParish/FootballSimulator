# NFL GM Simulator Monorepo

This repository contains the early scaffolding for the NFL GM Simulator project. The monorepo is organized into dedicated workspaces for the FastAPI backend, React + Tailwind frontend, database assets, and shared utilities used across services.

## Project Structure

```
backend/   # FastAPI application
frontend/  # React + Tailwind dashboard
database/  # SQLite schema, initialization, and loaders
shared/    # Shared data files, constants, and parsing utilities
```

## Getting Started

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`. After seeding the database the service reads the SQLite-backed rosters, schedule, and transaction data to drive every response, and the React frontend now consumes those live results instead of local mocks. Use the `/health` endpoint to confirm the server is ready before pointing the dashboard at it. Key endpoints now include:

| Endpoint | Description |
| --- | --- |
| `GET /health` | Service readiness check that returns `{ "status": "ok" }`. |
| `GET /teams` | List all NFL teams in the simulation. |
| `POST /simulate-week` | Simulate an entire week, returning box scores, player stats, injuries, and narratives. |
| `GET /games/week/{week}` | Retrieve the saved box scores for a specific week. |
| `GET /standings` | Compute league standings from the played games. |
| `GET /free-agents` / `POST /teams/{teamId}/sign` | Manage free agent signings. |
| `POST /trade` | Execute validated trades between teams. |
| `GET/POST /teams/{teamId}/depth-chart` | Inspect or update depth chart assignments. |

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the dashboard at `http://localhost:5173` to view the placeholder GM control center UI.

### Database Seeding

```bash
python database/load_data.py
```

The command initializes `database/nfl_gm_sim.db` using the schema defined in `database/schema.sql` and seeds the tables with the latest roster, schedule, and free-agent data found in `shared/data`. Run this before starting the backend so the API can serve the database-driven responses consumed by the frontend and automated simulations.

### Running the test suite

Backend tests rely on the seeded SQLite database. From the repository root run:

```bash
pytest
```

The tests cover week simulations, free agency, trades, standings, and box score retrievals.
