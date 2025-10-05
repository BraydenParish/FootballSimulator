import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { leagueApi } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import { BoxScore, GameSummary, Player, TeamStats } from "../../types/league";
import { Card } from "../../components/ui/Card";
import { Modal } from "../../components/ui/Modal";
import { SimulationControls } from "./components/SimulationControls";
import { StandingsPreview } from "./components/StandingsPreview";
import { RecentResultsCard } from "./components/RecentResultsCard";
import { DepthChartPreview } from "./components/DepthChartPreview";

const FOCUS_TEAM_ID = 1;

function useFocusTeamData() {
  const standingsQuery = useQuery({
    queryKey: queryKeys.standings,
    queryFn: () => leagueApi.fetchStandings(),
  });

  const scheduleQuery = useQuery({
    queryKey: queryKeys.schedule(FOCUS_TEAM_ID),
    queryFn: () => leagueApi.fetchSchedule(FOCUS_TEAM_ID),
  });

  const boxScoresQuery = useQuery({
    queryKey: queryKeys.boxScores(FOCUS_TEAM_ID),
    queryFn: () => leagueApi.fetchBoxScores(FOCUS_TEAM_ID),
  });

  const rosterQuery = useQuery({
    queryKey: queryKeys.roster(FOCUS_TEAM_ID),
    queryFn: () => leagueApi.fetchTeamRoster(FOCUS_TEAM_ID),
  });

  const statsQuery = useQuery({
    queryKey: queryKeys.teamStats(FOCUS_TEAM_ID),
    queryFn: () => leagueApi.fetchTeamStats(FOCUS_TEAM_ID),
  });

  return { standingsQuery, scheduleQuery, boxScoresQuery, rosterQuery, statsQuery };
}

function determineUpcomingGame(schedule: GameSummary[]): GameSummary | null {
  if (!schedule.length) {
    return null;
  }
  const sorted = [...schedule].sort((a, b) => a.week - b.week || a.id - b.id);
  const unplayed = sorted.find((game) => !game.playedAt);
  return unplayed ?? sorted[sorted.length - 1];
}

function determineLastResult(schedule: GameSummary[]): GameSummary | null {
  const completed = schedule.filter((game) => Boolean(game.playedAt));
  if (!completed.length) {
    return null;
  }
  return completed.sort((a, b) => {
    if (a.week !== b.week) {
      return b.week - a.week;
    }
    return (b.playedAt ?? "").localeCompare(a.playedAt ?? "");
  })[0];
}

function extractStarters(players: Player[]): Array<{ slot: string; player: Player | undefined }> {
  const slots = ["QB1", "RB1", "WR1", "TE1", "LB1", "CB1"] as const;
  return slots.map((slot) => ({ slot, player: players.find((candidate) => candidate.depthChartSlot === slot) }));
}

export function DashboardPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { standingsQuery, scheduleQuery, boxScoresQuery, rosterQuery, statsQuery } =
    useFocusTeamData();

  const standings = useMemo(() => standingsQuery.data ?? [], [standingsQuery.data]);
  const schedule = useMemo(() => scheduleQuery.data ?? [], [scheduleQuery.data]);
  const boxScores = useMemo(() => boxScoresQuery.data ?? [], [boxScoresQuery.data]);
  const roster = useMemo(() => rosterQuery.data ?? [], [rosterQuery.data]);
  const starters = useMemo(() => extractStarters(roster), [roster]);

  const upcomingGame = useMemo(() => determineUpcomingGame(schedule), [schedule]);
  const nextWeek = upcomingGame?.week ?? 1;

  const lastResultGame = useMemo(() => determineLastResult(schedule), [schedule]);
  const lastBoxScore = useMemo(
    () => boxScores.find((box) => box.gameId === lastResultGame?.id),
    [boxScores, lastResultGame]
  );

  const [boxScoreOpen, setBoxScoreOpen] = useState(false);
  const [playerStatsOpen, setPlayerStatsOpen] = useState(false);
  const [simulationMessage, setSimulationMessage] = useState<string | null>(null);
  const [detailedLog, setDetailedLog] = useState<string[]>([]);
  const [latestWeek, setLatestWeek] = useState<number | null>(null);
  const [latestSummaries, setLatestSummaries] = useState<BoxScore[]>([]);

  const simulationMutation = useMutation({
    mutationFn: leagueApi.simulateWeek,
    onSuccess: (_result, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.schedule(FOCUS_TEAM_ID) });
      queryClient.invalidateQueries({ queryKey: queryKeys.standings });
      queryClient.invalidateQueries({ queryKey: queryKeys.boxScores(FOCUS_TEAM_ID) });
      queryClient.invalidateQueries({ queryKey: queryKeys.teamStats(FOCUS_TEAM_ID) });
      setDetailedLog(_result.playByPlay);
      setLatestWeek(_result.week);
      setLatestSummaries(_result.summaries);
    },
  });

  const handleSimulateWeek = async () => {
    const result = await simulationMutation.mutateAsync({ week: nextWeek, mode: "quick" });
    const targetWeek = result.week ?? nextWeek;
    const highlight = result.summaries[0]?.gameId ?? null;
    navigate(`/results/${targetWeek}`, { state: highlight ? { highlight } : undefined });
  };

  const standingsTop = useMemo(() => standings.slice(0, 3), [standings]);

  const playerStats: TeamStats | undefined = statsQuery.data;

  return (
    <div className="space-y-6">
      <SimulationControls
        isLoading={simulationMutation.isPending}
        nextWeek={nextWeek}
        standings={standings}
        upcomingGame={upcomingGame ?? null}
        focusTeamId={FOCUS_TEAM_ID}
        onSimulateWeek={handleSimulateWeek}
        onOpenPlayerStats={() => setPlayerStatsOpen(true)}
      />

      <div className="grid gap-6 lg:grid-cols-[2fr,1fr]">
        <div className="space-y-6">
          <RecentResultsCard
            isLoading={scheduleQuery.isLoading}
            error={scheduleQuery.error instanceof Error ? scheduleQuery.error.message : null}
            lastResult={lastResultGame}
            standings={standings}
            focusTeamId={FOCUS_TEAM_ID}
            onViewBoxScore={() => setBoxScoreOpen(true)}
          />
          {latestWeek ? (
            <Card data-test="simulation-results">
              <h2 className="text-lg font-semibold text-white">Week {latestWeek} Results</h2>
              <ul className="mt-3 space-y-2">
                {latestSummaries.map((summary) => (
                  <li
                    key={summary.gameId}
                    className="rounded-lg border border-white/10 bg-slate-900/60 px-4 py-3 text-sm text-slate-200"
                    data-test="game-result"
                  >
                    {summary.homeTeam.name} {summary.homeTeam.points} – {summary.awayTeam.points} {" "}
                    {summary.awayTeam.name}
                  </li>
                ))}
              </ul>
            </Card>
          ) : null}
          <Card>
            <h2 className="text-lg font-semibold text-white">League Narrative</h2>
            <p className="mt-2 text-sm text-slate-300">
              The league office reports balanced competition this season. Use the detailed simulator to
              craft your own storylines while live results synchronize across trades and roster moves.
            </p>
          </Card>
        </div>
        <div className="space-y-6">
          <DepthChartPreview starters={starters} onManageRoster={() => setPlayerStatsOpen(true)} />
          <StandingsPreview standings={standingsTop} />
          <Card>
            <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">
              Ratings Snapshot
            </h3>
            <ul className="mt-3 space-y-2 text-sm text-slate-200">
              <li className="flex items-center justify-between"><span>Overall Index</span><span>86</span></li>
              <li className="flex items-center justify-between"><span>Offense</span><span>88</span></li>
              <li className="flex items-center justify-between"><span>Defense</span><span>84</span></li>
              <li className="flex items-center justify-between"><span>Special Teams</span><span>81</span></li>
            </ul>
          </Card>
        </div>
      </div>

      <Modal
        title="Latest box score"
        isOpen={boxScoreOpen}
        onClose={() => setBoxScoreOpen(false)}
        footer={
          <button
            type="button"
            onClick={() => setBoxScoreOpen(false)}
            className="rounded-lg bg-primary.accent px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary.accent/90"
          >
            Close
          </button>
        }
      >
        {lastBoxScore ? (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-base font-semibold text-white">
              <span>
                {lastBoxScore.homeTeam.name} {lastBoxScore.homeTeam.points}
              </span>
              <span>
                {lastBoxScore.awayTeam.points} {lastBoxScore.awayTeam.name}
              </span>
            </div>
            <div className="grid gap-3 text-sm text-slate-300">
              {lastBoxScore.keyPlayers.map((player) => (
                <div key={player.playerId} className="rounded-lg bg-slate-900 px-3 py-2">
                  <p className="font-semibold text-white">{player.name}</p>
                  <p className="text-xs text-slate-400">{player.statLine}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-400">Box score not available yet.</p>
        )}
      </Modal>

      <Modal
        title="Season player stats"
        isOpen={playerStatsOpen}
        onClose={() => setPlayerStatsOpen(false)}
        footer={
          <button
            type="button"
            onClick={() => setPlayerStatsOpen(false)}
            className="rounded-lg bg-primary.accent px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary.accent/90"
          >
            Close
          </button>
        }
      >
        {playerStats ? (
          <div className="space-y-3 text-sm text-slate-200">
            <div className="rounded-lg bg-slate-900 px-3 py-2">
              <p className="font-semibold text-white">Team totals</p>
              <p className="text-xs text-slate-400">
                {playerStats.totalPoints} pts · {playerStats.totalYards} yds · {playerStats.totalTurnovers} turnovers across {" "}
                {playerStats.gamesPlayed} games
              </p>
            </div>
            <div>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-400">Starters</h4>
              <ul className="mt-2 space-y-2">
                {playerStats.starters.map((starter) => (
                  <li key={starter.playerId} className="rounded-lg bg-slate-900 px-3 py-2">
                    <p className="text-sm font-semibold text-white">
                      {starter.name} – {starter.position}
                    </p>
                    <p className="text-xs text-slate-400">{starter.statLine}</p>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-400">Season stats will appear after the first simulation.</p>
        )}
      </Modal>
    </div>
  );
}
