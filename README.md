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

# Load the SQLite database from the parsed CSVs
make seed

# Start the API (alias: `make run-backend`)
make run
```

The API will be available at `http://localhost:8000`; the `/health` endpoint returns `{ "status": "ok" }` when running. The seeding step ingests `shared/data/ratings.csv`, `depth_charts.csv`, `schedule.csv`, and the 2025/2026 free agent CSVs into SQLite via SQLAlchemy models so runtime code never reparses the CSVs.

**Backend QA helpers**

```bash
cd backend
make lint   # black, isort, flake8, mypy
make test   # pytest with coverage enforcement
```

Use `TEST_TARGET=backend/tests/test_seed_ingestion.py make test` to focus on the ingestion regression checks when iterating on the CSV loader.

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

### End-to-end testing

Playwright runs a deterministic GM loop against the MSW-backed seed data found in `frontend/e2e/test_seed.json`. The worker intercepts REST calls so the flows succeed even when the FastAPI server is offline.

1. **Backend** – `cd backend && make run`
2. **Frontend** – `cd frontend && npm run dev`
3. **E2E suite** – `cd frontend && npm run test:e2e`

The tests launch the dev server with `VITE_API_MODE=live` and spin up the MSW worker automatically, ensuring free agent signings, trades, depth chart updates, simulations, and standings all execute in the browser.

## Regression suite

We maintain placeholder regression tests to capture known bugs and flip them to permanent guards once the fixes ship.

- **Backend** – `cd backend && pytest -k regression`
- **Frontend** – `cd frontend && npx vitest run tests/regression.test.ts`

Both suites currently contain skipped/XFailed tests that describe the defect being tracked. Remove the skip markers and add concrete assertions when the issue is resolved.

## Continuous Integration

GitHub Actions enforces a two-job pipeline defined in `.github/workflows/ci.yml`:

1. **Backend job** (Python 3.11 and 3.12 matrix) – installs dependencies with pip caching, runs `make lint`, and executes the coverage-enforced `make test` target.
2. **Frontend job** (Node 18 and 20 matrix) – installs npm dependencies with caching, runs `npm run lint`, `npm run typecheck`, `npm run test`, and the Playwright harness `npm run test:e2e` (including browser installation on CI nodes).

Pull requests must go green on both jobs before merging.

## Coverage enforcement

- **Backend** – `make test` wraps pytest with `coverage` to emit `coverage.xml`/`coverage.json` and fails the build if line coverage drops below 70% or branch coverage below 60%. The XML artifact is uploaded by CI for review.
- **Frontend** – Vitest emits `coverage/lcov.info` during `npm run test`, enforcing 70% line and 60% branch coverage thresholds. Playwright produces V8 coverage artifacts under `playwright-coverage/` during `npm run test:e2e`.

If you need to inspect coverage locally, run:

```bash
cd backend && make test  # generates coverage.xml and coverage.json
cd frontend && npm run test && npm run test:e2e
```

Both commands regenerate their reports so you can view them in your preferred coverage tooling.
