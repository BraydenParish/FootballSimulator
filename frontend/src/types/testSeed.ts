import { InjuryReport, Player, Team } from "./league";

export type TestSeedSchedule = {
  id?: number;
  week: number;
  homeTeamId: number;
  awayTeamId: number;
  homeScore?: number | null;
  awayScore?: number | null;
  playedAt?: string | null;
};

export type TestSeed = {
  seasonYear?: number;
  teams: Team[];
  players: Player[];
  freeAgents: Player[];
  schedule: TestSeedSchedule[];
  injuryLog?: Record<number, InjuryReport[]>;
};
