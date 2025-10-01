import { useMemo } from "react";

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
        </aside>
      </section>
    </main>
  );
}

export default App;
