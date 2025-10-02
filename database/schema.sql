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
