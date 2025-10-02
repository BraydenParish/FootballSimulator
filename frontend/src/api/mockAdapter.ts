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
import { useMockDataStore } from "../store/mockData";

const getState = () => useMockDataStore.getState();

export async function fetchStandings(): Promise<Standing[]> {
  return getState().computeStandings();
}

export async function fetchTeams(): Promise<Team[]> {
  return getState().teams;
}

export async function fetchSchedule(teamId?: number): Promise<GameSummary[]> {
  const games = getState().games;
  if (!teamId) {
    return games;
  }
  return games.filter((game) => game.homeTeamId === teamId || game.awayTeamId === teamId);
}

export async function fetchBoxScores(teamId?: number): Promise<BoxScore[]> {
  const scores = getState().boxScores;
  if (!teamId) {
    return scores;
  }
  return scores.filter(
    (box) => box.homeTeam.teamId === teamId || box.awayTeam.teamId === teamId
  );
}

export async function simulateWeek(request: SimulationRequest): Promise<SimulationResult> {
  return getState().simulateWeek(request.week, request.mode);
}

export async function fetchFreeAgents(): Promise<Player[]> {
  return getState().freeAgents;
}

export async function signFreeAgent(
  teamId: number,
  playerId: number
): Promise<TradeEvaluation> {
  return getState().signFreeAgent(teamId, playerId);
}

export async function evaluateTrade(proposal: TradeProposal): Promise<TradeEvaluation> {
  return getState().evaluateTrade(proposal);
}

export async function executeTrade(proposal: TradeProposal): Promise<TradeEvaluation> {
  const validation = getState().evaluateTrade(proposal);
  if (!validation.success) {
    return validation;
  }
  return getState().executeTrade(proposal);
}

export async function fetchTeamRoster(teamId: number): Promise<Player[]> {
  return getState().getTeamRoster(teamId);
}

export async function updateDepthChart(
  teamId: number,
  entries: DepthChartEntry[]
): Promise<void> {
  getState().updateDepthChart(teamId, entries);
}

export async function fetchTeamStats(teamId: number): Promise<TeamStats> {
  return getState().getTeamStats(teamId);
}

export async function uploadDepthCharts(text: string): Promise<void> {
  getState().loadDepthCharts(text);
}

export async function uploadFreeAgents(text: string): Promise<void> {
  getState().loadFreeAgents(text);
}

export async function uploadSchedule(text: string): Promise<void> {
  getState().loadSchedule(text);
}

export async function uploadRatings(text: string): Promise<void> {
  getState().loadRatings(text);
}

export async function uploadRules(text: string): Promise<void> {
  getState().loadRules(text);
}

export async function uploadSimulationRules(text: string): Promise<void> {
  getState().loadSimulationRules(text);
}
