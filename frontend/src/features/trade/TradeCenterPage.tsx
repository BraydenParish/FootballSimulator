import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { leagueApi } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import { Card } from "../../components/ui/Card";
import { Player, TradeProposal } from "../../types/league";

const DEFAULT_TEAM_A = 1;
const DEFAULT_TEAM_B = 2;

/**
 * TradeCenterPage renders the interactive trade workflow where users can build,
 * validate, and execute offers between two teams using mock trade rules.
 */
export function TradeCenterPage() {
  const queryClient = useQueryClient();
  const teamsQuery = useQuery({ queryKey: queryKeys.teams, queryFn: () => leagueApi.fetchTeams() });
  const [teamA, setTeamA] = useState<number>(DEFAULT_TEAM_A);
  const [teamB, setTeamB] = useState<number>(DEFAULT_TEAM_B);
  const [offer, setOffer] = useState<number[]>([]);
  const [request, setRequest] = useState<number[]>([]);
  const [feedback, setFeedback] = useState<string | null>(null);

  const rosterQueryA = useQuery({
    queryKey: queryKeys.roster(teamA),
    queryFn: () => leagueApi.fetchTeamRoster(teamA),
  });
  const rosterQueryB = useQuery({
    queryKey: queryKeys.roster(teamB),
    queryFn: () => leagueApi.fetchTeamRoster(teamB),
  });

  const evaluateMutation = useMutation({
    mutationFn: (proposal: TradeProposal) => leagueApi.evaluateTrade(proposal),
    onSuccess: (result) => {
      setFeedback(result.success ? "Trade Accepted" : result.message);
    },
    onError: (error: unknown) => {
      setFeedback(error instanceof Error ? error.message : "Trade evaluation failed.");
    },
  });

  const executeMutation = useMutation({
    mutationFn: (proposal: TradeProposal) => leagueApi.executeTrade(proposal),
    onSuccess: (result) => {
      setFeedback(result.message);
      queryClient.invalidateQueries({ queryKey: queryKeys.roster(teamA) });
      queryClient.invalidateQueries({ queryKey: queryKeys.roster(teamB) });
      setOffer([]);
      setRequest([]);
    },
  });

  const handleToggle = (playerId: number, list: number[], setList: (ids: number[]) => void) => {
    if (list.includes(playerId)) {
      setList(list.filter((id) => id !== playerId));
    } else {
      setList([...list, playerId]);
    }
  };

  const teams = teamsQuery.data ?? [];
  const rosterA = rosterQueryA.data ?? [];
  const rosterB = rosterQueryB.data ?? [];

  const handleEvaluate = () => {
    const proposal: TradeProposal = { teamA, teamB, offer, request };
    setFeedback(null);
    evaluateMutation.mutate(proposal);
  };

  const handleExecute = () => {
    const proposal: TradeProposal = { teamA, teamB, offer, request };
    setFeedback(null);
    executeMutation.mutate(proposal);
  };

  const teamName = (teamId: number) => teams.find((team) => team.id === teamId)?.name ?? "Team";

  const renderRosterList = (players: Player[], selected: number[], onToggle: (id: number) => void) => (
    <ul className="max-h-64 space-y-2 overflow-y-auto rounded-xl border border-white/10 bg-slate-950/60 p-4 text-sm text-slate-200">
      {players.map((player) => (
        <li key={player.id} className="flex items-center justify-between gap-2">
          <label className="flex items-center gap-3">
            <input
              type="checkbox"
              checked={selected.includes(player.id)}
              onChange={() => onToggle(player.id)}
              className="h-4 w-4 rounded border-white/30 bg-slate-900 text-primary.accent focus:ring-primary.accent"
            />
            <span className="font-semibold text-white">{player.name}</span>
          </label>
          <span className="text-xs text-slate-400">{player.position} · OVR {player.overall}</span>
        </li>
      ))}
    </ul>
  );

  const tradeSummary = useMemo(
    () =>
      offer.length || request.length
        ? `Offer ${offer.length} asset(s) for ${request.length} asset(s).`
        : "Select assets from each roster to build a proposal.",
    [offer, request]
  );

  return (
    <div className="space-y-6">
      <Card>
        <h2 className="text-2xl font-semibold text-white">Trade center</h2>
        <p className="mt-2 text-sm text-slate-300">
          Build trade offers between two teams. All evaluations leverage the shared backend trade
          engine, ensuring roster and salary validation before execution.
        </p>
        {feedback ? (
          <div
            className="mt-3 rounded-lg bg-primary.accent/10 px-4 py-2 text-xs font-semibold text-primary.accent"
            data-test="trade-result"
          >
            {feedback}
          </div>
        ) : null}
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <div className="space-y-3">
            <label className="flex flex-col text-sm text-slate-200">
              Offering team
              <select
                value={teamA}
                onChange={(event) => setTeamA(Number.parseInt(event.target.value, 10))}
                className="mt-1 rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
              >
                {teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name}
                  </option>
                ))}
              </select>
            </label>
            {renderRosterList(rosterA, offer, (id) => handleToggle(id, offer, setOffer))}
          </div>
          <div className="space-y-3">
            <label className="flex flex-col text-sm text-slate-200">
              Receiving team
              <select
                value={teamB}
                onChange={(event) => setTeamB(Number.parseInt(event.target.value, 10))}
                className="mt-1 rounded-lg border border-white/10 bg-slate-900 px-3 py-2 text-sm text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
              >
                {teams.map((team) => (
                  <option key={team.id} value={team.id}>
                    {team.name}
                  </option>
                ))}
              </select>
            </label>
            {renderRosterList(rosterB, request, (id) => handleToggle(id, request, setRequest))}
          </div>
        </div>
      </Card>

      <Card>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h3 className="text-lg font-semibold text-white">Proposal summary</h3>
            <p className="text-sm text-slate-300">{tradeSummary}</p>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row">
            <button
              type="button"
              onClick={handleEvaluate}
              disabled={evaluateMutation.isPending}
              className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent disabled:cursor-not-allowed disabled:bg-slate-700/60"
            >
              Propose Trade
            </button>
            <button
              type="button"
              onClick={handleExecute}
              className="rounded-lg bg-primary.accent px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary.accent/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
            >
              Execute Trade
            </button>
          </div>
        </div>
        <p className="mt-4 text-xs text-slate-400">
          Offering: {teamName(teamA)} ({offer.length}) · Requesting: {teamName(teamB)} ({request.length})
        </p>
      </Card>
    </div>
  );
}
