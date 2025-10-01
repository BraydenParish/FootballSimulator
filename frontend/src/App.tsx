import { useEffect, useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const FOCUS_TEAM_ID = 1;

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

const mockTeamStats = [
  { label: "Overall", value: 86 },
  { label: "Offense", value: 89 },
  { label: "Defense", value: 84 },
  { label: "Special Teams", value: 81 }
];

function StatCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-xl bg-slate-900 p-4 shadow-lg">
      <p className="text-sm font-medium text-slate-400">{label}</p>
      <p className="mt-2 text-3xl font-semibold text-white">{value}</p>
    </div>
  );
}

function App() {
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

  const featuredStandings = useMemo(() => standings.slice(0, 6), [standings]);

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

  const depthChartPreview = useMemo(() => {
    if (!players.length) {
      return [];
    }

    const sorted = [...players].sort((a, b) => {
      if (a.depth_chart_position && b.depth_chart_position) {
        return a.depth_chart_position.localeCompare(b.depth_chart_position);
      }
      if (a.depth_chart_position) {
        return -1;
      }
      if (b.depth_chart_position) {
        return 1;
      }
      return b.overall_rating - a.overall_rating || a.name.localeCompare(b.name);
    });

    return sorted.slice(0, 6);
  }, [players]);

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

      <section className="mx-auto mt-8 grid max-w-5xl gap-6 lg:grid-cols-[2fr,1fr]">
        <section className="space-y-6">
          <div className="rounded-2xl border border-white/5 bg-slate-950/70 p-6 shadow-lg">
            <h2 className="text-xl font-semibold text-white">Upcoming Matchup</h2>
            <p className="mt-2 text-sm text-slate-300">
              Prepare scouting reports, adjust depth charts, and finalize your game plan before kickoff.
            </p>
            {gamesLoading ? (
              <p className="mt-6 text-sm text-slate-400">Loading matchup…</p>
            ) : gamesError ? (
              <p className="mt-6 text-sm text-red-300">{gamesError}</p>
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
            <h2 className="text-xl font-semibold text-white">Depth Chart Preview</h2>
            {playersLoading ? (
              <p className="mt-4 text-sm text-slate-400">Loading roster…</p>
            ) : playersError ? (
              <p className="mt-4 text-sm text-red-300">{playersError}</p>
            ) : depthChartPreview.length ? (
              <ul className="mt-4 space-y-3 text-sm text-slate-300">
                {depthChartPreview.map((player) => (
                  <li key={player.id} className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-semibold text-white">
                        {player.name}
                      </p>
                      <p className="text-xs uppercase tracking-wide text-slate-400">
                        {player.position}
                        {player.depth_chart_position ? ` · ${player.depth_chart_position}` : ""}
                      </p>
                    </div>
                    <span className="rounded-full bg-primary/20 px-3 py-1 text-xs font-semibold text-primary">
                      OVR {player.overall_rating}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-4 text-sm text-slate-400">No roster data available.</p>
            )}
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
            <h2 className="text-xl font-semibold text-white">League Standings</h2>
            {standingsLoading ? (
              <p className="mt-4 text-sm text-slate-400">Loading standings…</p>
            ) : standingsError ? (
              <p className="mt-4 text-sm text-red-300">{standingsError}</p>
            ) : (
              <ul className="mt-4 space-y-3 text-sm text-slate-300">
                {featuredStandings.map((team) => (
                  <li key={team.id} className="flex items-center justify-between gap-4">
                    <div>
                      <p className="font-semibold text-white">{team.name}</p>
                      <p className="text-xs uppercase tracking-wide text-slate-400">
                        {team.conference} · {team.division}
                      </p>
                    </div>
                    <span className="rounded-full bg-primary/20 px-3 py-1 text-xs font-semibold text-primary">
                      {team.wins}-{team.losses}
                      {team.ties ? `-${team.ties}` : ""}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </aside>
      </section>
    </main>
  );
}

export default App;
