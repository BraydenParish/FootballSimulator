import { NavLink, Outlet } from "react-router-dom";

const navigation = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/results", label: "Results" },
  { to: "/depth-chart", label: "Depth Chart" },
  { to: "/free-agency", label: "Free Agency" },
  { to: "/trade-center", label: "Trade Center" },
  { to: "/standings", label: "Standings" },
];

export function AppLayout() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 to-slate-900 text-slate-100">
      <header className="border-b border-white/10 bg-slate-950/60 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.3rem] text-primary.accent">Gridiron GM</p>
            <h1 className="text-2xl font-bold text-white">League Operations Console</h1>
            <p className="text-sm text-slate-400">
              Manage simulations, rosters, and market moves from one unified dashboard.
            </p>
          </div>
          <nav aria-label="Primary" className="flex flex-wrap gap-2">
            {navigation.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  `rounded-full px-4 py-2 text-sm font-semibold transition focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent ${
                    isActive
                      ? "bg-primary.accent text-white shadow-lg"
                      : "bg-slate-800/80 text-slate-200 hover:bg-slate-700"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>
      <main className="px-6 py-10">
        <div className="mx-auto max-w-6xl">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
