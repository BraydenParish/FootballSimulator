// @ts-nocheck
import { rest, setupWorker, type SetupWorkerApi } from "msw";
import { useMockDataStore } from "../store/mockData";
import {
  DepthChartEntry,
  SimulationRequest,
  TradeProposal,
  TradeProposalResult,
} from "../types/league";
import { TestSeed } from "../types/testSeed";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

let workerInstance: SetupWorkerApi | null = null;
let activeSeasonYear = 2025;

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value));
}

function hydrateSeed(seed: TestSeed) {
  const teams = clone(seed.teams);
  const players = clone(seed.players);
  const freeAgents = clone(seed.freeAgents);
  const store = useMockDataStore.getState();

  const games = seed.schedule.map((matchup, index) => {
    const home = teams.find((team) => team.id === matchup.homeTeamId);
    const away = teams.find((team) => team.id === matchup.awayTeamId);
    if (!home || !away) {
      throw new Error("Seed schedule references an unknown team.");
    }
    return {
      id: matchup.id ?? index + 1,
      week: matchup.week,
      homeTeamId: home.id,
      awayTeamId: away.id,
      homeScore: matchup.homeScore ?? null,
      awayScore: matchup.awayScore ?? null,
      playedAt: matchup.playedAt ?? null,
      homeTeamName: home.name,
      homeTeamAbbreviation: home.abbreviation,
      awayTeamName: away.name,
      awayTeamAbbreviation: away.abbreviation,
    };
  });

  const highestRosterId = players.reduce((max, player) => Math.max(max, player.id ?? 0), 0);
  const highestFreeAgentId = freeAgents.reduce((max, player) => Math.max(max, player.id ?? 0), 0);
  const nextPlayerId = Math.max(store.nextPlayerId, highestRosterId + 1, highestFreeAgentId + 1);

  activeSeasonYear = seed.seasonYear ?? 2025;

  useMockDataStore.setState({
    teams,
    players,
    freeAgents,
    games,
    boxScores: [],
    injuryLog: clone(seed.injuryLog ?? {}),
    nextPlayerId,
  });
}

const handlers = [
  rest.get(`${API_BASE}/teams`, (_req, res, ctx) => {
    return res(ctx.json(useMockDataStore.getState().teams));
  }),
  rest.get(`${API_BASE}/free-agents`, (_req, res, ctx) => {
    const state = useMockDataStore.getState();
    return res(ctx.json({ year: activeSeasonYear, players: state.freeAgents }));
  }),
  rest.post(`${API_BASE}/free-agents/sign`, async (req, res, ctx) => {
    const body = await req.json<{ teamId: number; playerId: number }>();
    const result = useMockDataStore.getState().signFreeAgent(body.teamId, body.playerId);
    return res(ctx.json(result));
  }),
  rest.get(`${API_BASE}/players`, (req, res, ctx) => {
    const teamIdParam = req.url.searchParams.get("team_id");
    if (!teamIdParam) {
      return res(ctx.json([]));
    }
    const teamId = Number.parseInt(teamIdParam, 10);
    const roster = useMockDataStore.getState().getTeamRoster(teamId);
    return res(ctx.json(roster));
  }),
  rest.get(`${API_BASE}/games`, (req, res, ctx) => {
    const teamIdParam = req.url.searchParams.get("team_id");
    const games = useMockDataStore.getState().games;
    if (!teamIdParam) {
      return res(ctx.json(games));
    }
    const teamId = Number.parseInt(teamIdParam, 10);
    const filtered = games.filter(
      (game) => game.homeTeamId === teamId || game.awayTeamId === teamId
    );
    return res(ctx.json(filtered));
  }),
  rest.get(`${API_BASE}/games/box-scores`, (req, res, ctx) => {
    const teamIdParam = req.url.searchParams.get("team_id");
    const boxes = useMockDataStore.getState().boxScores;
    if (!teamIdParam) {
      return res(ctx.json(boxes));
    }
    const teamId = Number.parseInt(teamIdParam, 10);
    const filtered = boxes.filter(
      (box) => box.homeTeam.teamId === teamId || box.awayTeam.teamId === teamId
    );
    return res(ctx.json(filtered));
  }),
  rest.post(`${API_BASE}/simulate-week`, async (req, res, ctx) => {
    const payload = await req.json<SimulationRequest>();
    const result = useMockDataStore.getState().simulateWeek(payload.week, payload.mode);
    return res(ctx.json(result));
  }),
  rest.get(`${API_BASE}/games/week/:week`, (req, res, ctx) => {
    const week = Number.parseInt(req.params.week as string, 10);
    const results = useMockDataStore.getState().getWeekResults(week);
    return res(ctx.json(results));
  }),
  rest.get(`${API_BASE}/standings`, (_req, res, ctx) => {
    return res(ctx.json(useMockDataStore.getState().computeStandings()));
  }),
  rest.post(`${API_BASE}/teams/:teamId/depth-chart`, async (req, res, ctx) => {
    const teamId = Number.parseInt(req.params.teamId as string, 10);
    const body = await req.json<{ entries: DepthChartEntry[] }>();
    useMockDataStore.getState().updateDepthChart(teamId, body.entries ?? []);
    return res(ctx.status(204));
  }),
  rest.post(`${API_BASE}/trades/propose`, async (req, res, ctx) => {
    const proposal = await req.json<TradeProposal>();
    const result = useMockDataStore.getState().evaluateTrade(proposal) as TradeProposalResult;
    return res(ctx.json(result));
  }),
  rest.post(`${API_BASE}/trades/execute`, async (req, res, ctx) => {
    const proposal = await req.json<TradeProposal>();
    const result = useMockDataStore.getState().executeTrade(proposal);
    return res(ctx.json(result));
  }),
  rest.get(`${API_BASE}/teams/:teamId/stats`, (req, res, ctx) => {
    const teamId = Number.parseInt(req.params.teamId as string, 10);
    const stats = useMockDataStore.getState().getTeamStats(teamId);
    return res(ctx.json(stats));
  }),
];

async function ensureWorker() {
  if (!workerInstance) {
    workerInstance = setupWorker(...handlers);
    await workerInstance.start({ quiet: true });
  } else {
    workerInstance.resetHandlers(...handlers);
  }
}

export async function startWorker(seed: TestSeed) {
  hydrateSeed(seed);
  await ensureWorker();
}
