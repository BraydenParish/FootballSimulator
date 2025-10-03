import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { leagueApi } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import { Card } from "../../components/ui/Card";
import { Player, Team } from "../../types/league";

const DEFAULT_TEAM_ID = 1;

export function FreeAgencyPage() {
  const queryClient = useQueryClient();
  const [positionFilter, setPositionFilter] = useState<string>("All");
  const [selectedTeam, setSelectedTeam] = useState<number>(DEFAULT_TEAM_ID);
  const [feedback, setFeedback] = useState<string | null>(null);

  const teamsQuery = useQuery({ queryKey: queryKeys.teams, queryFn: () => leagueApi.fetchTeams() });
  const freeAgentsQuery = useQuery({
    queryKey: queryKeys.freeAgents,
    queryFn: () => leagueApi.fetchFreeAgents(),
  });

  const signMutation = useMutation({
    mutationFn: ({ playerId, teamId }: { playerId: number; teamId: number }) =>
      leagueApi.signFreeAgent(teamId, playerId),
    onSuccess: (result) => {
      setFeedback(result.message);
      if (result.status === "signed") {
        queryClient.invalidateQueries({ queryKey: queryKeys.freeAgents });
        queryClient.invalidateQueries({ queryKey: queryKeys.roster(selectedTeam) });
      }
    },
    onError: () => {
      setFeedback("Signing failed. Please try again.");
    },
  });

  const teams = teamsQuery.data ?? [];
  const freeAgents = freeAgentsQuery.data ?? [];

  const filteredFreeAgents = freeAgents.filter((player) =>
    positionFilter === "All" ? true : player.position === positionFilter
  );

  const uniquePositions = Array.from(new Set(freeAgents.map((player) => player.position))).sort();

  const handleSign = (playerId: number) => {
    signMutation.mutate({ playerId, teamId: selectedTeam });
  };

  const renderRow = (player: Player) => (
    <tr key={player.id} className="border-b border-white/5">
      <td className="px-4 py-3 text-sm text-white">{player.name}</td>
      <td className="px-4 py-3 text-sm text-slate-300">{player.position}</td>
      <td className="px-4 py-3 text-sm text-slate-300">{player.overall}</td>
      <td className="px-4 py-3 text-sm text-slate-300">{player.age}</td>
      <td className="px-4 py-3 text-sm text-slate-300">{player.contractValue}M</td>
      <td className="px-4 py-3 text-right text-sm">
        <button
          type="button"
          onClick={() => handleSign(player.id)}
          className="rounded-lg bg-primary.accent px-3 py-1 text-xs font-semibold uppercase tracking-wide text-white transition hover:bg-primary.accent/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
        >
          Sign
        </button>
      </td>
    </tr>
  );

  return (
    <div className="space-y-6">
      <Card>
        <h2 className="text-2xl font-semibold text-white">Free agency center</h2>
        <p className="mt-2 text-sm text-slate-300">
          Filter the available pool and sign players directly to the selected team. All moves are
          validated locally until the backend services are integrated.
        </p>
        <div className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-end">
          <label className="flex flex-col text-sm text-slate-200">
            Team
            <select
              value={selectedTeam}
              onChange={(event) => setSelectedTeam(Number.parseInt(event.target.value, 10))}
              className="mt-1 rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
            >
              {teams.map((team: Team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col text-sm text-slate-200">
            Position
            <select
              value={positionFilter}
              onChange={(event) => setPositionFilter(event.target.value)}
              className="mt-1 rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
            >
              <option value="All">All</option>
              {uniquePositions.map((position) => (
                <option key={position} value={position}>
                  {position}
                </option>
              ))}
            </select>
          </label>
          {feedback ? (
            <div className="rounded-lg bg-primary.accent/10 px-4 py-2 text-xs font-semibold text-primary.accent">
              {feedback}
            </div>
          ) : null}
        </div>
      </Card>

      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-white/10 text-left">
            <thead className="text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Player</th>
                <th className="px-4 py-3 font-medium">Pos</th>
                <th className="px-4 py-3 font-medium">OVR</th>
                <th className="px-4 py-3 font-medium">Age</th>
                <th className="px-4 py-3 font-medium">Salary</th>
                <th className="px-4 py-3 font-medium" aria-label="Actions"></th>
              </tr>
            </thead>
            <tbody>
              {freeAgentsQuery.isLoading ? (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-sm text-slate-400">
                    Loading free agents…
                  </td>
                </tr>
              ) : filteredFreeAgents.length ? (
                filteredFreeAgents.map(renderRow)
              ) : (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-sm text-slate-400">
                    No free agents match the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
