export type Team = {
  id: number;
  name: string;
  abbreviation: string;
  conference: string;
  division: string;
  rating?: number;
  salaryCap?: number;
  salarySpent?: number;
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

export type FreeAgentPool = {
  year: number;
  players: Player[];
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

export type TradeProposal = {
  teamA: number;
  teamB: number;
  offer: number[];
  request: number[];
};

export type TradeEvaluation = {
  success: boolean;
  message: string;
};

export type SignResult = {
  message: string;
  player: Player;
  team: Team;
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
