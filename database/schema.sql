PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    abbreviation TEXT NOT NULL UNIQUE,
    conference TEXT NOT NULL,
    division TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    position TEXT NOT NULL,
    team TEXT NOT NULL DEFAULT 'FA',
    ovr INTEGER NOT NULL DEFAULT 60,
    spd INTEGER,
    strength INTEGER,
    agi INTEGER,
    cod INTEGER,
    inj INTEGER,
    awr INTEGER,
    overall_rating INTEGER NOT NULL,
    age INTEGER DEFAULT 25,
    team_id INTEGER,
    depth_chart_position TEXT,
    depth_chart_order INTEGER,
    status TEXT DEFAULT 'active',
    salary INTEGER DEFAULT 0,
    contract_years INTEGER DEFAULT 0,
    free_agent_year INTEGER,
    injury_status TEXT DEFAULT 'healthy',
    FOREIGN KEY (team_id) REFERENCES teams (id)
);

CREATE TABLE IF NOT EXISTS depth_charts (
    id INTEGER PRIMARY KEY,
    team TEXT NOT NULL,
    position TEXT NOT NULL,
    player_name TEXT NOT NULL,
    depth INTEGER NOT NULL,
    player_id INTEGER,
    FOREIGN KEY (player_id) REFERENCES players (id)
);

CREATE TABLE IF NOT EXISTS free_agents (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    position TEXT NOT NULL,
    age REAL,
    yoe INTEGER,
    prev_team TEXT,
    prev_aav REAL,
    contract_type TEXT,
    market_value REAL,
    year INTEGER NOT NULL,
    player_id INTEGER,
    FOREIGN KEY (player_id) REFERENCES players (id)
);

CREATE TABLE IF NOT EXISTS schedule (
    id INTEGER PRIMARY KEY,
    team TEXT NOT NULL,
    week INTEGER NOT NULL,
    opponent TEXT NOT NULL,
    home_game INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY,
    week INTEGER NOT NULL,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    home_score INTEGER DEFAULT 0,
    away_score INTEGER DEFAULT 0,
    played_at TEXT,
    FOREIGN KEY (home_team_id) REFERENCES teams (id),
    FOREIGN KEY (away_team_id) REFERENCES teams (id)
);

CREATE TABLE IF NOT EXISTS draft_picks (
    id INTEGER PRIMARY KEY,
    team_id INTEGER NOT NULL,
    year INTEGER NOT NULL,
    round INTEGER NOT NULL,
    original_team_id INTEGER NOT NULL,
    FOREIGN KEY (team_id) REFERENCES teams (id),
    FOREIGN KEY (original_team_id) REFERENCES teams (id)
);

CREATE TABLE IF NOT EXISTS team_game_stats (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    total_yards INTEGER DEFAULT 0,
    turnovers INTEGER DEFAULT 0,
    FOREIGN KEY (game_id) REFERENCES games (id),
    FOREIGN KEY (team_id) REFERENCES teams (id)
);

CREATE TABLE IF NOT EXISTS player_game_stats (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    passing_yards INTEGER DEFAULT 0,
    passing_tds INTEGER DEFAULT 0,
    interceptions INTEGER DEFAULT 0,
    rushing_yards INTEGER DEFAULT 0,
    rushing_tds INTEGER DEFAULT 0,
    receiving_yards INTEGER DEFAULT 0,
    receiving_tds INTEGER DEFAULT 0,
    tackles INTEGER DEFAULT 0,
    sacks REAL DEFAULT 0,
    forced_turnovers INTEGER DEFAULT 0,
    FOREIGN KEY (game_id) REFERENCES games (id),
    FOREIGN KEY (player_id) REFERENCES players (id),
    FOREIGN KEY (team_id) REFERENCES teams (id)
);
CREATE TABLE IF NOT EXISTS game_events (
    id INTEGER PRIMARY KEY,
    game_id INTEGER NOT NULL,
    sequence INTEGER NOT NULL,
    quarter INTEGER NOT NULL,
    clock TEXT NOT NULL,
    team_id INTEGER,
    player_id INTEGER,
    description TEXT NOT NULL,
    highlight_type TEXT NOT NULL,
    impact TEXT,
    points INTEGER NOT NULL,
    home_score_after INTEGER NOT NULL,
    away_score_after INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (game_id) REFERENCES games (id),
    FOREIGN KEY (team_id) REFERENCES teams (id),
    FOREIGN KEY (player_id) REFERENCES players (id)
);
CREATE INDEX IF NOT EXISTS idx_game_events_game_sequence ON game_events (game_id, sequence);
CREATE TABLE IF NOT EXISTS week_narratives (
    id INTEGER PRIMARY KEY,
    week INTEGER NOT NULL,
    headline TEXT NOT NULL,
    body TEXT,
    game_id INTEGER,
    tags TEXT,
    sequence INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (game_id) REFERENCES games (id)
);
CREATE INDEX IF NOT EXISTS idx_week_narratives_week ON week_narratives (week, sequence);
