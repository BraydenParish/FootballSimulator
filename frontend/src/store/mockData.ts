import { create } from "zustand";
import {
  BoxScore,
  DepthChartEntry,
  FreeAgentSigningResult,
  GameSummary,
  InjuryReport,
  Player,
  SignResult,
  SimulationMode,
  SimulationResult,
  Standing,
  Team,
  TeamStats,
  TradeExecutionResult,
  TradeProposal,
  TradeProposalResult,
  WeeklyGameResult,
} from "../types/league";
import { parseDepthChartFile, parseFreeAgentFile, parseScheduleCsv } from "../utils/parsers";

export const ROSTER_LIMIT = 53;
export const ROSTER_MIN = 46;
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

function getSalaryCap(team: Team): number {
  return team.salaryCap ?? Number.POSITIVE_INFINITY;
}

function getSalarySpent(team: Team): number {
  return team.salarySpent ?? 0;
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

const defaultInjuryLog: Record<number, InjuryReport[]> = {
  1: [
    {
      playerId: 5,
      name: "Alpha Linebacker",
      teamId: 1,
      teamName: "Team Alpha",
      position: "LB",
      status: "Questionable",
      description: "Shoulder strain sustained late in the fourth quarter.",
      expectedReturn: "1 week",
    },
    {
      playerId: 18,
      name: "Gamma Corner",
      teamId: 3,
      teamName: "Team Gamma",
      position: "CB",
      status: "Out",
      description: "Ankle sprain – held out as precaution.",
      expectedReturn: "2 weeks",
    },
  ],
};

const DEFENSIVE_POSITIONS = ["LB", "CB", "S", "SS", "FS", "DE", "DT", "EDGE"] as const;

function cloneTeams(teams: Team[]): Team[] {
  return teams.map((team) => ({ ...team }));
}

function clonePlayers(players: Player[]): Player[] {
  return players.map((player) => ({ ...player }));
}

function cloneBoxScores(boxScores: BoxScore[]): BoxScore[] {
  return boxScores.map((box) => ({
    ...box,
    homeTeam: { ...box.homeTeam },
    awayTeam: { ...box.awayTeam },
    keyPlayers: box.keyPlayers.map((player) => ({ ...player })),
  }));
}

function createInitialState() {
  return {
    teams: cloneTeams(defaultTeams),
    players: clonePlayers(defaultPlayers),
    freeAgents: clonePlayers(defaultFreeAgents),
    games: defaultGames.map((game) => ({ ...game })),
    boxScores: cloneBoxScores(defaultBoxScores),
    injuryLog: { ...defaultInjuryLog },
    nextPlayerId: Math.max(...defaultPlayers.map((player) => player.id), 0) + 100,
    ratingsSource: null as string | null,
    rulesSource: null as string | null,
    simulationRulesSource: null as string | null,
  };
}

type MockDataState = {
  teams: Team[];
  players: Player[];
  freeAgents: Player[];
  games: GameSummary[];
  boxScores: BoxScore[];
  injuryLog: Record<number, InjuryReport[]>;
  nextPlayerId: number;
  ratingsSource: string | null;
  rulesSource: string | null;
  simulationRulesSource: string | null;
  reset: () => void;
  loadDepthCharts: (text: string) => void;
  loadFreeAgents: (text: string) => void;
  loadSchedule: (text: string) => void;
  loadRatings: (text: string) => void;
  loadRules: (text: string) => void;
  loadSimulationRules: (text: string) => void;
  simulateWeek: (week: number, mode: SimulationMode) => SimulationResult;
  signFreeAgent: (teamId: number, playerId: number) => SignResult;
  evaluateTrade: (proposal: TradeProposal) => TradeEvaluation;
  executeTrade: (proposal: TradeProposal) => TradeEvaluation;
  updateDepthChart: (teamId: number, entries: DepthChartEntry[]) => void;
  computeStandings: () => Standing[];
  getTeamRoster: (teamId: number) => Player[];
  getTeamStats: (teamId: number) => TeamStats;
  getWeekResults: (week: number) => WeeklyGameResult[];
  getLatestCompletedWeek: () => number | null;
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

  const standings = Array.from(records.values());
  standings.forEach((entry) => {
    const gamesPlayed = entry.wins + entry.losses + entry.ties;
    entry.winPct = gamesPlayed ? Number((entry.wins / gamesPlayed).toFixed(3)) : 0;
  });

  return standings.sort((a, b) => {
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

function playerToStatLine(player: Player, note: string): BoxScore["keyPlayers"][number] {
  return {
    playerId: player.id,
    name: player.name,
    teamId: player.teamId ?? 0,
    position: player.position,
    statLine: note,
  };
}

function computeWeeklyLeaders(
  game: GameSummary,
  boxScore: BoxScore | undefined,
  players: Player[]
): {
  passingLeader: BoxScore["keyPlayers"][number] | null;
  rushingLeader: BoxScore["keyPlayers"][number] | null;
  receivingLeader: BoxScore["keyPlayers"][number] | null;
  defensiveLeaders: BoxScore["keyPlayers"][number][];
} {
  const statLines = boxScore?.keyPlayers ?? [];
  const participants = players.filter(
    (player) => player.teamId === game.homeTeamId || player.teamId === game.awayTeamId
  );

  const pickStat = (positions: string[]): BoxScore["keyPlayers"][number] | undefined =>
    statLines.find((line) => positions.includes(line.position));

  const fallback = (slot: string, predicate: (player: Player) => boolean, descriptor: string) => {
    const fromSlot = participants.find((player) => player.depthChartSlot === slot);
    const selected = fromSlot ?? participants.find(predicate);
    return selected ? playerToStatLine(selected, descriptor) : null;
  };

  const qbOverall = participants.find((player) => player.position === "QB")?.overall ?? 70;
  const rbOverall = participants.find((player) => player.position === "RB")?.overall ?? 65;
  const wrOverall = participants.find((player) => player.position === "WR")?.overall ?? 68;

  const passingLeader =
    pickStat(["QB"]) ?? fallback("QB1", (player) => player.position === "QB", `${220 + qbOverall} pass yds · 2 TD`);

  const rushingLeader =
    pickStat(["RB"]) ?? fallback("RB1", (player) => player.position === "RB", `${90 + rbOverall} rush yds · TD`);

  const receivingLeader =
    pickStat(["WR", "TE"]) ??
    fallback(
      "WR1",
      (player) => player.position === "WR" || player.position === "TE",
      `6 rec · ${wrOverall + 40} yds`
    );

  const defensiveLeadersFromStats = statLines.filter((line) =>
    DEFENSIVE_POSITIONS.includes(line.position as (typeof DEFENSIVE_POSITIONS)[number])
  );

  const defensiveFallback = participants
    .filter((player) => DEFENSIVE_POSITIONS.includes(player.position as any))
    .sort((a, b) => b.overall - a.overall)
    .slice(0, 2)
    .map((player) => playerToStatLine(player, `${player.overall} OVR · defensive anchor`));

  const defensiveLeaders = defensiveLeadersFromStats.length ? defensiveLeadersFromStats : defensiveFallback;

  return {
    passingLeader: passingLeader ?? null,
    rushingLeader: rushingLeader ?? null,
    receivingLeader: receivingLeader ?? null,
    defensiveLeaders,
  };
}

function buildInjurySummary(summary: BoxScore): InjuryReport | null {
  const candidate = summary.keyPlayers.find((player) => player.position !== "QB") ?? summary.keyPlayers[0];
  if (!candidate) {
    return null;
  }
  const teamName =
    candidate.teamId === summary.homeTeam.teamId ? summary.homeTeam.name : summary.awayTeam.name;
  return {
    playerId: candidate.playerId,
    name: candidate.name,
    teamId: candidate.teamId,
    teamName,
    position: candidate.position,
    status: "Questionable",
    description: "Day-to-day after taking a hit.",
    expectedReturn: "1 week",
  };
}

const useMockDataStore = create<MockDataState>((set, get) => ({
  ...createInitialState(),
  reset: () => set(createInitialState()),
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
    set({ games: schedule, boxScores: [], injuryLog: {} });
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

    const simulatedInjuries = summaries
      .map((summary) => buildInjurySummary(summary))
      .filter((injury): injury is InjuryReport => Boolean(injury));

    const existingWeekInjuries = state.injuryLog[week] ?? [];
    const updatedInjuryLog = simulatedInjuries.length
      ? { ...state.injuryLog, [week]: [...existingWeekInjuries, ...simulatedInjuries] }
      : state.injuryLog;

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
      injuryLog: updatedInjuryLog,
    });

    return { week, summaries, playByPlay };
  },
  signFreeAgent: (teamId: number, playerId: number) => {
    // TODO: Expand salary + cap bookkeeping to incorporate bonuses and prorated structures from rule files.
    const state = get();
    const player = state.freeAgents.find((candidate) => candidate.id === playerId);
    if (!player) {
      throw new Error("Player is no longer available.");
    }

    const team = state.teams.find((candidate) => candidate.id === teamId);
    if (!team) {
      throw new Error("Team not found.");
    }

    const rosterCount = state.players.filter((candidate) => candidate.teamId === teamId).length;
    if (rosterCount >= 53) {
      throw new Error("Roster limit reached.");
    }

    const currentSalarySpent = getSalarySpent(team);
    const salaryCap = getSalaryCap(team);

    if (currentSalarySpent + player.contractValue > salaryCap) {
      throw new Error("Signing would exceed salary cap.");
    }

    const updatedPlayer: Player = {
      ...player,
      teamId,
      status: "active",
      depthChartSlot: `${player.position}2`,
    };

    const updatedTeam = {
      ...team,
      salarySpent: currentSalarySpent + player.contractValue,
    };

    set({
      freeAgents: state.freeAgents.filter((candidate) => candidate.id !== playerId),
      players: [...state.players, updatedPlayer],
      teams: state.teams.map((candidate) =>
        candidate.id === teamId ? updatedTeam : candidate
      ),
    });

    return {
      message: `Signed ${player.name} to the roster`,
      player: updatedPlayer,
      team: updatedTeam,
    };
  },
  evaluateTrade: (proposal: TradeProposal) => {
    const state = get();
    if (proposal.teamA === proposal.teamB) {
      return { status: "rejected", message: "Teams must be different." };
    }
    if (!proposal.offer.length || !proposal.request.length) {
      return { status: "rejected", message: "Both teams must include at least one asset." };
    }

    const teamA = state.teams.find((candidate) => candidate.id === proposal.teamA);
    const teamB = state.teams.find((candidate) => candidate.id === proposal.teamB);
    if (!teamA || !teamB) {
      return { status: "rejected", message: "Both teams must be valid selections." };
    }

    if (proposal.offer.some((id) => proposal.request.includes(id))) {
      return { status: "rejected", message: "Assets cannot appear on both sides of the trade." };
    }

    const offerPlayers = state.players.filter((player) => proposal.offer.includes(player.id));
    const requestPlayers = state.players.filter((player) => proposal.request.includes(player.id));

    if (!offerPlayers.length || !requestPlayers.length) {
      return { status: "rejected", message: "Unable to match selected players." };
    }

    if (!offerPlayers.every((player) => player.teamId === proposal.teamA)) {
      return { status: "rejected", message: "Offering assets must belong to the selected team." };
    }
    if (!requestPlayers.every((player) => player.teamId === proposal.teamB)) {
      return { status: "rejected", message: "Requested assets must belong to the opposing team." };
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

    const teamATotal = state.players.filter((player) => player.teamId === proposal.teamA).length;
    const teamBTotal = state.players.filter((player) => player.teamId === proposal.teamB).length;
    const teamARoster = projectedPlayers.filter((player) => player.teamId === proposal.teamA);
    const teamBRoster = projectedPlayers.filter((player) => player.teamId === proposal.teamB);

    if (teamARoster.length > ROSTER_LIMIT && teamARoster.length > teamATotal) {
      return { success: false, message: `${teamA.name} would exceed the roster limit.` };
    }
    if (teamBRoster.length > ROSTER_LIMIT && teamBRoster.length > teamBTotal) {
      return { success: false, message: `${teamB.name} would exceed the roster limit.` };
    }
    if (teamARoster.length < ROSTER_MIN && teamARoster.length < teamATotal) {
      return {
        success: false,
        message: `${teamA.name} must retain at least ${ROSTER_MIN} players.`,
      };
    }
    if (teamBRoster.length < ROSTER_MIN && teamBRoster.length < teamBTotal) {
      return {
        success: false,
        message: `${teamB.name} must retain at least ${ROSTER_MIN} players.`,
      };
    }

    for (const position of KEY_POSITIONS) {
      if (!teamARoster.some((player) => player.position === position)) {
        return { status: "rejected", message: `Team ${teamA.name} must retain a ${position}.` };
      }
      if (!teamBRoster.some((player) => player.position === position)) {
        return { status: "rejected", message: `Team ${teamB.name} must retain a ${position}.` };
      }
    }

    const offerValue = sumContractValue(offerPlayers);
    const requestValue = sumContractValue(requestPlayers);
    const teamASalary = getSalarySpent(teamA) - offerValue + requestValue;
    const teamBSalary = getSalarySpent(teamB) - requestValue + offerValue;
    if (teamASalary > getSalaryCap(teamA)) {
      return { success: false, message: `Trade would exceed salary cap for ${teamA.name}.` };
    }
    if (teamBSalary > getSalaryCap(teamB)) {
      return { success: false, message: `Trade would exceed salary cap for ${teamB.name}.` };
    }

    if (countEliteQuarterbacks(teamARoster) > 1) {
      return { status: "rejected", message: `${teamA.name} cannot roster multiple elite quarterbacks.` };
    }
    if (countEliteQuarterbacks(teamBRoster) > 1) {
      return { status: "rejected", message: `${teamB.name} cannot roster multiple elite quarterbacks.` };
    }

    return {
      status: "accepted",
      message: "Proposal passes mock validation.",
      offerValue,
      requestValue,
      valueDelta: requestValue - offerValue,
    };
  },
  executeTrade: (proposal: TradeProposal) => {
    const state = get();
    const validation = get().evaluateTrade(proposal);
    if (validation.status !== "accepted") {
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
          salarySpent:
            getSalarySpent(team) - sumContractValue(offerPlayers) + sumContractValue(requestPlayers),
        };
      }
      if (team.id === proposal.teamB) {
        return {
          ...team,
          salarySpent:
            getSalarySpent(team) - sumContractValue(requestPlayers) + sumContractValue(offerPlayers),
        };
      }
      return team;
    });

    set({ players: updatedPlayers, teams: updatedTeams });
    return {
      status: "accepted",
      message: "Trade completed.",
      offerValue: validation.offerValue,
      requestValue: validation.requestValue,
      valueDelta: validation.valueDelta,
    };
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
  getWeekResults: (week: number) => {
    const state = get();
    const games = state.games.filter((game) => game.week === week);
    if (!games.length) {
      return [];
    }
    const injuriesByWeek = state.injuryLog[week] ?? [];
    return games.map((game) => {
      const boxScore = state.boxScores.find((box) => box.gameId === game.id);
      const leaders = computeWeeklyLeaders(game, boxScore, state.players);
      const injuries = injuriesByWeek.filter(
        (injury) => injury.teamId === game.homeTeamId || injury.teamId === game.awayTeamId
      );
      return {
        gameId: game.id,
        week: game.week,
        playedAt: game.playedAt,
        homeTeam: {
          id: game.homeTeamId,
          name: game.homeTeamName,
          abbreviation: game.homeTeamAbbreviation,
          points: boxScore?.homeTeam.points ?? game.homeScore,
        },
        awayTeam: {
          id: game.awayTeamId,
          name: game.awayTeamName,
          abbreviation: game.awayTeamAbbreviation,
          points: boxScore?.awayTeam.points ?? game.awayScore,
        },
        passingLeader: leaders.passingLeader,
        rushingLeader: leaders.rushingLeader,
        receivingLeader: leaders.receivingLeader,
        defensiveLeaders: leaders.defensiveLeaders,
        injuries,
      } satisfies WeeklyGameResult;
    });
  },
  getLatestCompletedWeek: () => {
    const playedWeeks = get()
      .games.filter((game) => Boolean(game.playedAt))
      .map((game) => game.week);
    if (!playedWeeks.length) {
      return null;
    }
    return Math.max(...playedWeeks);
  },
}));

export { useMockDataStore };
