import { useMemo } from "react";
import { GameSummary, Standing } from "../../../types/league";
import { Card } from "../../../components/ui/Card";

type RecentResultsCardProps = {
  isLoading: boolean;
  error: string | null;
  lastResult: GameSummary | null;
  standings: Standing[];
  focusTeamId?: number;
  onViewBoxScore: () => void;
};

function formatResultLabel(game: GameSummary | null, focusTeamId: number): string {
  if (!game || game.homeScore === null || game.awayScore === null) {
    return "Awaiting the first result.";
  }
  const isHome = game.homeTeamId === focusTeamId;
  const focusScore = isHome ? game.homeScore : game.awayScore;
  const opponentScore = isHome ? game.awayScore : game.homeScore;
  const opponentName = isHome ? game.awayTeamName : game.homeTeamName;
  const outcome = focusScore > opponentScore ? "Win" : focusScore < opponentScore ? "Loss" : "Tie";
  return `${outcome} vs ${opponentName}`;
}

export function RecentResultsCard({
  isLoading,
  error,
  lastResult,
  standings,
  focusTeamId = 1,
  onViewBoxScore,
}: RecentResultsCardProps) {
  const summary = useMemo(() => {
    if (!lastResult || lastResult.homeScore === null || lastResult.awayScore === null) {
      return null;
    }
    const isHome = lastResult.homeTeamId === focusTeamId;
    const focusScore = isHome ? lastResult.homeScore : lastResult.awayScore;
    const opponentScore = isHome ? lastResult.awayScore : lastResult.homeScore;
    const opponent = isHome ? lastResult.awayTeamName : lastResult.homeTeamName;
    const opponentStanding = standings.find((team) =>
      team.teamId === (isHome ? lastResult.awayTeamId : lastResult.homeTeamId)
    );
    const opponentRecord = opponentStanding
      ? `${opponentStanding.wins}-${opponentStanding.losses}`
      : "record TBD";

    return {
      focusScore,
      opponentScore,
      opponent,
      opponentRecord,
      outcome: focusScore > opponentScore ? "Victory" : focusScore < opponentScore ? "Defeat" : "Draw",
    };
  }, [lastResult, standings]);

  return (
    <Card>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-400">Most recent result</p>
          {isLoading ? (
            <p className="text-sm text-slate-400">Loading game data…</p>
          ) : error ? (
            <p className="text-sm text-red-400">{error}</p>
          ) : (
            <>
              <h3 className="text-xl font-semibold text-white">
                {formatResultLabel(lastResult, focusTeamId)}
              </h3>
              {summary ? (
                <p className="text-sm text-slate-300">
                  {summary.focusScore} – {summary.opponentScore} vs {summary.opponent} ({summary.opponentRecord}) · {summary.outcome}
                </p>
              ) : (
                <p className="text-sm text-slate-300">Final score will appear after your first simulation.</p>
              )}
            </>
          )}
        </div>
        <div className="flex flex-col items-start gap-2 sm:items-end">
          <button
            type="button"
            onClick={onViewBoxScore}
            className="rounded-lg bg-primary.accent px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary.accent/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
          >
            View Box Score
          </button>
        </div>
      </div>
    </Card>
  );
}
