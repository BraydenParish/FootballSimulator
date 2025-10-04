import { useNavigate } from "react-router-dom";
import { GameSummary, Standing } from "../../../types/league";
import { Card } from "../../../components/ui/Card";

type SimulationControlsProps = {
  isLoading: boolean;
  nextWeek: number;
  standings: Standing[];
  upcomingGame: GameSummary | null;
  focusTeamId: number;
  onSimulateWeek: () => void;
  onOpenPlayerStats: () => void;
};

function formatOpponent(
  game: GameSummary | null,
  standings: Standing[],
  focusTeamId: number
): string {
  if (!game) {
    return "Schedule not available";
  }
  const isHome = game.homeTeamId === focusTeamId;
  const opponentId = isHome ? game.awayTeamId : game.homeTeamId;
  const opponent = standings.find((team) => team.teamId === opponentId);
  const opponentRecord = opponent ? `${opponent.wins}-${opponent.losses}` : "record TBD";
  const opponentName = isHome ? game.awayTeamName : game.homeTeamName;
  return `${opponentName} (${opponentRecord}) · ${isHome ? "Home" : "Road"}`;
}

export function SimulationControls({
  isLoading,
  nextWeek,
  standings,
  upcomingGame,
  focusTeamId,
  onSimulateWeek,
  onOpenPlayerStats,
}: SimulationControlsProps) {
  const navigate = useNavigate();

  return (
    <Card>
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-400">Upcoming matchup</p>
          <h2 className="text-2xl font-semibold text-white">Week {nextWeek}</h2>
          <p className="text-sm text-slate-300">
            {formatOpponent(upcomingGame, standings, focusTeamId)}
          </p>
        </div>
        <div className="flex flex-col gap-2 sm:flex-row">
          <button
            type="button"
            onClick={onSimulateWeek}
            disabled={isLoading}
            className="rounded-xl bg-primary.accent px-4 py-2 text-sm font-semibold text-white shadow-lg transition hover:bg-primary.accent/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent disabled:cursor-wait disabled:bg-primary.accent/60"
          >
            {isLoading ? "Simulating…" : "Simulate Week"}
          </button>
          <button
            type="button"
            onClick={() => navigate("/free-agency")}
            className="rounded-xl bg-slate-800 px-4 py-2 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
          >
            Sign Free Agents
          </button>
          <button
            type="button"
            onClick={() => navigate("/trade-center")}
            className="rounded-xl bg-slate-800 px-4 py-2 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
          >
            Make a Trade
          </button>
          <button
            type="button"
            onClick={onOpenPlayerStats}
            className="rounded-xl bg-slate-800 px-4 py-2 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
          >
            View Player Stats
          </button>
          <button
            type="button"
            onClick={() => navigate(`/results/${Math.max(1, nextWeek - 1)}`)}
            className="rounded-xl bg-slate-800 px-4 py-2 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
          >
            Recent Results
          </button>
        </div>
      </div>
    </Card>
  );
}
