import {
  BoxScore,
  DepthChartEntry,
  GameSummary,
  Player,
  SimulationRequest,
  SimulationResult,
  Standing,
  Team,
  TeamStats,
  TradeEvaluation,
  TradeProposal,
} from "../types/league";
import * as mockAdapter from "./mockAdapter";

const API_MODE = (import.meta.env.VITE_API_MODE ?? "mock").toLowerCase();
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
    },
    ...init,
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export const leagueApi = API_MODE === "mock"
  ? {
      fetchStandings: mockAdapter.fetchStandings,
      fetchTeams: mockAdapter.fetchTeams,
      fetchSchedule: mockAdapter.fetchSchedule,
      fetchBoxScores: mockAdapter.fetchBoxScores,
      simulateWeek: mockAdapter.simulateWeek,
      fetchFreeAgents: mockAdapter.fetchFreeAgents,
      signFreeAgent: mockAdapter.signFreeAgent,
      evaluateTrade: mockAdapter.evaluateTrade,
      executeTrade: mockAdapter.executeTrade,
      fetchTeamRoster: mockAdapter.fetchTeamRoster,
      updateDepthChart: mockAdapter.updateDepthChart,
      fetchTeamStats: mockAdapter.fetchTeamStats,
      uploadDepthCharts: mockAdapter.uploadDepthCharts,
      uploadFreeAgents: mockAdapter.uploadFreeAgents,
      uploadSchedule: mockAdapter.uploadSchedule,
      uploadRatings: mockAdapter.uploadRatings,
      uploadRules: mockAdapter.uploadRules,
      uploadSimulationRules: mockAdapter.uploadSimulationRules,
    }
  : {
      async fetchStandings(): Promise<Standing[]> {
        return request<Standing[]>("/standings");
      },
      async fetchTeams(): Promise<Team[]> {
        return request<Team[]>("/teams");
      },
      async fetchSchedule(teamId?: number): Promise<GameSummary[]> {
        const query = teamId ? `?team_id=${teamId}` : "";
        return request<GameSummary[]>(`/games${query}`);
      },
      async fetchBoxScores(teamId?: number): Promise<BoxScore[]> {
        const query = teamId ? `?team_id=${teamId}` : "";
        return request<BoxScore[]>(`/games/box-scores${query}`);
      },
      async simulateWeek(payload: SimulationRequest): Promise<SimulationResult> {
        return request<SimulationResult>("/simulate-week", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      },
      async fetchFreeAgents(): Promise<Player[]> {
        return request<Player[]>("/free-agents");
      },
      async signFreeAgent(teamId: number, playerId: number): Promise<TradeEvaluation> {
        return request<TradeEvaluation>(`/teams/${teamId}/sign`, {
          method: "POST",
          body: JSON.stringify({ player_id: playerId }),
        });
      },
      async evaluateTrade(proposal: TradeProposal): Promise<TradeEvaluation> {
        return request<TradeEvaluation>("/trade/validate", {
          method: "POST",
          body: JSON.stringify(proposal),
        });
      },
      async executeTrade(proposal: TradeProposal): Promise<TradeEvaluation> {
        return request<TradeEvaluation>("/trade", {
          method: "POST",
          body: JSON.stringify(proposal),
        });
      },
      async fetchTeamRoster(teamId: number): Promise<Player[]> {
        return request<Player[]>(`/players?team_id=${teamId}`);
      },
      async updateDepthChart(teamId: number, entries: DepthChartEntry[]): Promise<void> {
        await request<void>(`/teams/${teamId}/depth-chart`, {
          method: "POST",
          body: JSON.stringify({ entries }),
        });
      },
      async fetchTeamStats(teamId: number): Promise<TeamStats> {
        return request<TeamStats>(`/teams/${teamId}/stats`);
      },
      async uploadDepthCharts(): Promise<void> {
        throw new Error("Uploads require mock mode.");
      },
      async uploadFreeAgents(): Promise<void> {
        throw new Error("Uploads require mock mode.");
      },
      async uploadSchedule(): Promise<void> {
        throw new Error("Uploads require mock mode.");
      },
      async uploadRatings(): Promise<void> {
        throw new Error("Uploads require mock mode.");
      },
      async uploadRules(): Promise<void> {
        throw new Error("Uploads require mock mode.");
      },
      async uploadSimulationRules(): Promise<void> {
        throw new Error("Uploads require mock mode.");
      },
    } as const;

export type LeagueApi = typeof leagueApi;
