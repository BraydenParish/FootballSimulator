import { DepthChartEntry, Player, Team } from "../types/league";

/**
 * Parses a depth chart file where each non-empty line follows the format:
 * `Team Name,Position Slot,Player Name`.
 * Lines that do not match the three column structure are ignored.
 *
 * @param text - Raw file contents uploaded by the user.
 * @param teams - Teams that exist in the mock data set. The parser will try to
 *   match team names case-insensitively. When a team cannot be matched the line
 *   is skipped to avoid polluting the store with partial data.
 * @returns Depth chart assignments keyed by team id.
 */
export function parseDepthChartFile(
  text: string,
  teams: Team[]
): Record<number, DepthChartEntry[]> {
  const byTeam: Record<number, DepthChartEntry[]> = {};
  const teamNameToId = new Map<string, number>();
  teams.forEach((team) => teamNameToId.set(team.name.toLowerCase(), team.id));

  text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .forEach((line) => {
      const [teamName, slot, playerName] = line.split(/,|\|/).map((part) => part.trim());
      if (!teamName || !slot || !playerName) {
        return;
      }

      const teamId = teamNameToId.get(teamName.toLowerCase());
      if (!teamId) {
        return;
      }

      const entries = byTeam[teamId] ?? [];
      entries.push({ slot: slot.toUpperCase(), playerId: null, playerName });
      byTeam[teamId] = entries;
    });

  return byTeam;
}

/**
 * Parses a free agent list where each row contains `Player Name,Position,Rating`.
 * Additional columns are ignored so the parser can accommodate richer datasets
 * without code changes.
 *
 * @param text - Raw file contents uploaded by the user.
 * @param nextPlayerId - Sequence start for newly ingested players.
 */
export function parseFreeAgentFile(text: string, nextPlayerId: number): Player[] {
  const freeAgents: Player[] = [];

  text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .forEach((line, index) => {
      const [name, position, rating] = line.split(/,|\|/).map((part) => part.trim());
      if (!name || !position) {
        return;
      }
      const parsedRating = Number.parseInt(rating ?? "70", 10) || 70;

      freeAgents.push({
        id: nextPlayerId + index,
        name,
        position: position.toUpperCase(),
        overall: parsedRating,
        age: 26,
        contractValue: 4,
        contractYears: 1,
        teamId: null,
        depthChartSlot: null,
        status: "free-agent",
      });
    });

  return freeAgents;
}

/**
 * Parses a CSV schedule shaped as `week,home,away` and returns tuples matching
 * team ids. When a team cannot be matched the matchup is ignored.
 */
export function parseScheduleCsv(text: string, teams: Team[]): Array<{
  week: number;
  homeTeamName: string;
  awayTeamName: string;
}> {
  const teamNameToId = new Set(teams.map((team) => team.name.toLowerCase()));

  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith("#"))
    .map((line) => line.split(/,|\|/).map((part) => part.trim()))
    .filter(([week, home, away]) => week && home && away)
    .filter(([, home, away]) =>
      teamNameToId.has(home.toLowerCase()) && teamNameToId.has(away.toLowerCase())
    )
    .map(([week, homeTeamName, awayTeamName]) => ({
      week: Number.parseInt(week, 10) || 1,
      homeTeamName,
      awayTeamName,
    }));
}
