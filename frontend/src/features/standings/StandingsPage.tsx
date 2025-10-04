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
    <Card>
      <h2 className="text-2xl font-semibold text-white">League standings</h2>
      <p className="mt-2 text-sm text-slate-300">
        Full conference and division ordering calculated from completed simulations.
      </p>
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full divide-y divide-white/10 text-left">
          <thead className="text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-4 py-3 font-medium">Team</th>
              <th className="px-4 py-3 font-medium">Conference</th>
              <th className="px-4 py-3 font-medium">Division</th>
              <th className="px-4 py-3 font-medium">Wins</th>
              <th className="px-4 py-3 font-medium">Losses</th>
              <th className="px-4 py-3 font-medium">Ties</th>
            </tr>
          </thead>
          <tbody>
            {standingsQuery.isLoading ? (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-sm text-slate-400">
                  Loading standings…
                </td>
              </tr>
            ) : standings.length ? (
              standings.map((team) => (
                <tr key={team.teamId} className="border-b border-white/5" data-test="standings-row">
                  <td className="px-4 py-3 text-sm text-white">{team.name}</td>
                  <td className="px-4 py-3 text-sm text-slate-300">{team.conference}</td>
                  <td className="px-4 py-3 text-sm text-slate-300">{team.division}</td>
                  <td className="px-4 py-3 text-sm text-slate-300">{team.wins}</td>
                  <td className="px-4 py-3 text-sm text-slate-300">{team.losses}</td>
                  <td className="px-4 py-3 text-sm text-slate-300">{team.ties}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="px-4 py-6 text-center text-sm text-slate-400">
                  Standings will appear after the first simulation.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
