import { Standing } from "../../../types/league";
import { Card } from "../../../components/ui/Card";
import { useNavigate } from "react-router-dom";

type StandingsPreviewProps = {
  standings: Standing[];
};

export function StandingsPreview({ standings }: StandingsPreviewProps) {
  const navigate = useNavigate();
  const placeholder = [
    { name: "League Leaders", record: "0-0" },
    { name: "Playoff Contenders", record: "0-0" },
    { name: "Wild Card Bubble", record: "0-0" },
  ];
  const rows = standings.length
    ? standings.map((team) => ({
        key: team.teamId,
        label: `${team.name}`,
        record: `${team.wins}-${team.losses}${team.ties ? `-${team.ties}` : ""}`,
      }))
    : placeholder.map((team, index) => ({ key: index, label: team.name, record: team.record }));

  return (
    <Card>
      <div className="flex items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-semibold text-white">League standings</h3>
          <p className="text-xs uppercase tracking-wide text-slate-400">Top performers</p>
        </div>
        <button
          type="button"
          onClick={() => navigate("/standings")}
          className="rounded-lg bg-slate-800 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-200 transition hover:bg-slate-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary.accent"
        >
          View Full Standings
        </button>
      </div>
      <ul className="mt-4 space-y-2 text-sm text-slate-200">
        {rows.map((row) => (
          <li key={row.key} className="flex items-center justify-between rounded-xl bg-slate-900 px-4 py-3">
            <span>{row.label}</span>
            <span className="text-xs text-slate-400">{row.record}</span>
          </li>
        ))}
      </ul>
    </Card>
  );
}
