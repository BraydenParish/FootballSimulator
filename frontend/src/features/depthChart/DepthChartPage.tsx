import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { leagueApi } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import { Card } from "../../components/ui/Card";
import { DepthChartEntry, Player, Team } from "../../types/league";

const DEFAULT_TEAM_ID = 1;

const slots = ["QB1", "QB2", "RB1", "RB2", "WR1", "WR2", "TE1", "TE2", "LB1", "LB2", "CB1", "CB2"];

export function DepthChartPage() {
  const queryClient = useQueryClient();
  const teamsQuery = useQuery({ queryKey: queryKeys.teams, queryFn: () => leagueApi.fetchTeams() });
  const [teamId, setTeamId] = useState(DEFAULT_TEAM_ID);
  const rosterQuery = useQuery({
    queryKey: queryKeys.roster(teamId),
    queryFn: () => leagueApi.fetchTeamRoster(teamId),
  });
  const [entries, setEntries] = useState<Record<number, string>>({});
  const [feedback, setFeedback] = useState<string | null>(null);

  useEffect(() => {
    const players = rosterQuery.data ?? [];
    const mapping: Record<number, string> = {};
    players.forEach((player) => {
      if (player.depthChartSlot) {
        mapping[player.id] = player.depthChartSlot;
      }
    });
    setEntries(mapping);
  }, [rosterQuery.data]);

  const updateMutation = useMutation({
    mutationFn: (payload: { teamId: number; entries: DepthChartEntry[] }) =>
      leagueApi.updateDepthChart(payload.teamId, payload.entries),
    onSuccess: () => {
      setFeedback("Depth chart saved.");
      queryClient.invalidateQueries({ queryKey: queryKeys.roster(teamId) });
    },
    onError: () => {
      setFeedback("Unable to save depth chart. Please retry.");
    },
  });

  const teams = teamsQuery.data ?? [];
  const roster = rosterQuery.data ?? [];

  const slotOptions = useMemo(() => slots, []);

  const handleEntryChange = (player: Player, slotValue: string) => {
    setEntries((prev) => {
      const next = { ...prev };
      const previousSlot = prev[player.id] ?? "";

      if (previousSlot === slotValue) {
        return next;
      }

      if (!slotValue) {
        delete next[player.id];
        return next;
      }

      const conflict = Object.entries(prev).find(([otherId, slot]) => Number(otherId) !== player.id && slot === slotValue);
      if (conflict) {
        const [conflictId] = conflict;
        if (previousSlot) {
          next[Number(conflictId)] = previousSlot;
        } else {
          delete next[Number(conflictId)];
        }
      }

      next[player.id] = slotValue;
      return next;
    });
  };

  const handleSave = () => {
    const payload: DepthChartEntry[] = Object.entries(entries).map(([playerId, slot]) => ({
      playerId: Number.parseInt(playerId, 10),
      slot,
    }));
    updateMutation.mutate({ teamId, entries: payload });
  };

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-white">Depth chart management</h2>
            <p className="mt-2 text-sm text-slate-300">
              Assign starters and backups for key positions. Updates persist to the shared backend roster so
              simulations and trades immediately respect the adjustments.
            </p>
          </div>
          <label className="flex flex-col text-sm text-slate-200">
            Team
            <select
              value={teamId}
              onChange={(event) => setTeamId(Number.parseInt(event.target.value, 10))}
              className="mt-1 rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
            >
              {teams.map((team: Team) => (
                <option key={team.id} value={team.id}>
                  {team.name}
                </option>
              ))}
            </select>
          </label>
        </div>
        {feedback ? (
          <div className="mt-3 rounded-lg bg-primary.accent/10 px-4 py-2 text-xs font-semibold text-primary.accent">
            {feedback}
          </div>
        ) : null}
      </Card>

      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-white/10 text-left">
            <thead className="text-xs uppercase tracking-wide text-slate-400">
              <tr>
                <th className="px-4 py-3 font-medium">Player</th>
                <th className="px-4 py-3 font-medium">Pos</th>
                <th className="px-4 py-3 font-medium">OVR</th>
                <th className="px-4 py-3 font-medium">Slot</th>
              </tr>
            </thead>
            <tbody>
              {rosterQuery.isLoading ? (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-sm text-slate-400">
                    Loading roster…
                  </td>
                </tr>
              ) : roster.length ? (
                roster.map((player) => (
                  <tr key={player.id} className="border-b border-white/5">
                    <td className="px-4 py-3 text-sm text-white">{player.name}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">{player.position}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">{player.overall}</td>
                    <td className="px-4 py-3 text-sm text-slate-200">
                      <select
                        value={entries[player.id] ?? ""}
                        onChange={(event) => handleEntryChange(player, event.target.value)}
                        className="w-full rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
                      >
                        <option value="">Unassigned</option>
                        {slotOptions.map((slot) => (
                          <option key={slot} value={slot}>
                            {slot}
                          </option>
                        ))}
                      </select>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-sm text-slate-400">
                    No players found for this team.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
        <div className="mt-4 flex flex-col gap-2 sm:flex-row sm:justify-end">
          <button
            type="button"
            onClick={handleSave}
            className="rounded-lg bg-primary.accent px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary.accent/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
          >
            Save Depth Chart
          </button>
        </div>
      </Card>
    </div>
  );
}
