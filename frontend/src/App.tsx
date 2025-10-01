import { useEffect, useMemo, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

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

const mockUpcomingOpponent = {
  name: "Baltimore Ravens",
  record: "2-0",
  kickoff: "Sunday 1:00 PM ET"
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

  const featuredStandings = useMemo(() => standings.slice(0, 6), [standings]);

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-950 to-slate-900 p-6">
      <header className="mx-auto flex max-w-5xl flex-col gap-4 rounded-2xl bg-primary p-6 text-white shadow-xl sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">NFL GM Simulator</h1>
          <p className="text-sm text-slate-200">Season 2024 · Week 3</p>
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
            <div className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-lg font-semibold text-white">{mockUpcomingOpponent.name}</p>
                <p className="text-sm text-slate-400">{mockUpcomingOpponent.record}</p>
              </div>
              <span className="rounded-full bg-primary.accent/90 px-4 py-2 text-sm font-medium uppercase text-white">
                {mockUpcomingOpponent.kickoff}
              </span>
            </div>
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
