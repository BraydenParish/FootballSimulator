# NFL GM Simulator Monorepo

This repository contains the scaffolding for the NFL GM Simulator project. The
monorepo is organized into dedicated workspaces for the FastAPI backend, React +
Tailwind frontend, database assets, and shared utilities used across services.

## Project Structure

```text
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

The API will be available at `http://localhost:8000`, and `GET /health` returns
`{ "status": "ok" }` when the service is running. After seeding the database, the
backend serves deterministic placeholder data so the frontend can render consistent
results while development continues. Key endpoints now include:

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/teams` | List every NFL team and its current roster. |
| GET | `/teams/{teamId}` | Retrieve a single team including its players. |
| GET | `/teams/{teamId}/stats` | Starter stats generated from simulations. |
| GET | `/players` | Browse the player pool; filter by `teamId` or `status`. |
| GET | `/free-agents` | View the current free-agent market for the season. |
| POST | `/teams/{teamId}/sign` | Sign a free agent while checking depth rules. |
| GET/POST | `/teams/{teamId}/depth-chart` | Inspect or update depth slots. |
| POST | `/trade/validate` | Validate a proposed trade against roster rules. |
| POST | `/trade` | Execute an approved trade and persist roster changes. |
| GET | `/games` | Review scheduled or completed games by week or team. |
| GET | `/games/{gameId}` | Inspect one scheduled or completed game summary. |
| POST | `/simulate-week` | Simulate a week with scores, stats, and narratives. |

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open the dashboard at `http://localhost:5173` to interact with the GM control center UI. When both services are running you can simulate weeks, review results, and manage your roster end-to-end.

### Full-stack workflow

1. Start the backend in one terminal (`uvicorn app.main:app --reload`).
2. Start the frontend in another terminal (`npm run dev`).
3. Load `http://localhost:5173` – the dashboard greets you with a matchup preview, roster summary, and quick links to roster management pages.
4. Click **Simulate Week** to trigger a quick simulation. The UI will navigate to the **Results** page with box scores, stat leaders, and injuries for the selected week. Use the Previous/Next buttons to browse other weeks at any time.
5. Use the navigation bar to reach:
   - **Results** – recap the latest week using `/games/week/{week}` data.
   - **Depth Chart** – reorder starters with dropdown swaps using `/teams/{id}/depth-chart` (GET + POST) to keep lineups in sync.
   - **Free Agency** – filter and sign available free agents from `/free-agents`; commit signings with `POST /free-agents/sign`.
   - **Trade Center** – build multi-player trades, validate them through `POST /trades/propose`, and commit approved deals via `POST /trades/execute`.
   - **Standings** – view division tables powered by `/standings`, including win-percentage tiebreakers and highlighted leaders.

All transactional pages fall back to seeded demo data if live endpoints are unavailable, ensuring the UI remains interactive.

### Database Seeding

```bash
make seed
```

The `make seed` target provisions the SQLite database using the schema defined in
`database/schema.sql` and populates the tables with the roster, free-agent,
schedule, and narrative placeholder data from `shared/data`. Once seeded,
endpoints such as `/teams`, `/free-agents`, `/trade`, `/games`, and `/simulate-week`
read from the database for deterministic responses.

### Running the test suite

Backend tests rely on the seeded SQLite database. From the repository root run:

```bash
pytest
```

The tests cover week simulations, free agency, trades, standings, and box score retrievals.
