import { create } from "zustand";
import {
  BoxScore,
  DepthChartEntry,
  GameSummary,
  Player,
  SimulationMode,
  SimulationResult,
  Standing,
  Team,
  TeamStats,
  TradeEvaluation,
  TradeProposal,
} from "../types/league";
import { parseDepthChartFile, parseFreeAgentFile, parseScheduleCsv } from "../utils/parsers";

const ROSTER_LIMIT = 53;
const ELITE_QB_THRESHOLD = 90;
const KEY_POSITIONS: string[] = ["QB", "RB", "WR"];

const defaultTeams: Team[] = [
  {
    id: 1,
    name: "Team Alpha",
    abbreviation: "ALP",
    conference: "Coastal",
    division: "North",
    rating: 86,
    salaryCap: 200,
    salarySpent: 150,
  },
  {
    id: 2,
    name: "Team Beta",
    abbreviation: "BET",
    conference: "Coastal",
    division: "North",
    rating: 83,
    salaryCap: 200,
    salarySpent: 147,
  },
  {
    id: 3,
    name: "Team Gamma",
    abbreviation: "GAM",
    conference: "Heartland",
    division: "South",
    rating: 81,
    salaryCap: 200,
    salarySpent: 142,
  },
  {
    id: 4,
    name: "Team Delta",
    abbreviation: "DEL",
    conference: "Heartland",
    division: "South",
    rating: 79,
    salaryCap: 200,
    salarySpent: 140,
  },
];

const defaultPlayers: Player[] = [
  {
    id: 1,
    name: "Alpha Quarterback",
    position: "QB",
    overall: 88,
    age: 28,
    contractValue: 20,
    contractYears: 3,
    teamId: 1,
    depthChartSlot: "QB1",
    status: "active",
  },
  {
    id: 2,
    name: "Alpha Runner",
    position: "RB",
    overall: 84,
    age: 26,
    contractValue: 9,
    contractYears: 2,
    teamId: 1,
    depthChartSlot: "RB1",
    status: "active",
  },
  {
    id: 3,
    name: "Alpha Receiver",
    position: "WR",
    overall: 87,
    age: 27,
    contractValue: 12,
    contractYears: 4,
    teamId: 1,
    depthChartSlot: "WR1",
    status: "active",
  },
  {
    id: 4,
    name: "Alpha Tight End",
    position: "TE",
    overall: 82,
    age: 30,
    contractValue: 6,
    contractYears: 2,
    teamId: 1,
    depthChartSlot: "TE1",
    status: "active",
  },
  {
    id: 5,
    name: "Alpha Linebacker",
    position: "LB",
    overall: 85,
    age: 29,
    contractValue: 8,
    contractYears: 3,
    teamId: 1,
    depthChartSlot: "LB1",
    status: "active",
  },
  {
    id: 6,
    name: "Alpha Corner",
    position: "CB",
    overall: 83,
    age: 27,
    contractValue: 7,
    contractYears: 3,
    teamId: 1,
    depthChartSlot: "CB1",
    status: "active",
  },
  {
    id: 7,
    name: "Beta Quarterback",
    position: "QB",
    overall: 86,
    age: 29,
    contractValue: 18,
    contractYears: 3,
    teamId: 2,
    depthChartSlot: "QB1",
    status: "active",
  },
  {
    id: 8,
    name: "Beta Runner",
    position: "RB",
    overall: 82,
    age: 26,
    contractValue: 8,
    contractYears: 2,
    teamId: 2,
    depthChartSlot: "RB1",
    status: "active",
  },
  {
    id: 9,
    name: "Beta Receiver",
    position: "WR",
    overall: 85,
    age: 27,
    contractValue: 11,
    contractYears: 4,
    teamId: 2,
    depthChartSlot: "WR1",
    status: "active",
  },
  {
    id: 10,
    name: "Beta Tight End",
    position: "TE",
    overall: 80,
    age: 30,
    contractValue: 5,
    contractYears: 1,
    teamId: 2,
    depthChartSlot: "TE1",
    status: "active",
  },
  {
    id: 11,
    name: "Beta Linebacker",
    position: "LB",
    overall: 83,
    age: 28,
    contractValue: 7,
    contractYears: 2,
    teamId: 2,
    depthChartSlot: "LB1",
    status: "active",
  },
  {
    id: 12,
    name: "Beta Corner",
    position: "CB",
    overall: 82,
    age: 27,
    contractValue: 6,
    contractYears: 2,
    teamId: 2,
    depthChartSlot: "CB1",
    status: "active",
  },
  {
    id: 13,
    name: "Gamma Quarterback",
    position: "QB",
    overall: 82,
    age: 28,
    contractValue: 14,
    contractYears: 2,
    teamId: 3,
    depthChartSlot: "QB1",
    status: "active",
  },
  {
    id: 14,
    name: "Gamma Runner",
    position: "RB",
    overall: 80,
    age: 25,
    contractValue: 6,
    contractYears: 2,
    teamId: 3,
    depthChartSlot: "RB1",
    status: "active",
  },
  {
    id: 15,
    name: "Gamma Receiver",
    position: "WR",
    overall: 83,
    age: 26,
    contractValue: 9,
    contractYears: 3,
    teamId: 3,
    depthChartSlot: "WR1",
    status: "active",
  },
  {
    id: 16,
    name: "Gamma Tight End",
    position: "TE",
    overall: 78,
    age: 30,
    contractValue: 4,
    contractYears: 1,
    teamId: 3,
    depthChartSlot: "TE1",
    status: "active",
  },
  {
    id: 17,
    name: "Gamma Linebacker",
    position: "LB",
    overall: 81,
    age: 27,
    contractValue: 6,
    contractYears: 2,
    teamId: 3,
    depthChartSlot: "LB1",
    status: "active",
  },
  {
    id: 18,
    name: "Gamma Corner",
    position: "CB",
    overall: 80,
    age: 26,
    contractValue: 5,
    contractYears: 2,
    teamId: 3,
    depthChartSlot: "CB1",
    status: "active",
  },
  {
    id: 19,
    name: "Delta Quarterback",
    position: "QB",
    overall: 79,
    age: 28,
    contractValue: 12,
    contractYears: 2,
    teamId: 4,
    depthChartSlot: "QB1",
    status: "active",
  },
  {
    id: 20,
    name: "Delta Runner",
    position: "RB",
    overall: 78,
    age: 26,
    contractValue: 5,
    contractYears: 2,
    teamId: 4,
    depthChartSlot: "RB1",
    status: "active",
  },
  {
    id: 21,
    name: "Delta Receiver",
    position: "WR",
    overall: 80,
    age: 27,
    contractValue: 8,
    contractYears: 3,
    teamId: 4,
    depthChartSlot: "WR1",
    status: "active",
  },
  {
    id: 22,
    name: "Delta Tight End",
    position: "TE",
    overall: 76,
    age: 30,
    contractValue: 3,
    contractYears: 1,
    teamId: 4,
    depthChartSlot: "TE1",
    status: "active",
  },
  {
    id: 23,
    name: "Delta Linebacker",
    position: "LB",
    overall: 79,
    age: 28,
    contractValue: 5,
    contractYears: 2,
    teamId: 4,
    depthChartSlot: "LB1",
    status: "active",
  },
  {
    id: 24,
    name: "Delta Corner",
    position: "CB",
    overall: 78,
    age: 27,
    contractValue: 4,
    contractYears: 2,
    teamId: 4,
    depthChartSlot: "CB1",
    status: "active",
  },
];

const defaultFreeAgents: Player[] = [
  {
    id: 101,
    name: "Free Agent Quarterback",
    position: "QB",
    overall: 75,
    age: 30,
    contractValue: 3,
    contractYears: 1,
    teamId: null,
    depthChartSlot: null,
    status: "free-agent",
  },
  {
    id: 102,
    name: "Free Agent Runner",
    position: "RB",
    overall: 74,
    age: 27,
    contractValue: 2,
    contractYears: 1,
    teamId: null,
    depthChartSlot: null,
    status: "free-agent",
  },
  {
    id: 103,
    name: "Free Agent Defender",
    position: "LB",
    overall: 76,
    age: 28,
    contractValue: 2,
    contractYears: 1,
    teamId: null,
    depthChartSlot: null,
    status: "free-agent",
  },
];

function sumContractValue(players: Player[]): number {
  return players.reduce((total, player) => total + player.contractValue, 0);
}

function countEliteQuarterbacks(roster: Player[]): number {
  return roster.filter((player) => player.position === "QB" && player.overall >= ELITE_QB_THRESHOLD).length;
}

const defaultGames: GameSummary[] = [
  {
    id: 1,
    week: 1,
    homeTeamId: 1,
    awayTeamId: 2,
    homeScore: 24,
    awayScore: 20,
    playedAt: new Date().toISOString(),
    homeTeamName: "Team Alpha",
    homeTeamAbbreviation: "ALP",
    awayTeamName: "Team Beta",
    awayTeamAbbreviation: "BET",
  },
  {
    id: 2,
    week: 1,
    homeTeamId: 3,
    awayTeamId: 4,
    homeScore: 17,
    awayScore: 21,
    playedAt: new Date().toISOString(),
    homeTeamName: "Team Gamma",
    homeTeamAbbreviation: "GAM",
    awayTeamName: "Team Delta",
    awayTeamAbbreviation: "DEL",
  },
  {
    id: 3,
    week: 2,
    homeTeamId: 2,
    awayTeamId: 1,
    homeScore: null,
    awayScore: null,
    playedAt: null,
    homeTeamName: "Team Beta",
    homeTeamAbbreviation: "BET",
    awayTeamName: "Team Alpha",
    awayTeamAbbreviation: "ALP",
  },
  {
    id: 4,
    week: 2,
    homeTeamId: 4,
    awayTeamId: 3,
    homeScore: null,
    awayScore: null,
    playedAt: null,
    homeTeamName: "Team Delta",
    homeTeamAbbreviation: "DEL",
    awayTeamName: "Team Gamma",
    awayTeamAbbreviation: "GAM",
  },
];

const defaultBoxScores: BoxScore[] = [
  {
    gameId: 1,
    week: 1,
    homeTeam: { teamId: 1, name: "Team Alpha", points: 24, yards: 365, turnovers: 1 },
    awayTeam: { teamId: 2, name: "Team Beta", points: 20, yards: 342, turnovers: 2 },
    keyPlayers: [
      {
        playerId: 1,
        name: "Alpha Quarterback",
        position: "QB",
        teamId: 1,
        statLine: "248 pass yds · 2 TD · 1 INT",
      },
      {
        playerId: 2,
        name: "Alpha Runner",
        position: "RB",
        teamId: 1,
        statLine: "96 rush yds · 1 TD",
      },
      {
        playerId: 9,
        name: "Beta Receiver",
        position: "WR",
        teamId: 2,
        statLine: "7 rec · 112 yds",
      },
    ],
  },
  {
    gameId: 2,
    week: 1,
    homeTeam: { teamId: 3, name: "Team Gamma", points: 17, yards: 320, turnovers: 1 },
    awayTeam: { teamId: 4, name: "Team Delta", points: 21, yards: 338, turnovers: 0 },
    keyPlayers: [
      {
        playerId: 21,
        name: "Delta Receiver",
        position: "WR",
        teamId: 4,
        statLine: "6 rec · 98 yds · 1 TD",
      },
      {
        playerId: 19,
        name: "Delta Quarterback",
        position: "QB",
        teamId: 4,
        statLine: "214 pass yds · 2 TD",
      },
      {
        playerId: 18,
        name: "Gamma Corner",
        position: "CB",
        teamId: 3,
        statLine: "1 INT · 3 PD",
      },
    ],
  },
];

type MockDataState = {
  teams: Team[];
  players: Player[];
  freeAgents: Player[];
  games: GameSummary[];
  boxScores: BoxScore[];
  nextPlayerId: number;
  ratingsSource: string | null;
  rulesSource: string | null;
  simulationRulesSource: string | null;
  loadDepthCharts: (text: string) => void;
  loadFreeAgents: (text: string) => void;
  loadSchedule: (text: string) => void;
  loadRatings: (text: string) => void;
  loadRules: (text: string) => void;
  loadSimulationRules: (text: string) => void;
  simulateWeek: (week: number, mode: SimulationMode) => SimulationResult;
  signFreeAgent: (teamId: number, playerId: number) => TradeEvaluation;
  evaluateTrade: (proposal: TradeProposal) => TradeEvaluation;
  executeTrade: (proposal: TradeProposal) => TradeEvaluation;
  updateDepthChart: (teamId: number, entries: DepthChartEntry[]) => void;
  computeStandings: () => Standing[];
  getTeamRoster: (teamId: number) => Player[];
  getTeamStats: (teamId: number) => TeamStats;
};

function computeStandingsFromGames(games: GameSummary[], teams: Team[]): Standing[] {
  const records = new Map<number, Standing>();

  teams.forEach((team) => {
    records.set(team.id, {
      teamId: team.id,
      name: team.name,
      abbreviation: team.abbreviation,
      conference: team.conference,
      division: team.division,
      wins: 0,
      losses: 0,
      ties: 0,
    });
  });

  games
    .filter((game) => game.playedAt && game.homeScore !== null && game.awayScore !== null)
    .forEach((game) => {
      const homeRecord = records.get(game.homeTeamId);
      const awayRecord = records.get(game.awayTeamId);
      if (!homeRecord || !awayRecord) {
        return;
      }

      if (game.homeScore === game.awayScore) {
        homeRecord.ties += 1;
        awayRecord.ties += 1;
        return;
      }

      const homeWon = (game.homeScore ?? 0) > (game.awayScore ?? 0);
      if (homeWon) {
        homeRecord.wins += 1;
        awayRecord.losses += 1;
      } else {
        awayRecord.wins += 1;
        homeRecord.losses += 1;
      }
    });

  return Array.from(records.values()).sort((a, b) => {
    if (b.wins !== a.wins) {
      return b.wins - a.wins;
    }
    if (a.losses !== b.losses) {
      return a.losses - b.losses;
    }
    return a.teamId - b.teamId;
  });
}

function ratingForTeam(teamId: number, teams: Team[]): number {
  const team = teams.find((candidate) => candidate.id === teamId);
  return team?.rating ?? 75;
}

function buildBoxScore(
  game: GameSummary,
  players: Player[],
  teams: Team[],
  mode: SimulationMode
): BoxScore {
  const homeRating = ratingForTeam(game.homeTeamId, teams);
  const awayRating = ratingForTeam(game.awayTeamId, teams);
  const baseScore = 17;
  const homeScore = Math.max(
    10,
    Math.round(baseScore + (homeRating - awayRating) / 4 + (mode === "detailed" ? 3 : 1))
  );
  const awayScore = Math.max(
    10,
    Math.round(baseScore + (awayRating - homeRating) / 4 + (mode === "detailed" ? 2 : 0))
  );

  const yards = (rating: number, score: number) => 250 + Math.round(rating * 1.5 + score * 4);

  const homeYards = yards(homeRating, homeScore);
  const awayYards = yards(awayRating, awayScore);

  const teamPlayers = (teamId: number) => players.filter((player) => player.teamId === teamId);
  const pickPlayer = (teamId: number, slot: string) =>
    teamPlayers(teamId).find((player) => player.depthChartSlot === slot) ?? teamPlayers(teamId)[0];

  const homeQuarterback = pickPlayer(game.homeTeamId, "QB1");
  const awayQuarterback = pickPlayer(game.awayTeamId, "QB1");
  const homeRunner = pickPlayer(game.homeTeamId, "RB1");
  const awayRunner = pickPlayer(game.awayTeamId, "RB1");

  const keyPlayers = [
    homeQuarterback,
    homeRunner,
    awayQuarterback,
    awayRunner,
  ]
    .filter(Boolean)
    .map((player) => ({
      playerId: player!.id,
      name: player!.name,
      teamId: player!.teamId ?? 0,
      position: player!.position,
      statLine:
        player!.position === "QB"
          ? `${220 + player!.overall} pass yds · ${Math.max(1, Math.round(player!.overall / 20))} TD`
          : `${80 + player!.overall / 2} ${player!.position === "RB" ? "rush" : "rec"} yds · 1 TD`,
    }));

  return {
    gameId: game.id,
    week: game.week,
    homeTeam: {
      teamId: game.homeTeamId,
      name: game.homeTeamName,
      points: homeScore,
      yards: homeYards,
      turnovers: mode === "detailed" ? 1 : 2,
    },
    awayTeam: {
      teamId: game.awayTeamId,
      name: game.awayTeamName,
      points: awayScore,
      yards: awayYards,
      turnovers: mode === "detailed" ? 1 : 2,
    },
    keyPlayers,
  };
}

function buildPlayByPlay(game: GameSummary, boxScore: BoxScore): string[] {
  return [
    `Q1 10:35 – ${boxScore.homeTeam.name} opens with a methodical drive capped by a short score.`,
    `Q2 03:12 – ${boxScore.awayTeam.name} responds with a quick strike to their top receiver.`,
    `Q3 07:48 – ${boxScore.homeTeam.name} defense forces a turnover leading to points.`,
    `Q4 01:56 – ${boxScore.homeTeam.name} kneels out the win against ${boxScore.awayTeam.name}.`,
  ];
}

const useMockDataStore = create<MockDataState>((set, get) => ({
  teams: defaultTeams,
  players: defaultPlayers,
  freeAgents: defaultFreeAgents,
  games: defaultGames,
  boxScores: defaultBoxScores,
  nextPlayerId: 200,
  ratingsSource: null,
  rulesSource: null,
  simulationRulesSource: null,
  loadDepthCharts: (text: string) => {
    const assignments = parseDepthChartFile(text, get().teams);
    set((state) => {
      const updatedPlayers = state.players.map((player) => {
        const teamAssignments = assignments[player.teamId ?? -1];
        if (!teamAssignments) {
          return player;
        }
        const matchingEntry = teamAssignments.find((entry) =>
          entry.playerName && entry.playerName.toLowerCase() === player.name.toLowerCase()
        );
        if (!matchingEntry) {
          return player;
        }
        return { ...player, depthChartSlot: matchingEntry.slot };
      });
      return { players: updatedPlayers };
    });
  },
  loadFreeAgents: (text: string) => {
    const nextPlayerId = get().nextPlayerId;
    const freeAgents = parseFreeAgentFile(text, nextPlayerId);
    set({ freeAgents, nextPlayerId: nextPlayerId + freeAgents.length });
  },
  loadSchedule: (text: string) => {
    const teams = get().teams;
    // TODO: Replace this basic CSV ingestion with a multi-season scheduler that validates rules metadata.
    const parsed = parseScheduleCsv(text, teams);
    if (!parsed.length) {
      return;
    }
    const schedule: GameSummary[] = parsed.map((row, index) => {
      const home = teams.find((team) => team.name.toLowerCase() === row.homeTeamName.toLowerCase());
      const away = teams.find((team) => team.name.toLowerCase() === row.awayTeamName.toLowerCase());
      if (!home || !away) {
        throw new Error("Unable to match teams from schedule upload");
      }
      return {
        id: 100 + index,
        week: row.week,
        homeTeamId: home.id,
        awayTeamId: away.id,
        homeScore: null,
        awayScore: null,
        playedAt: null,
        homeTeamName: home.name,
        homeTeamAbbreviation: home.abbreviation,
        awayTeamName: away.name,
        awayTeamAbbreviation: away.abbreviation,
      };
    });
    set({ games: schedule, boxScores: [] });
  },
  loadRatings: (text: string) => {
    set({ ratingsSource: text });
  },
  loadRules: (text: string) => {
    set({ rulesSource: text });
  },
  loadSimulationRules: (text: string) => {
    set({ simulationRulesSource: text });
  },
  simulateWeek: (week: number, mode: SimulationMode) => {
    const state = get();
    const gamesToSimulate = state.games.filter((game) => game.week === week && !game.playedAt);
    if (!gamesToSimulate.length) {
      return {
        week,
        summaries: [],
        playByPlay: ["No unplayed matchups remain for this week."],
      };
    }

    const summaries = gamesToSimulate.map((game) => buildBoxScore(game, state.players, state.teams, mode));
    const playByPlay = summaries.flatMap((summary, index) =>
      buildPlayByPlay(gamesToSimulate[index], summary)
    );

    const updatedGames = state.games.map((game) => {
      const summary = summaries.find((item) => item.gameId === game.id);
      if (!summary) {
        return game;
      }
      return {
        ...game,
        homeScore: summary.homeTeam.points,
        awayScore: summary.awayTeam.points,
        playedAt: new Date().toISOString(),
      };
    });

    set({
      games: updatedGames,
      boxScores: [...state.boxScores, ...summaries],
    });

    return { week, summaries, playByPlay };
  },
  signFreeAgent: (teamId: number, playerId: number) => {
    // TODO: Expand salary + cap bookkeeping to incorporate bonuses and prorated structures from rule files.
    const state = get();
    const player = state.freeAgents.find((candidate) => candidate.id === playerId);
    if (!player) {
      return { success: false, message: "Player is no longer available." };
    }

    const team = state.teams.find((candidate) => candidate.id === teamId);
    if (!team) {
      return { success: false, message: "Team not found." };
    }

    const rosterCount = state.players.filter((candidate) => candidate.teamId === teamId).length;
    if (rosterCount >= 53) {
      return { success: false, message: "Roster limit reached." };
    }

    if (team.salarySpent + player.contractValue > team.salaryCap) {
      return { success: false, message: "Signing would exceed salary cap." };
    }

    set({
      freeAgents: state.freeAgents.filter((candidate) => candidate.id !== playerId),
      players: [
        ...state.players,
        { ...player, teamId, status: "active", depthChartSlot: `${player.position}2` },
      ],
      teams: state.teams.map((candidate) =>
        candidate.id === teamId
          ? { ...candidate, salarySpent: candidate.salarySpent + player.contractValue }
          : candidate
      ),
    });

    return { success: true, message: "Player signed to roster." };
  },
  evaluateTrade: (proposal: TradeProposal) => {
    const state = get();
    if (proposal.teamA === proposal.teamB) {
      return { success: false, message: "Teams must be different." };
    }
    if (!proposal.offer.length || !proposal.request.length) {
      return { success: false, message: "Both teams must include at least one asset." };
    }

    const teamA = state.teams.find((candidate) => candidate.id === proposal.teamA);
    const teamB = state.teams.find((candidate) => candidate.id === proposal.teamB);
    if (!teamA || !teamB) {
      return { success: false, message: "Both teams must be valid selections." };
    }

    if (proposal.offer.some((id) => proposal.request.includes(id))) {
      return { success: false, message: "Assets cannot appear on both sides of the trade." };
    }

    const offerPlayers = state.players.filter((player) => proposal.offer.includes(player.id));
    const requestPlayers = state.players.filter((player) => proposal.request.includes(player.id));

    if (!offerPlayers.length || !requestPlayers.length) {
      return { success: false, message: "Unable to match selected players." };
    }

    if (!offerPlayers.every((player) => player.teamId === proposal.teamA)) {
      return { success: false, message: "Offering assets must belong to the selected team." };
    }
    if (!requestPlayers.every((player) => player.teamId === proposal.teamB)) {
      return { success: false, message: "Requested assets must belong to the opposing team." };
    }

    const projectedPlayers = state.players.map((player) => {
      if (proposal.offer.includes(player.id)) {
        return { ...player, teamId: proposal.teamB };
      }
      if (proposal.request.includes(player.id)) {
        return { ...player, teamId: proposal.teamA };
      }
      return player;
    });

    const teamARoster = projectedPlayers.filter((player) => player.teamId === proposal.teamA);
    const teamBRoster = projectedPlayers.filter((player) => player.teamId === proposal.teamB);

    if (teamARoster.length > ROSTER_LIMIT || teamBRoster.length > ROSTER_LIMIT) {
      return { success: false, message: "Trade would exceed the roster limit for a team." };
    }

    for (const position of KEY_POSITIONS) {
      if (!teamARoster.some((player) => player.position === position)) {
        return { success: false, message: `Team ${teamA.name} must retain a ${position}.` };
      }
      if (!teamBRoster.some((player) => player.position === position)) {
        return { success: false, message: `Team ${teamB.name} must retain a ${position}.` };
      }
    }

    const offerValue = sumContractValue(offerPlayers);
    const requestValue = sumContractValue(requestPlayers);
    const teamASalary = teamA.salarySpent - offerValue + requestValue;
    const teamBSalary = teamB.salarySpent - requestValue + offerValue;
    if (teamASalary > teamA.salaryCap) {
      return { success: false, message: `Trade would exceed salary cap for ${teamA.name}.` };
    }
    if (teamBSalary > teamB.salaryCap) {
      return { success: false, message: `Trade would exceed salary cap for ${teamB.name}.` };
    }

    if (countEliteQuarterbacks(teamARoster) > 1) {
      return { success: false, message: `${teamA.name} cannot roster multiple elite quarterbacks.` };
    }
    if (countEliteQuarterbacks(teamBRoster) > 1) {
      return { success: false, message: `${teamB.name} cannot roster multiple elite quarterbacks.` };
    }

    return { success: true, message: "Proposal passes local validation." };
  },
  executeTrade: (proposal: TradeProposal) => {
    const state = get();
    const validation = get().evaluateTrade(proposal);
    if (!validation.success) {
      return validation;
    }

    const offerPlayers = state.players.filter((player) => proposal.offer.includes(player.id));
    const requestPlayers = state.players.filter((player) => proposal.request.includes(player.id));

    const updatedPlayers = state.players.map((player) => {
      if (proposal.offer.includes(player.id)) {
        return { ...player, teamId: proposal.teamB };
      }
      if (proposal.request.includes(player.id)) {
        return { ...player, teamId: proposal.teamA };
      }
      return player;
    });

    const updatedTeams = state.teams.map((team) => {
      if (team.id === proposal.teamA) {
        return {
          ...team,
          salarySpent: team.salarySpent - sumContractValue(offerPlayers) + sumContractValue(requestPlayers),
        };
      }
      if (team.id === proposal.teamB) {
        return {
          ...team,
          salarySpent: team.salarySpent - sumContractValue(requestPlayers) + sumContractValue(offerPlayers),
        };
      }
      return team;
    });

    set({ players: updatedPlayers, teams: updatedTeams });
    return { success: true, message: "Trade completed." };
  },
  updateDepthChart: (teamId: number, entries: DepthChartEntry[]) => {
    set((state) => ({
      players: state.players.map((player) => {
        if (player.teamId !== teamId) {
          return player;
        }
        const entry = entries.find((candidate) => candidate.playerId === player.id);
        if (!entry) {
          return player;
        }
        return { ...player, depthChartSlot: entry.slot };
      }),
    }));
  },
  computeStandings: () => computeStandingsFromGames(get().games, get().teams),
  getTeamRoster: (teamId: number) => get().players.filter((player) => player.teamId === teamId),
  getTeamStats: (teamId: number) => {
    const state = get();
    const relevant = state.boxScores.filter(
      (box) => box.homeTeam.teamId === teamId || box.awayTeam.teamId === teamId
    );
    if (!relevant.length) {
      return {
        teamId,
        totalPoints: 0,
        totalYards: 0,
        totalTurnovers: 0,
        gamesPlayed: 0,
        starters: [],
      };
    }

    const totals = relevant.reduce(
      (acc, box) => {
        const teamTotals =
          box.homeTeam.teamId === teamId ? box.homeTeam : (box.awayTeam as BoxScore["awayTeam"]);
        acc.points += teamTotals.points;
        acc.yards += teamTotals.yards;
        acc.turnovers += teamTotals.turnovers;
        return acc;
      },
      { points: 0, yards: 0, turnovers: 0 }
    );

    const starters = state.players
      .filter((player) => player.teamId === teamId && player.depthChartSlot?.endsWith("1"))
      .map((player) => ({
        playerId: player.id,
        name: player.name,
        teamId: teamId,
        position: player.position,
        statLine: `${player.overall} rating · leader`,
      }));

    return {
      teamId,
      totalPoints: totals.points,
      totalYards: totals.yards,
      totalTurnovers: totals.turnovers,
      gamesPlayed: relevant.length,
      starters,
    };
  },
}));

export { useMockDataStore };
