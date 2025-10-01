# NFL GM Simulator Project Overview

## 1. High-Level Architecture

```mermaid
flowchart LR
    subgraph Client[React + Tailwind Frontend]
        UI[UI Components]
        State[Redux Toolkit / Zustand State]
        UI -->|REST| API
    end

    subgraph Server[FastAPI Backend]
        Router[API Routers]
        Services[Service Layer]
        Engine[Simulation Engine]
        DBLayer[DB Models & Repositories]
    end

    subgraph Data[SQLite (MVP) / PostgreSQL]
        Schema[(Normalized Schema)]
    end

    Files[Rules & Data Files]

    UI -->|HTTPS JSON| Router
    Router --> Services --> Engine
    Services --> DBLayer --> Schema
    Engine --> Files
    Engine --> DBLayer
    DBLayer --> Engine
    Router --> Files
```

- **Frontend**: React SPA served via Vite/CRA, Tailwind for styling, communicates with backend via REST.
- **Backend**: FastAPI chosen for its fast development, async support, Pydantic models, and strong typing conducive to deterministic simulation engines. Python ecosystem aligns with rules-based simulation using structured data files.
- **Database**: SQLite for MVP persistence, easily migrated to PostgreSQL via SQLAlchemy.
- **File-Based Inputs**: `ratings.txt`, `depth_charts.txt`, `free_agents.txt`, `gamerules.txt`, `simulationrules.txt` feed deterministic engine.

## 2. File Structure

```
FootballSimulator/
├── README.md
├── docs/
│   └── project_overview.md
├── backend/
│   ├── app.py
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   ├── api/
│   │   ├── dependencies.py
│   │   ├── routes/
│   │   │   ├── players.py
│   │   │   ├── teams.py
│   │   │   ├── games.py
│   │   │   ├── transactions.py
│   │   │   └── simulation.py
│   ├── services/
│   │   ├── simulation_service.py
│   │   ├── roster_service.py
│   │   ├── transaction_service.py
│   │   ├── draft_service.py
│   │   └── playoff_service.py
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── rules_loader.py
│   │   ├── scheduler.py
│   │   ├── game_simulator.py
│   │   ├── stats_tracker.py
│   │   ├── season_manager.py
│   │   ├── narrative_generator.py
│   │   └── progression.py
│   ├── repositories/
│   │   ├── base.py
│   │   ├── players.py
│   │   ├── teams.py
│   │   ├── games.py
│   │   ├── stats.py
│   │   ├── transactions.py
│   │   └── draft_picks.py
│   ├── models/
│   │   ├── db/
│   │   │   ├── player.py
│   │   │   ├── team.py
│   │   │   ├── game.py
│   │   │   ├── stat.py
│   │   │   ├── transaction.py
│   │   │   └── draft_pick.py
│   │   └── schemas/
│   │       ├── player.py
│   │       ├── team.py
│   │       ├── game.py
│   │       ├── transaction.py
│   │       └── draft.py
│   ├── data/
│   │   ├── ratings.txt
│   │   ├── depth_charts.txt
│   │   ├── free_agents.txt
│   │   ├── gamerules.txt
│   │   └── simulationrules.txt
│   └── tests/
│       ├── conftest.py
│       ├── unit/
│       └── integration/
└── frontend/
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── src/
    │   ├── main.tsx
    │   ├── App.tsx
    │   ├── api/
    │   │   └── client.ts
    │   ├── store/
    │   │   ├── index.ts
    │   │   ├── slices/
    │   │   │   ├── teamsSlice.ts
    │   │   │   ├── playersSlice.ts
    │   │   │   ├── gamesSlice.ts
    │   │   │   └── transactionsSlice.ts
    │   ├── components/
    │   │   ├── Dashboard/
    │   │   │   └── Dashboard.tsx
    │   │   ├── Standings/
    │   │   │   └── StandingsTable.tsx
    │   │   ├── Roster/
    │   │   │   ├── RosterView.tsx
    │   │   │   └── DepthChartManager.tsx
    │   │   ├── GameResults/
    │   │   │   └── GameSummary.tsx
    │   │   ├── Transactions/
    │   │   │   ├── TradeCenter.tsx
    │   │   │   └── FreeAgency.tsx
    │   │   └── Shared/
    │   │       ├── Layout.tsx
    │   │       └── Loader.tsx
    │   ├── pages/
    │   │   ├── DashboardPage.tsx
    │   │   ├── StandingsPage.tsx
    │   │   ├── RosterPage.tsx
    │   │   ├── TransactionsPage.tsx
    │   │   ├── SchedulePage.tsx
    │   │   └── DraftPage.tsx
    │   └── styles/
    │       └── index.css
    └── tests/
        └── e2e/
```

## 3. Backend Modules

- **Simulation Engine**
  - `rules_loader.py`: Parses deterministic rules files into structured objects.
  - `scheduler.py`: Generates season schedule, playoffs, and offseason events.
  - `game_simulator.py`: Runs weekly simulations using rules, player ratings, depth charts.
  - `stats_tracker.py`: Records stats, player performance, aggregates season totals.
  - `narrative_generator.py`: Produces textual narratives from simulation results.
  - `progression.py`: Applies aging, development, regression post-season per rules.
  - `season_manager.py`: Coordinates season phases (regular season, playoffs, offseason).

- **Roster Manager**
  - `roster_service.py`: CRUD for rosters, enforce depth chart constraints.
  - `engine/depth_chart_validator.py` (implied helper): ensures positions filled.
  - Integrates with simulation engine to update active rosters weekly.

- **Transaction System**
  - `transaction_service.py`: Handles trades, signings, releases, contract logic.
  - Validates salary cap rules from `gamerules.txt`.
  - Updates player/team associations and persists transactions history.

- **Playoff/Draft Logic**
  - `playoff_service.py`: Seeds teams, simulates playoff bracket, Super Bowl results.
  - `draft_service.py`: Manages draft order, picks, rookies generation, contract slottings.
  - Offseason workflow: retirements, free agency, draft, training camp progression.

## 4. Frontend Components

- **Dashboard**
  - `DashboardPage`, `Dashboard` component showing next game, team record, key stats.
  - Widgets for injury reports and recent transactions.

- **Standings**
  - `StandingsPage`, `StandingsTable` with conference/division filters.
  - Uses charts (Recharts) for win streaks.

- **Roster Screen**
  - `RosterPage`, `RosterView` to view players by position, stats, contract info.
  - `DepthChartManager` drag-and-drop (react-beautiful-dnd) to manage depth charts.

- **Game Results**
  - `SchedulePage`, `GameSummary` for weekly box scores, highlight narratives.
  - Modal for detailed player stats.

- **Transaction UI**
  - `TransactionsPage` with tabs: Trades, Free Agency, Draft.
  - `TradeCenter` for proposing/validating trades with cap impact preview.
  - `FreeAgency` to browse signable players, filter by position.
  - Draft board view with pick tracking.

## 5. Database Schema

| Table | Key Columns | Notes |
|-------|-------------|-------|
| `teams` | `id`, `name`, `city`, `abbreviation`, `division`, `conference`, `overall_rating` | Seeded from league data. |
| `players` | `id`, `team_id`, `first_name`, `last_name`, `position`, `age`, `rating_overall`, `contract_years`, `contract_value`, `traits` | `team_id` nullable for free agents. |
| `depth_chart_slots` | `id`, `team_id`, `position`, `player_id`, `order` | Tracks lineup priority. |
| `games` | `id`, `season_year`, `week`, `home_team_id`, `away_team_id`, `home_score`, `away_score`, `status`, `is_playoff` | Records scheduled and simulated games. |
| `player_game_stats` | `id`, `game_id`, `player_id`, `stat_blob` (JSON) | Stores per-game stats (passing, rushing, etc.). |
| `team_season_stats` | `id`, `team_id`, `season_year`, `wins`, `losses`, `ties`, `points_for`, `points_against`, `streak` | Aggregated standings data. |
| `transactions` | `id`, `type`, `team_from_id`, `team_to_id`, `player_id`, `details`, `created_at` | Covers trades, signings, releases. |
| `draft_picks` | `id`, `season_year`, `round`, `overall_pick`, `original_team_id`, `current_team_id`, `player_id` | Tracks draft rights and outcomes. |
| `narratives` | `id`, `game_id`, `title`, `body`, `created_at` | Optional for storytelling. |
| `saves` | `id`, `user_id`, `save_name`, `state_snapshot` (JSON), `created_at`, `updated_at` | Persist save states for multiple careers. |
| `users` (future) | `id`, `email`, `password_hash` | For multi-user support if desired. |

## 6. Development Phases

1. **Phase 1 – MVP**
   - Implement core backend API: load rules, simulate weekly games, basic roster management, transactions, persistent saves.
   - Frontend: Dashboard, roster view, schedule/results, basic transactions.
   - Single-season loop with deterministic results.

2. **Phase 2 – Season Completion**
   - Add playoffs, Super Bowl simulation, offseason workflow (draft, free agency).
   - Implement player progression and aging, contract management UI.
   - Improve narratives and statistics presentation.

3. **Phase 3 – Depth & Realism Enhancements**
   - Expand rules engine for injuries, advanced stats, coaching strategies.
  - Add scouting, draft combine, player morale systems.
   - Transition to PostgreSQL, implement authentication, multi-save support.

4. **Phase 4 – Live Service Features**
   - Online sharing of custom rosters, cloud saves.
   - Real-time updates, modding support, analytics dashboards.

## 7. Dependencies

- **Frontend**
  - React, TypeScript, Vite, Tailwind CSS
  - State: Redux Toolkit or Zustand
  - Data fetching: Axios, React Query
  - UI enhancements: Headless UI, Heroicons, Recharts, react-beautiful-dnd
  - Testing: Jest, React Testing Library, Cypress

- **Backend**
  - FastAPI, Uvicorn, SQLAlchemy, Alembic, Pydantic
  - Simulation support: Pandas (optional), NumPy for calculations
  - Auth/security: Passlib, PyJWT (future)
  - Testing: Pytest, httpx, pytest-asyncio

- **Dev Tooling**
  - Pre-commit hooks (black, isort, flake8, mypy)
  - Docker & docker-compose for environment parity

## 8. How to Run the Project

```bash
# Clone repo
git clone <repo-url>
cd FootballSimulator

# Backend setup
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload

# Frontend setup
cd frontend
npm install
npm run dev
```

- Access app at `http://localhost:5173` (Vite default).
- Backend API served at `http://localhost:8000`.

