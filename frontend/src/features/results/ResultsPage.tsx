import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { leagueApi } from "../../api/client";
import { queryKeys } from "../../api/queryKeys";
import { Card } from "../../components/ui/Card";
import { InjuryReport, WeeklyGameResult } from "../../types/league";

const FOCUS_TEAM_ID = 1;

function useLatestWeek(): { latestCompleted: number | null; maxWeek: number } {
  const scheduleQuery = useQuery({ queryKey: queryKeys.schedule(), queryFn: () => leagueApi.fetchSchedule() });
  const games = scheduleQuery.data ?? [];
  const latestCompleted = useMemo(() => {
    const completed = games.filter((game) => Boolean(game.playedAt));
    if (!completed.length) {
      return null;
    }
    return Math.max(...completed.map((game) => game.week));
  }, [games]);

  const maxWeek = useMemo(() => (games.length ? Math.max(...games.map((game) => game.week)) : 1), [games]);

  return { latestCompleted, maxWeek };
}

function formatScore(team: WeeklyGameResult["homeTeam"], fallback: string): string {
  if (team.points === null || typeof team.points === "undefined") {
    return fallback;
  }
  return String(team.points);
}

function StatRow({
  label,
  stat,
}: {
  label: string;
  stat:
    | WeeklyGameResult["passingLeader"]
    | WeeklyGameResult["rushingLeader"]
    | WeeklyGameResult["receivingLeader"]
    | null;
}) {
  if (!stat) {
    return (
      <li className="rounded-lg bg-slate-900 px-3 py-2 text-xs text-slate-400">
        {label}: Data pending
      </li>
    );
  }
  return (
    <li className="rounded-lg bg-slate-900 px-3 py-2">
      <p className="text-sm font-semibold text-white">
        {label}: {stat.name} ({stat.position})
      </p>
      <p className="text-xs text-slate-400">{stat.statLine}</p>
    </li>
  );
}

function InjuryRow({ injury }: { injury: InjuryReport }) {
  return (
    <li className="rounded-lg bg-slate-900 px-3 py-2">
      <p className="text-sm font-semibold text-white">
        {injury.name} · {injury.position} ({injury.teamName})
      </p>
      <p className="text-xs text-slate-400">
        {injury.status} · {injury.description} · ETA {injury.expectedReturn}
      </p>
    </li>
  );
}

export function ResultsPage() {
  const params = useParams<{ week?: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const highlightGameId =
    typeof (location.state as { highlight?: number } | undefined)?.highlight === "number"
      ? (location.state as { highlight?: number }).highlight
      : null;

  const rawWeek = params.week ? Number.parseInt(params.week, 10) : NaN;
  const { latestCompleted, maxWeek } = useLatestWeek();

  const [currentWeek, setCurrentWeek] = useState<number>(() =>
    Number.isNaN(rawWeek) ? latestCompleted ?? 1 : rawWeek
  );

  useEffect(() => {
    if (!Number.isNaN(rawWeek)) {
      setCurrentWeek(rawWeek);
      return;
    }
    if (Number.isNaN(rawWeek) && latestCompleted) {
      setCurrentWeek(latestCompleted);
      navigate(`/results/${latestCompleted}`, { replace: true });
    }
  }, [rawWeek, latestCompleted, navigate]);

  const weekResultsQuery = useQuery({
    queryKey: queryKeys.weekResults(currentWeek),
    queryFn: () => leagueApi.fetchWeekResults(currentWeek),
    enabled: currentWeek > 0,
  });

  const gameResults = weekResultsQuery.data ?? [];

  const aggregatedInjuries = useMemo(() => {
    const byPlayer = new Map<number, InjuryReport>();
    gameResults.forEach((game) => {
      game.injuries.forEach((injury) => {
        if (!byPlayer.has(injury.playerId)) {
          byPlayer.set(injury.playerId, injury);
        }
      });
    });
    return Array.from(byPlayer.values());
  }, [gameResults]);

  const changeWeek = (nextWeek: number) => {
    const normalized = Math.min(Math.max(1, nextWeek), Math.max(maxWeek, 1));
    setCurrentWeek(normalized);
    navigate(`/results/${normalized}`);
  };

  const hasPrevious = currentWeek > 1;
  const hasNext = currentWeek < maxWeek;

  const focusGameId = useMemo(() => {
    const focusGame = gameResults.find(
      (game) => game.homeTeam.id === FOCUS_TEAM_ID || game.awayTeam.id === FOCUS_TEAM_ID
    );
    return focusGame?.gameId ?? null;
  }, [gameResults]);

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Weekly summary</p>
            <h2 className="text-2xl font-semibold text-white">Week {currentWeek} results</h2>
            <p className="text-sm text-slate-300">
              Review every matchup, star performances, and reported injuries from around the league.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => changeWeek(currentWeek - 1)}
              disabled={!hasPrevious}
              className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent disabled:cursor-not-allowed disabled:bg-slate-800/60"
            >
              Previous Week
            </button>
            <button
              type="button"
              onClick={() => changeWeek(currentWeek + 1)}
              disabled={!hasNext}
              className="rounded-lg bg-primary.accent px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary.accent/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent disabled:cursor-not-allowed disabled:bg-primary.accent/60"
            >
              Next Week
            </button>
          </div>
        </div>
      </Card>

      {weekResultsQuery.isLoading ? (
        <Card>
          <p className="text-sm text-slate-400">Loading weekly results…</p>
        </Card>
      ) : weekResultsQuery.isError ? (
        <Card>
          <p className="text-sm text-red-400">Unable to load results for this week.</p>
        </Card>
      ) : gameResults.length ? (
        <div className="space-y-6">
          {gameResults.map((game) => {
            const isFocus = focusGameId === game.gameId;
            const isHighlighted = highlightGameId === game.gameId;
            const statusLabel = game.playedAt ? "Final" : "Scheduled";
            return (
              <Card
                key={game.gameId}
                className={
                  isHighlighted || isFocus
                    ? "border border-primary.accent/60 bg-primary.accent/5"
                    : undefined
                }
              >
                <div className="flex flex-col gap-3 border-b border-white/10 pb-4 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-400">{statusLabel}</p>
                    <div className="mt-1 text-lg font-semibold text-white">
                      <span className={game.homeTeam.id === FOCUS_TEAM_ID ? "text-primary.accent" : undefined}>
                        {game.homeTeam.name}
                      </span>{" "}
                      {formatScore(game.homeTeam, "—")} – {formatScore(game.awayTeam, "—")}{" "}
                      <span className={game.awayTeam.id === FOCUS_TEAM_ID ? "text-primary.accent" : undefined}>
                        {game.awayTeam.name}
                      </span>
                    </div>
                  </div>
                  <div className="text-sm text-slate-300">
                    <p>
                      {game.homeTeam.abbreviation} vs {game.awayTeam.abbreviation}
                    </p>
                  </div>
                </div>
                <div className="mt-4 grid gap-6 lg:grid-cols-2">
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                      Offensive leaders
                    </h3>
                    <ul className="mt-2 space-y-2 text-sm text-slate-200">
                      <StatRow label="Passing" stat={game.passingLeader} />
                      <StatRow label="Rushing" stat={game.rushingLeader} />
                      <StatRow label="Receiving" stat={game.receivingLeader} />
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                      Defensive standouts
                    </h3>
                    <ul className="mt-2 space-y-2 text-sm text-slate-200">
                      {game.defensiveLeaders.length ? (
                        game.defensiveLeaders.map((leader) => (
                          <li key={leader.playerId} className="rounded-lg bg-slate-900 px-3 py-2">
                            <p className="text-sm font-semibold text-white">
                              {leader.name} ({leader.position})
                            </p>
                            <p className="text-xs text-slate-400">{leader.statLine}</p>
                          </li>
                        ))
                      ) : (
                        <li className="rounded-lg bg-slate-900 px-3 py-2 text-xs text-slate-400">
                          Defensive stats pending
                        </li>
                      )}
                    </ul>
                  </div>
                </div>
                <div className="mt-4">
                  <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-400">Injuries</h3>
                  {game.injuries.length ? (
                    <ul className="mt-2 space-y-2 text-sm text-slate-200">
                      {game.injuries.map((injury) => (
                        <InjuryRow key={`${game.gameId}-${injury.playerId}`} injury={injury} />
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-2 text-xs text-slate-400">No injuries reported in this matchup.</p>
                  )}
                </div>
              </Card>
            );
          })}
        </div>
      ) : (
        <Card>
          <p className="text-sm text-slate-400">
            Results are not available for this week yet. Run a simulation from the dashboard to generate outcomes.
          </p>
        </Card>
      )}

      <Card>
        <h3 className="text-sm font-semibold uppercase tracking-wide text-slate-400">League injury report</h3>
        {aggregatedInjuries.length ? (
          <ul className="mt-3 space-y-2 text-sm text-slate-200">
            {aggregatedInjuries.map((injury) => (
              <InjuryRow key={`injury-${injury.playerId}`} injury={injury} />
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-xs text-slate-400">No active injuries reported for Week {currentWeek}.</p>
        )}
      </Card>
    </div>
  );
}
