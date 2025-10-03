import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { leagueApi } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import { Card } from "../../components/ui/Card";
import { Standing } from "../../types/league";

type DivisionGroup = {
  id: string;
  title: string;
  teams: Standing[];
};

export function StandingsPage() {
  const standingsQuery = useQuery({ queryKey: queryKeys.standings, queryFn: () => leagueApi.fetchStandings() });
  const standings = standingsQuery.data ?? [];

  const grouped = useMemo<DivisionGroup[]>(() => {
    const map = new Map<string, DivisionGroup>();
    standings.forEach((team) => {
      const key = `${team.conference}-${team.division}`;
      if (!map.has(key)) {
        map.set(key, {
          id: key,
          title: `${team.conference} · ${team.division}`,
          teams: [],
        });
      }
      const winPct = typeof team.winPct === "number" ? team.winPct : 0;
      map.get(key)!.teams.push({ ...team, winPct });
    });
    return Array.from(map.values()).map((group) => ({
      ...group,
      teams: group.teams.sort((a, b) => {
        if (b.winPct !== a.winPct) {
          return b.winPct - a.winPct;
        }
        return b.wins - a.wins || a.losses - b.losses || a.teamId - b.teamId;
      }),
    }));
  }, [standings]);

  return (
    <div className="space-y-6">
      <Card>
        <h2 className="text-2xl font-semibold text-white">Division standings</h2>
        <p className="mt-2 text-sm text-slate-300">
          Each table highlights the current division leader based on backend win percentage data.
        </p>
      </Card>

      {standingsQuery.isLoading ? (
        <Card>
          <p className="text-sm text-slate-400">Loading standings…</p>
        </Card>
      ) : !grouped.length ? (
        <Card>
          <p className="text-sm text-slate-400">Standings will appear once games have been completed.</p>
        </Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-2">
          {grouped.map((division) => (
            <Card key={division.id}>
              <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">{division.title}</h3>
              <div className="mt-3 overflow-hidden rounded-xl border border-white/5">
                <table className="min-w-full text-left text-sm">
                  <thead className="bg-slate-900/60 text-xs uppercase tracking-wide text-slate-400">
                    <tr>
                      <th className="px-4 py-3 font-medium">Team</th>
                      <th className="px-4 py-3 font-medium text-center">W</th>
                      <th className="px-4 py-3 font-medium text-center">L</th>
                      <th className="px-4 py-3 font-medium text-center">T</th>
                      <th className="px-4 py-3 font-medium text-right">Win %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {division.teams.map((team, index) => (
                      <tr
                        key={team.teamId}
                        className={
                          index === 0
                            ? "bg-primary.accent/10 text-white"
                            : "border-t border-white/5 text-slate-200"
                        }
                      >
                        <td className="px-4 py-3 font-semibold">
                          {team.name}
                          <span className="ml-2 text-xs font-normal uppercase tracking-wide text-slate-400">
                            {team.abbreviation}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-center">{team.wins}</td>
                        <td className="px-4 py-3 text-center">{team.losses}</td>
                        <td className="px-4 py-3 text-center">{team.ties}</td>
                        <td className="px-4 py-3 text-right">{team.winPct.toFixed(3)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
