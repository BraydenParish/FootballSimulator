import { useNavigate } from "react-router-dom";
import { Player } from "../../../types/league";
import { Card } from "../../../components/ui/Card";

type Starter = {
  slot: string;
  player: Player | undefined;
};

type DepthChartPreviewProps = {
  starters: Starter[];
  onManageRoster: () => void;
};

function formatSlot(slot: string): string {
  return slot.replace(/1$/, "");
}

export function DepthChartPreview({ starters, onManageRoster }: DepthChartPreviewProps) {
  const navigate = useNavigate();

  return (
    <Card>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white">Depth chart preview</h3>
          <p className="mt-1 text-xs uppercase tracking-wide text-slate-400">Key starters</p>
        </div>
        <button
          type="button"
          onClick={() => navigate("/depth-chart")}
          className="rounded-lg bg-slate-800 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-200 transition hover:bg-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
        >
          Edit Depth Chart
        </button>
      </div>
      <ul className="mt-4 grid gap-3 text-sm text-slate-200">
        {starters.map((entry) => (
          <li key={entry.slot} className="flex items-center justify-between rounded-xl bg-slate-900 px-4 py-3">
            <div>
              <p className="text-xs uppercase tracking-wide text-slate-400">{formatSlot(entry.slot)}</p>
              <p className="text-base font-semibold text-white">
                {entry.player ? entry.player.name : "TBD"}
              </p>
            </div>
            <p className="text-xs text-slate-400">
              {entry.player ? `OVR ${entry.player.overall}` : "Awaiting assignment"}
            </p>
          </li>
        ))}
      </ul>
      <button
        type="button"
        onClick={onManageRoster}
        className="mt-4 w-full rounded-lg bg-primary.accent px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-primary.accent/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
      >
        View Player Stats
      </button>
    </Card>
  );
}
