import { useState } from "react";
import { leagueApi } from "../../api/client";
import { Card } from "../../components/ui/Card";
import { UploadKind } from "../../types/league";

const uploadConfig: Array<{
  label: string;
  description: string;
  kind: UploadKind;
  accept: string;
}> = [
  {
    label: "Depth chart assignments",
    description: "CSV or pipe-delimited text with Team,Slot,Player columns.",
    kind: "depthCharts",
    accept: ".txt,.csv",
  },
  {
    label: "Player ratings",
    description: "Raw ratings file. Stored for reference in mock mode.",
    kind: "ratings",
    accept: ".txt,.csv",
  },
  {
    label: "2025 free agents",
    description: "List of players entering the 2025 pool.",
    kind: "freeAgents2025",
    accept: ".txt,.csv",
  },
  {
    label: "2026 free agents",
    description: "List of players entering the 2026 pool.",
    kind: "freeAgents2026",
    accept: ".txt,.csv",
  },
  {
    label: "Game rules",
    description: "Roster and cap rules used for validation.",
    kind: "rules",
    accept: ".txt",
  },
  {
    label: "Simulation rules",
    description: "Formula definitions powering the sim engine.",
    kind: "simulationRules",
    accept: ".txt",
  },
  {
    label: "Season schedule",
    description: "CSV with week,home,away columns.",
    kind: "schedule",
    accept: ".csv",
  },
];

async function uploadFile(kind: UploadKind, text: string) {
  switch (kind) {
    case "depthCharts":
      await leagueApi.uploadDepthCharts(text);
      break;
    case "ratings":
      await leagueApi.uploadRatings(text);
      break;
    case "freeAgents2025":
    case "freeAgents2026":
      await leagueApi.uploadFreeAgents(text);
      break;
    case "rules":
      await leagueApi.uploadRules(text);
      break;
    case "simulationRules":
      await leagueApi.uploadSimulationRules(text);
      break;
    case "schedule":
      await leagueApi.uploadSchedule(text);
      break;
  }
}

export function DataUploadsPage() {
  const [status, setStatus] = useState<string | null>(null);

  const handleFileChange = async (kind: UploadKind, fileList: FileList | null) => {
    if (!fileList?.length) {
      return;
    }
    const file = fileList[0];
    const text = await file.text();
    await uploadFile(kind, text);
    setStatus(`${file.name} processed successfully.`);
  };

  return (
    <div className="space-y-6">
      <Card>
        <h2 className="text-2xl font-semibold text-white">Dataset uploads</h2>
        <p className="mt-2 text-sm text-slate-300">
          Load league configuration files into the mock data layer. Uploads update the Zustand store so
          the UI can exercise flows before the backend is ready.
        </p>
        {status ? (
          <div className="mt-3 rounded-lg bg-primary.accent/10 px-4 py-2 text-xs font-semibold text-primary.accent">
            {status}
          </div>
        ) : null}
      </Card>

      <div className="grid gap-6 lg:grid-cols-2">
        {uploadConfig.map((item) => (
          <Card key={item.kind}>
            <h3 className="text-lg font-semibold text-white">{item.label}</h3>
            <p className="mt-1 text-sm text-slate-300">{item.description}</p>
            <input
              type="file"
              accept={item.accept}
              onChange={(event) => handleFileChange(item.kind, event.target.files)}
              className="mt-4 w-full cursor-pointer rounded-lg border border-dashed border-white/20 bg-slate-900 px-4 py-3 text-sm text-slate-200 file:mr-4 file:rounded-lg file:border-0 file:bg-primary.accent file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white"
            />
          </Card>
        ))}
      </div>
    </div>
  );
}
