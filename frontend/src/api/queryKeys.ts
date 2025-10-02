export const queryKeys = {
  teams: ["teams"] as const,
  standings: ["standings"] as const,
  schedule: (teamId?: number) => ["schedule", teamId ?? "all"] as const,
  boxScores: (teamId?: number) => ["boxScores", teamId ?? "all"] as const,
  freeAgents: ["freeAgents"] as const,
  roster: (teamId: number) => ["roster", teamId] as const,
  teamStats: (teamId: number) => ["teamStats", teamId] as const,
};
