import { useQuery } from "@tanstack/react-query";
import { leagueApi } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import { Card } from "../../components/ui/Card";

export function StandingsPage() {
  const standingsQuery = useQuery({ queryKey: queryKeys.standings, queryFn: () => leagueApi.fetchStandings() });
  const standings = standingsQuery.data ?? [];

  return (
    <Card>
      <h2 className="text-2xl font-semibold text-white">League standings</h2>
      <p className="mt-2 text-sm text-slate-300">
        Full conference and division ordering sourced from the mock data store.
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
                <tr key={team.teamId} className="border-b border-white/5">
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
