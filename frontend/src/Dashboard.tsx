import { ReactNode, useEffect, useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const FOCUS_TEAM_ID = 1;

const placeholderLastResult = {
  week: 2,
  location: "Home",
  opponentName: "Cincinnati Bengals",
  focusScore: 27,
  opponentScore: 20,
  outcomeLabel: "Win",
};

const placeholderBoxScore = {
  quarterback: { name: "Josh Allen", yards: 312, touchdowns: 3, interceptions: 1 },
  runningBack: { name: "James Cook", yards: 94, touchdowns: 1 },
  receiver: { name: "Stefon Diggs", yards: 124, touchdowns: 1 },
  defender: { name: "Von Miller", sacks: 2, interceptions: 0 },
  teamTotals: { yards: 412, turnovers: 2 },
};

const placeholderPlayerStats = {
  offense: [
    { name: "Josh Allen", statLine: "312 PASS YDS · 3 TD · 1 INT" },
    { name: "James Cook", statLine: "94 RUSH YDS · 1 TD" },
    { name: "Stefon Diggs", statLine: "8 REC · 124 YDS · 1 TD" },
  ],
  defense: [
    { name: "Von Miller", statLine: "2 SACKS" },
    { name: "Matt Milano", statLine: "8 TACK · 1 FF" },
  ],
};

const placeholderStandings = [
  { name: "Buffalo Bills", record: "2-0" },
  { name: "Kansas City Chiefs", record: "2-0" },
  { name: "Cincinnati Bengals", record: "1-1" },
];

const placeholderGameLog = [
  "Q1 10:25 – Allen finds Diggs for a 42-yard touchdown.",
  "Q2 03:11 – Defense forces a fumble recovered by Milano.",
  "Q3 07:45 – Cook punches in a 6-yard rushing score.",
  "Q4 01:58 – Bass drills a 45-yard field goal to seal it.",
];

const KEY_DEPTH_CHART_SLOTS = ["QB1", "RB1", "WR1", "TE1", "LB1", "CB1"] as const;

type StandingRow = {
  id: number;
  name: string;
  abbreviation: string;
  conference: string;
  division: string;
  wins: number;
  losses: number;
  ties: number;
};

type GameRow = {
  id: number;
  week: number;
  home_team_id: number;
  away_team_id: number;
  home_score: number;
  away_score: number;
  played_at: string | null;
  home_team_name: string;
  home_team_abbreviation: string;
  away_team_name: string;
  away_team_abbreviation: string;
};

type PlayerRow = {
  id: number;
  name: string;
  position: string;
  overall_rating: number;
  age: number;
  team_id: number | null;
  depth_chart_position: string | null;
  status: string;
};

type ModalProps = {
  title: string;
  onClose: () => void;
  children: ReactNode;
  footer?: ReactNode;
};

function Modal({ title, onClose, children, footer }: ModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 px-4 py-6">
      <div className="w-full max-w-lg rounded-2xl border border-white/10 bg-slate-900 p-6 shadow-2xl">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h3 className="text-lg font-semibold text-white">{title}</h3>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full bg-white/10 p-2 text-slate-300 transition hover:bg-white/20"
            aria-label="Close"
          >
            ×
          </button>
        </div>
        <div className="mt-4 space-y-4 text-sm text-slate-200">{children}</div>
        {footer ? <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-end">{footer}</div> : null}
      </div>
    </div>
  );
}

const mockTeamStats = [
  { label: "Overall", value: 86 },
  { label: "Offense", value: 89 },
  { label: "Defense", value: 84 },
  { label: "Special Teams", value: 81 },
];

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl bg-slate-900 p-4 shadow-lg">
      <p className="text-sm font-medium text-slate-400">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-white">{value}</p>
    </div>
  );
}

function Dashboard() {
  const totalRating = useMemo(
    () => Math.round(mockTeamStats.reduce((sum, stat) => sum + stat.value, 0) / mockTeamStats.length),
    []
  );
  const [standings, setStandings] = useState<StandingRow[]>([]);
  const [standingsLoading, setStandingsLoading] = useState(true);
  const [standingsError, setStandingsError] = useState<string | null>(null);
  const [games, setGames] = useState<GameRow[]>([]);
  const [gamesLoading, setGamesLoading] = useState(true);
  const [gamesError, setGamesError] = useState<string | null>(null);
  const [players, setPlayers] = useState<PlayerRow[]>([]);
  const [playersLoading, setPlayersLoading] = useState(true);
  const [playersError, setPlayersError] = useState<string | null>(null);

  const [isSimModalOpen, setSimModalOpen] = useState(false);
  const [isDetailedSimModalOpen, setDetailedSimModalOpen] = useState(false);
  const [isBoxScoreOpen, setBoxScoreOpen] = useState(false);
  const [isPlayerStatsOpen, setPlayerStatsOpen] = useState(false);
  const [simulationResult, setSimulationResult] = useState<string | null>(null);

  useEffect(() => {
    let isActive = true;

    async function loadStandings() {
      try {
        setStandingsLoading(true);
        const response = await fetch(`${API_BASE_URL}/standings`);
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }

        const data = (await response.json()) as StandingRow[];
        if (!Array.isArray(data)) {
          throw new Error("Unexpected response format");
        }

        if (isActive) {
          setStandings(data);
          setStandingsError(null);
        }
      } catch (error) {
        if (isActive) {
          console.error("Failed to load standings", error);
          setStandings([]);
          setStandingsError("Unable to load standings right now.");
        }
      } finally {
        if (isActive) {
          setStandingsLoading(false);
        }
      }
    }

    loadStandings();

    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    let isActive = true;

    async function loadGames() {
      try {
        setGamesLoading(true);
        const response = await fetch(`${API_BASE_URL}/games?team_id=${FOCUS_TEAM_ID}`);
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }

        const data = (await response.json()) as GameRow[];
        if (!Array.isArray(data)) {
          throw new Error("Unexpected response format");
        }

        if (isActive) {
          setGames(data);
          setGamesError(null);
        }
      } catch (error) {
        if (isActive) {
          console.error("Failed to load games", error);
          setGames([]);
          setGamesError("Unable to load schedule right now.");
        }
      } finally {
        if (isActive) {
          setGamesLoading(false);
        }
      }
    }

    loadGames();

    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    let isActive = true;

    async function loadPlayers() {
      try {
        setPlayersLoading(true);
        const response = await fetch(
          `${API_BASE_URL}/players?team_id=${FOCUS_TEAM_ID}&status=active`
        );
        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`);
        }

        const data = (await response.json()) as PlayerRow[];
        if (!Array.isArray(data)) {
          throw new Error("Unexpected response format");
        }

        if (isActive) {
          setPlayers(data);
          setPlayersError(null);
        }
      } catch (error) {
        if (isActive) {
          console.error("Failed to load roster", error);
          setPlayers([]);
          setPlayersError("Unable to load roster right now.");
        }
      } finally {
        if (isActive) {
          setPlayersLoading(false);
        }
      }
    }

    loadPlayers();

    return () => {
      isActive = false;
    };
  }, []);

  const standingsMap = useMemo(() => {
    const map = new Map<number, StandingRow>();
    standings.forEach((team) => {
      map.set(team.id, team);
    });
    return map;
  }, [standings]);

  const featuredStandings = useMemo(() => {
    if (standings.length) {
      return standings.slice(0, 3).map((team) => ({
        name: team.name,
        record: `${team.wins}-${team.losses}${team.ties ? `-${team.ties}` : ""}`,
        details: `${team.conference} · ${team.division}`,
      }));
    }
    return placeholderStandings.map((team) => ({ ...team, details: "" }));
  }, [standings]);

  const focusTeamRecord = useMemo(() => {
    const team = standingsMap.get(FOCUS_TEAM_ID);
    if (!team) {
      return null;
    }
    const recordParts = [`${team.wins}-${team.losses}`];
    if (team.ties) {
      recordParts.push(`${team.ties}`);
    }
    return recordParts.join("-");
  }, [standingsMap]);

  const upcomingGame = useMemo(() => {
    if (!games.length) {
      return null;
    }
    const sorted = [...games].sort((a, b) => a.week - b.week || a.id - b.id);
    return sorted.find((game) => !game.played_at) ?? sorted[0];
  }, [games]);

  const upcomingOpponent = useMemo(() => {
    if (!upcomingGame) {
      return null;
    }

    const isHome = upcomingGame.home_team_id === FOCUS_TEAM_ID;
    const opponentId = isHome ? upcomingGame.away_team_id : upcomingGame.home_team_id;
    const opponentName = isHome ? upcomingGame.away_team_name : upcomingGame.home_team_name;
    const opponent = standingsMap.get(opponentId);
    const opponentRecordParts = opponent ? [`${opponent.wins}-${opponent.losses}`] : [];
    if (opponent?.ties) {
      opponentRecordParts.push(`${opponent.ties}`);
    }

    return {
      name: opponentName,
      isHome,
      week: upcomingGame.week,
      record: opponentRecordParts.length ? opponentRecordParts.join("-") : null,
    };
  }, [standingsMap, upcomingGame]);

  const depthChartStarters = useMemo(() => {
    if (!players.length) {
      return KEY_DEPTH_CHART_SLOTS.map((slot) => ({
        slot,
        name: "TBD",
        position: slot.replace("1", ""),
        overall: null,
      }));
    }

    return KEY_DEPTH_CHART_SLOTS.map((slot) => {
      const player = players.find((candidate) =>
        candidate.depth_chart_position?.toUpperCase() === slot
      );
      if (player) {
        return {
          slot,
          name: player.name,
          position: player.position,
          overall: player.overall_rating,
        };
      }
      return {
        slot,
        name: "TBD",
        position: slot.replace("1", ""),
        overall: null,
      };
    });
  }, [players]);

  const lastCompletedGame = useMemo(() => {
    const completedGames = games.filter((game) => Boolean(game.played_at));
    if (!completedGames.length) {
      return null;
    }

    return completedGames
      .slice()
      .sort((a, b) => {
        if (a.week !== b.week) {
          return b.week - a.week;
        }

        if (a.played_at && b.played_at && a.played_at !== b.played_at) {
          return new Date(b.played_at).getTime() - new Date(a.played_at).getTime();
        }

        return b.id - a.id;
      })[0];
  }, [games]);

  const lastResult = useMemo(() => {
    if (!lastCompletedGame) {
      return null;
    }

    const isHome = lastCompletedGame.home_team_id === FOCUS_TEAM_ID;
    const opponentName = isHome
      ? lastCompletedGame.away_team_name
      : lastCompletedGame.home_team_name;
    const focusScore = isHome ? lastCompletedGame.home_score : lastCompletedGame.away_score;
    const opponentScore = isHome ? lastCompletedGame.away_score : lastCompletedGame.home_score;

    let outcomeLabel = "Tie";
    if (focusScore > opponentScore) {
      outcomeLabel = "Win";
    } else if (focusScore < opponentScore) {
      outcomeLabel = "Loss";
    }

    return {
      week: lastCompletedGame.week,
      location: isHome ? "Home" : "Away",
      opponentName,
      focusScore,
      opponentScore,
      outcomeLabel,
    };
  }, [lastCompletedGame]);

  const displayedResult = lastResult ?? placeholderLastResult;

  const handleNavigate = (path: string) => {
    window.location.href = path;
  };

  const handleQuickSim = () => {
    setSimModalOpen(false);
    setDetailedSimModalOpen(false);
    setSimulationResult("Quick Sim complete – score 27–20.");
  };

  const handleDetailedSim = () => {
    setSimModalOpen(false);
    setDetailedSimModalOpen(true);
  };

  const handleCloseDetailedSim = () => {
    setDetailedSimModalOpen(false);
    setSimulationResult("Detailed Sim complete – score 31–28.");
  };

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-950 to-slate-900 p-6">
      <header className="mx-auto flex max-w-5xl flex-col gap-4 rounded-2xl bg-primary p-6 text-white shadow-xl sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">NFL GM Simulator</h1>
          <p className="text-sm text-slate-200">
            Season 2024 · {upcomingGame ? `Week ${upcomingGame.week}` : "Loading"}
            {focusTeamRecord ? ` · Record ${focusTeamRecord}` : ""}
          </p>
        </div>
        <div className="rounded-xl bg-white/10 px-6 py-3 text-right">
          <p className="text-sm uppercase tracking-wide text-slate-200">Team Power Index</p>
          <p className="text-4xl font-black">{totalRating}</p>
        </div>
      </header>

      <section className="mx-auto mt-6 flex max-w-5xl flex-wrap gap-3">
        <button
          type="button"
          onClick={() => setSimModalOpen(true)}
          className="flex-1 rounded-xl bg-primary px-4 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-primary/90"
        >
          Simulate Week
        </button>
        <button
          type="button"
          onClick={() => handleNavigate("/free-agency")}
          className="flex-1 rounded-xl bg-slate-800 px-4 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700"
        >
          Sign Free Agents
        </button>
        <button
          type="button"
          onClick={() => handleNavigate("/trade-center")}
          className="flex-1 rounded-xl bg-slate-800 px-4 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700"
        >
          Make a Trade
        </button>
        <button
          type="button"
          onClick={() => setPlayerStatsOpen(true)}
          className="flex-1 rounded-xl bg-slate-800 px-4 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700"
        >
          View Player Stats
        </button>
      </section>

      {simulationResult ? (
        <div className="mx-auto mt-4 max-w-5xl rounded-2xl border border-primary/40 bg-primary/10 p-4 text-sm font-semibold text-primary">
          {simulationResult}
        </div>
      ) : null}

      <section className="mx-auto mt-8 grid max-w-5xl gap-6 lg:grid-cols-[2fr,1fr]">
        <section className="space-y-6">
          <div className="rounded-2xl border border-white/5 bg-slate-950/70 p-6 shadow-lg">
            <h2 className="text-xl font-semibold text-white">Upcoming Matchup</h2>
            <p className="mt-2 text-sm text-slate-300">
              Prepare scouting reports, adjust depth charts, and finalize your game plan before kickoff.
            </p>
            {gamesLoading ? (
              <p className="mt-6 text-sm text-slate-400">Loading matchup…</p>
            ) : upcomingOpponent ? (
              <div className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-lg font-semibold text-white">{upcomingOpponent.name}</p>
                  <p className="text-sm text-slate-400">
                    {upcomingOpponent.record ?? "Record unavailable"}
                  </p>
                </div>
                <span className="rounded-full bg-primary.accent/90 px-4 py-2 text-sm font-medium uppercase text-white">
                  Week {upcomingOpponent.week} · {upcomingOpponent.isHome ? "Home" : "Away"}
                </span>
              </div>
            ) : (
              <p className="mt-6 text-sm text-slate-400">No scheduled games found.</p>
            )}
            {gamesError ? (
              <p className="mt-4 text-xs text-red-300">{gamesError}</p>
            ) : null}
          </div>

          <div className="rounded-2xl border border-white/5 bg-slate-950/70 p-6 shadow-lg">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold text-white">Recent Result</h2>
                <p className="mt-2 text-sm text-slate-300">
                  Review the latest scoreboard to gauge momentum heading into the next matchup.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setBoxScoreOpen(true)}
                className="hidden rounded-lg bg-primary px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-primary/90 sm:block"
              >
                View Box Score
              </button>
            </div>
            {gamesLoading ? (
              <p className="mt-6 text-sm text-slate-400">Checking results…</p>
            ) : (
              <div className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="text-lg font-semibold text-white">vs. {displayedResult.opponentName}</p>
                  <p className="text-sm text-slate-400">
                    Week {displayedResult.week} · {displayedResult.location}
                  </p>
                </div>
                <div className="flex items-center gap-3 text-white">
                  <span className="rounded-full bg-primary/20 px-3 py-1 text-xs font-semibold text-primary">
                    {displayedResult.outcomeLabel}
                  </span>
                  <p className="text-2xl font-bold">
                    {displayedResult.focusScore}-{displayedResult.opponentScore}
                  </p>
                </div>
              </div>
            )}
            <button
              type="button"
              onClick={() => setBoxScoreOpen(true)}
              className="mt-4 w-full rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary/90 sm:hidden"
            >
              View Box Score
            </button>
            {gamesError ? (
              <p className="mt-4 text-xs text-red-300">Showing placeholder score while schedule is unavailable.</p>
            ) : null}
          </div>

          <div className="rounded-2xl border border-white/5 bg-slate-950/70 p-6 shadow-lg">
            <h2 className="text-xl font-semibold text-white">Season Narrative</h2>
            <ul className="mt-4 space-y-3 text-sm text-slate-300">
              <li>· Rookie QB is rising quickly up the weekly power rankings.</li>
              <li>· Defense ranks top 5 in takeaways through two weeks.</li>
              <li>· Contract negotiations pending with star wide receiver.</li>
            </ul>
          </div>
        </section>

        <aside className="space-y-6">
          <div className="rounded-2xl border border-white/5 bg-slate-950/70 p-6 shadow-lg">
            <h2 className="text-xl font-semibold text-white">Team Ratings</h2>
            <div className="mt-4 grid grid-cols-2 gap-4">
              {mockTeamStats.map((stat) => (
                <StatCard key={stat.label} label={stat.label} value={stat.value} />
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-white/5 bg-slate-950/70 p-6 shadow-lg">
            <div className="flex items-center justify-between gap-4">
              <h2 className="text-xl font-semibold text-white">Depth Chart Preview</h2>
              <button
                type="button"
                onClick={() => handleNavigate("/roster-management")}
                className="rounded-lg bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-200 shadow-sm transition hover:bg-slate-700"
              >
                Edit Depth Chart
              </button>
            </div>
            {playersLoading ? (
              <p className="mt-4 text-sm text-slate-400">Loading roster…</p>
            ) : playersError ? (
              <p className="mt-4 text-sm text-red-300">{playersError}</p>
            ) : (
              <ul className="mt-4 space-y-3 text-sm text-slate-300">
                {depthChartStarters.map((player) => (
                  <li key={player.slot} className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-semibold text-white">{player.name}</p>
                      <p className="text-xs uppercase tracking-wide text-slate-400">
                        {player.slot} · {player.position}
                      </p>
                    </div>
                    <span className="rounded-full bg-primary/20 px-3 py-1 text-xs font-semibold text-primary">
                      {player.overall !== null ? `OVR ${player.overall}` : "Awaiting"}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            {playersError ? (
              <p className="mt-4 text-xs text-red-300">Showing placeholder starters.</p>
            ) : null}
          </div>

          <div className="rounded-2xl border border-white/5 bg-slate-950/70 p-6 shadow-lg">
            <h2 className="text-xl font-semibold text-white">Next Actions</h2>
            <ul className="mt-4 space-y-3 text-sm text-slate-300">
              <li>· Review injury report and adjust depth chart.</li>
              <li>· Scout upcoming draft prospects.</li>
              <li>· Evaluate free agent market for linebacker depth.</li>
            </ul>
          </div>

          <div className="rounded-2xl border border-white/5 bg-slate-950/70 p-6 shadow-lg">
            <div className="flex items-center justify-between gap-4">
              <h2 className="text-xl font-semibold text-white">League Standings</h2>
              <button
                type="button"
                onClick={() => handleNavigate("/standings")}
                className="rounded-lg bg-slate-800 px-3 py-1 text-xs font-semibold text-slate-200 shadow-sm transition hover:bg-slate-700"
              >
                View Full Standings
              </button>
            </div>
            {standingsLoading ? (
              <p className="mt-4 text-sm text-slate-400">Loading standings…</p>
            ) : (
              <ul className="mt-4 space-y-3 text-sm text-slate-300">
                {featuredStandings.map((team) => (
                  <li key={team.name} className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-semibold text-white">{team.name}</p>
                      {team.details ? (
                        <p className="text-xs uppercase tracking-wide text-slate-400">{team.details}</p>
                      ) : null}
                    </div>
                    <span className="rounded-full bg-primary/20 px-3 py-1 text-xs font-semibold text-primary">
                      {team.record}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            {standingsError ? (
              <p className="mt-4 text-xs text-red-300">Showing placeholder standings while data loads.</p>
            ) : null}
          </div>
        </aside>
      </section>

      {isSimModalOpen ? (
        <Modal
          title="Simulate Week"
          onClose={() => setSimModalOpen(false)}
          footer={
            <>
              <button
                type="button"
                onClick={handleQuickSim}
                className="flex-1 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary/90"
              >
                Quick Sim
              </button>
              <button
                type="button"
                onClick={handleDetailedSim}
                className="flex-1 rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-slate-200 shadow-sm transition hover:bg-slate-700"
              >
                Detailed Sim
              </button>
            </>
          }
        >
          <p>
            Choose how you want to advance the league. Quick sims jump straight to the final score,
            while detailed sims provide a full play-by-play report.
          </p>
        </Modal>
      ) : null}

      {isDetailedSimModalOpen ? (
        <Modal
          title="Detailed Simulation Log"
          onClose={handleCloseDetailedSim}
          footer={
            <button
              type="button"
              onClick={handleCloseDetailedSim}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary/90"
            >
              Close Log
            </button>
          }
        >
          <ul className="space-y-2 text-left">
            {placeholderGameLog.map((entry, index) => (
              <li key={index} className="rounded-lg bg-slate-900 px-3 py-2 text-slate-200">
                {entry}
              </li>
            ))}
          </ul>
        </Modal>
      ) : null}

      {isBoxScoreOpen ? (
        <Modal
          title="Latest Box Score"
          onClose={() => setBoxScoreOpen(false)}
          footer={
            <button
              type="button"
              onClick={() => setBoxScoreOpen(false)}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary/90"
            >
              Close
            </button>
          }
        >
          <div className="space-y-4">
            <div>
              <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Passing</h4>
              <p className="mt-1 text-white">
                {placeholderBoxScore.quarterback.name} – {placeholderBoxScore.quarterback.yards} YDS · {placeholderBoxScore.quarterback.touchdowns} TD · {placeholderBoxScore.quarterback.interceptions} INT
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Rushing</h4>
              <p className="mt-1 text-white">
                {placeholderBoxScore.runningBack.name} – {placeholderBoxScore.runningBack.yards} YDS · {placeholderBoxScore.runningBack.touchdowns} TD
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Receiving</h4>
              <p className="mt-1 text-white">
                {placeholderBoxScore.receiver.name} – {placeholderBoxScore.receiver.yards} YDS · {placeholderBoxScore.receiver.touchdowns} TD
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Defense</h4>
              <p className="mt-1 text-white">
                {placeholderBoxScore.defender.name} – {placeholderBoxScore.defender.sacks} SACK · {placeholderBoxScore.defender.interceptions} INT
              </p>
            </div>
            <div>
              <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Team Totals</h4>
              <p className="mt-1 text-white">
                {placeholderBoxScore.teamTotals.yards} Total Yards · {placeholderBoxScore.teamTotals.turnovers} Turnovers
              </p>
            </div>
          </div>
        </Modal>
      ) : null}

      {isPlayerStatsOpen ? (
        <Modal
          title="Player Spotlight"
          onClose={() => setPlayerStatsOpen(false)}
          footer={
            <button
              type="button"
              onClick={() => setPlayerStatsOpen(false)}
              className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary/90"
            >
              Close
            </button>
          }
        >
          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Offense</h4>
            <ul className="mt-2 space-y-2">
              {placeholderPlayerStats.offense.map((player) => (
                <li key={player.name} className="rounded-lg bg-slate-900 px-3 py-2 text-white">
                  <p className="text-sm font-semibold">{player.name}</p>
                  <p className="text-xs text-slate-300">{player.statLine}</p>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold uppercase tracking-wide text-slate-400">Defense</h4>
            <ul className="mt-2 space-y-2">
              {placeholderPlayerStats.defense.map((player) => (
                <li key={player.name} className="rounded-lg bg-slate-900 px-3 py-2 text-white">
                  <p className="text-sm font-semibold">{player.name}</p>
                  <p className="text-xs text-slate-300">{player.statLine}</p>
                </li>
              ))}
            </ul>
          </div>
        </Modal>
      ) : null}
    </main>
  );
}

export default Dashboard;
