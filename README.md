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

The API will be available at `http://localhost:8000`; the `/health` endpoint returns `{ "status": "ok" }` when running. The frontend defaults to mock data, but setting `VITE_API_MODE=api` will point the UI at the live backend once the service is running.

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
python database/load_data.py
```

The command initializes `database/nfl_gm_sim.db` using the schema defined in `database/schema.sql` and seeds the tables with the placeholder roster and free-agent data found in `shared/data`.

## Frontend tests

Vitest powers the integration tests that cover simulations, roster moves, depth chart persistence, trades, and standings updates. Pytest exercises the FastAPI endpoints for simulations, free agency, depth charts, and trades to keep backend workflows green.

```bash
cd frontend
npm run test
```

The tests exercise the React Query + mock data store flow, so they remain green even when backend parsers are still being wired up.
