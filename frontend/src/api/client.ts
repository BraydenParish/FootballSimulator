import {
  BoxScore,
  DepthChartEntry,
  FreeAgentPool,
  GameSummary,
  Player,
  SignResult,
  SimulationRequest,
  SimulationResult,
  Standing,
  Team,
  TeamStats,
  TradeExecutionResult,
  TradeProposal,
  TradeProposalResult,
  WeeklyGameResult,
} from "../types/league";
import * as mockAdapter from "./mockAdapter";

const API_MODE = (import.meta.env.VITE_API_MODE ?? "mock").toLowerCase();
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

type RawPlayer = Record<string, unknown> & {
  id: number;
  name: string;
  position: string;
  overall_rating?: number;
  overall?: number;
  age?: number;
  salary?: number;
  contract_value?: number;
  contractYears?: number;
  contract_years?: number;
  team_id?: number | null;
  teamId?: number | null;
  depth_chart_position?: string | null;
  depthChartSlot?: string | null;
  status?: string;
};

function mapStatus(status: string | undefined): Player["status"] {
  if (!status) {
    return "active";
  }
  if (status === "free_agent") {
    return "free-agent";
  }
  if (status === "practice_squad") {
    return "practice";
  }
  return status as Player["status"];
}

function mapPlayer(raw: RawPlayer): Player {
  return {
    id: raw.id,
    name: raw.name,
    position: raw.position,
    overall:
      typeof raw.overall === "number"
        ? raw.overall
        : Number(raw.overall ?? raw.overall_rating ?? 0),
    age:
      typeof raw.age === "number"
        ? raw.age
        : raw.age !== undefined
        ? Number(raw.age)
        : 0,
    contractValue:
      typeof raw.contract_value === "number"
        ? raw.contract_value
        : raw.contract_value !== undefined
        ? Number(raw.contract_value)
        : raw.salary !== undefined
        ? Number(raw.salary)
        : 0,
    contractYears:
      typeof raw.contractYears === "number"
        ? raw.contractYears
        : raw.contractYears !== undefined
        ? Number(raw.contractYears)
        : raw.contract_years !== undefined
        ? Number(raw.contract_years)
        : 0,
    teamId:
      raw.teamId !== undefined
        ? (raw.teamId as number | null)
        : raw.team_id !== undefined
        ? (raw.team_id as number | null)
        : null,
    depthChartSlot: (raw.depthChartSlot ?? raw.depth_chart_position ?? null) as string | null,
    status: mapStatus(typeof raw.status === "string" ? raw.status : undefined),
  };
}

function mapPlayers(rawPlayers: RawPlayer[] | undefined): Player[] {
  if (!rawPlayers) {
    return [];
  }
  return rawPlayers.map(mapPlayer);
}

type RawFreeAgentsResponse = {
  year: number;
  players: RawPlayer[];
};

type RawSignResponse = {
  team: Team;
  player: RawPlayer;
};

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
      fetchWeekResults: mockAdapter.fetchWeekResults,
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
      async fetchWeekResults(week: number): Promise<WeeklyGameResult[]> {
        return request<WeeklyGameResult[]>(`/games/week/${week}`);
      },
      async simulateWeek(payload: SimulationRequest): Promise<SimulationResult> {
        return request<SimulationResult>("/simulate-week", {
          method: "POST",
          body: JSON.stringify(payload),
        });
      },
      async fetchFreeAgents(): Promise<FreeAgentPool> {
        const response = await request<RawFreeAgentsResponse>("/free-agents");
        return {
          year: response.year,
          players: mapPlayers(response.players),
        };
      },
      async signFreeAgent(teamId: number, playerId: number): Promise<SignResult> {
        const result = await request<RawSignResponse>(`/teams/${teamId}/sign`, {
          method: "POST",
          body: JSON.stringify({ teamId, playerId }),
        });
        return {
          message: `Signed ${result.player.name} to the roster`,
          player: mapPlayer(result.player),
          team: result.team,
        };
      },
      async evaluateTrade(proposal: TradeProposal): Promise<TradeProposalResult> {
        return request<TradeProposalResult>("/trades/propose", {
          method: "POST",
          body: JSON.stringify(proposal),
        });
      },
      async executeTrade(proposal: TradeProposal): Promise<TradeExecutionResult> {
        return request<TradeExecutionResult>("/trades/execute", {
          method: "POST",
          body: JSON.stringify(proposal),
        });
      },
      async fetchTeamRoster(teamId: number): Promise<Player[]> {
        const roster = await request<RawPlayer[]>(`/players?team_id=${teamId}`);
        return mapPlayers(roster);
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
