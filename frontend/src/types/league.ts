export type Team = {
  id: number;
  name: string;
  abbreviation: string;
  conference: string;
  division: string;
  rating: number;
  salaryCap: number;
  salarySpent: number;
};

export type Player = {
  id: number;
  name: string;
  position: string;
  overall: number;
  age: number;
  contractValue: number;
  contractYears: number;
  teamId: number | null;
  depthChartSlot: string | null;
  status: "active" | "free-agent" | "practice";
};

export type Game = {
  id: number;
  week: number;
  homeTeamId: number;
  awayTeamId: number;
  homeScore: number | null;
  awayScore: number | null;
  playedAt: string | null;
};

export type GameSummary = Game & {
  homeTeamName: string;
  homeTeamAbbreviation: string;
  awayTeamName: string;
  awayTeamAbbreviation: string;
};

export type Standing = {
  teamId: number;
  name: string;
  abbreviation: string;
  conference: string;
  division: string;
  wins: number;
  losses: number;
  ties: number;
  winPct: number;
};

export type TeamTotals = {
  teamId: number;
  points: number;
  yards: number;
  turnovers: number;
};

export type PlayerStatLine = {
  playerId: number;
  name: string;
  teamId: number;
  position: string;
  statLine: string;
};

export type InjuryReport = {
  playerId: number;
  name: string;
  teamId: number;
  teamName: string;
  position: string;
  status: string;
  description: string;
  expectedReturn: string;
};

export type BoxScore = {
  gameId: number;
  week: number;
  homeTeam: TeamTotals & { name: string };
  awayTeam: TeamTotals & { name: string };
  keyPlayers: PlayerStatLine[];
};

export type SimulationMode = "quick" | "detailed";

export type SimulationRequest = {
  week: number;
  mode: SimulationMode;
};

export type SimulationResult = {
  week: number;
  summaries: BoxScore[];
  playByPlay: string[];
};

export type WeeklyGameResult = {
  gameId: number;
  week: number;
  playedAt: string | null;
  homeTeam: {
    id: number;
    name: string;
    abbreviation: string;
    points: number | null;
  };
  awayTeam: {
    id: number;
    name: string;
    abbreviation: string;
    points: number | null;
  };
  passingLeader: PlayerStatLine | null;
  rushingLeader: PlayerStatLine | null;
  receivingLeader: PlayerStatLine | null;
  defensiveLeaders: PlayerStatLine[];
  injuries: InjuryReport[];
};

export type TradeProposal = {
  teamA: number;
  teamB: number;
  offer: number[];
  request: number[];
};

export type TradeProposalResult = {
  status: "accepted" | "rejected";
  message: string;
  offerValue?: number;
  requestValue?: number;
  valueDelta?: number;
};

export type TradeExecutionResult = TradeProposalResult & {
  teamA?: Record<string, unknown>;
  teamB?: Record<string, unknown>;
  teamA_sent?: Record<string, unknown>;
  teamA_received?: Record<string, unknown>;
  teamB_sent?: Record<string, unknown>;
  teamB_received?: Record<string, unknown>;
};

export type FreeAgentListing = {
  year: number;
  players: Player[];
};

export type FreeAgentSigningResult = {
  status: "signed" | "error";
  message: string;
  player?: Player;
};

export type DepthChartEntry = {
  slot: string;
  playerId: number | null;
  playerName?: string;
};

export type TeamStats = {
  teamId: number;
  totalPoints: number;
  totalYards: number;
  totalTurnovers: number;
  gamesPlayed: number;
  starters: PlayerStatLine[];
};

export type UploadKind =
  | "depthCharts"
  | "ratings"
  | "freeAgents2025"
  | "freeAgents2026"
  | "rules"
  | "simulationRules"
  | "schedule";
