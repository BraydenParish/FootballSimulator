import { beforeEach, describe, expect, it } from "vitest";
import { useMockDataStore } from "./mockData";
import { TradeProposal } from "../types/league";

const baseState = useMockDataStore.getState();

function resetStore() {
  useMockDataStore.setState(
    () => ({
      ...baseState,
      teams: baseState.teams.map((team) => ({ ...team })),
      players: baseState.players.map((player) => ({ ...player })),
      freeAgents: baseState.freeAgents.map((player) => ({ ...player })),
      games: baseState.games.map((game) => ({ ...game })),
      boxScores: baseState.boxScores.map((box) => ({
        ...box,
        homeTeam: { ...box.homeTeam },
        awayTeam: { ...box.awayTeam },
        keyPlayers: box.keyPlayers.map((player) => ({ ...player })),
      })),
    }),
    true
  );
}

describe("mockData store", () => {
  beforeEach(() => {
    resetStore();
  });

  it("computes standings with win percentages", () => {
    const standings = useMockDataStore.getState().computeStandings();
    expect(standings.length).toBeGreaterThan(0);
    expect(standings.every((entry) => typeof entry.winPct === "number")).toBe(true);
  });

  it("invariant: executeTrade preserves combined roster size", () => {
    const store = useMockDataStore.getState();
    const offerPlayer = store.players.find((player) => player.name === "Alpha Linebacker");
    const requestPlayer = store.players.find((player) => player.name === "Beta Linebacker");
    if (!offerPlayer || !requestPlayer) {
      throw new Error("Expected linebackers for the invariant test");
    }

    const proposal: TradeProposal = {
      teamA: offerPlayer.teamId ?? 1,
      teamB: requestPlayer.teamId ?? 2,
      offer: [offerPlayer.id],
      request: [requestPlayer.id],
    };

    const initial = useMockDataStore
      .getState()
      .players.filter((player) => player.teamId === proposal.teamA || player.teamId === proposal.teamB)
      .length;

    const result = store.executeTrade(proposal);
    expect(result.status).toBe("accepted");

    const final = useMockDataStore
      .getState()
      .players.filter((player) => player.teamId === proposal.teamA || player.teamId === proposal.teamB)
      .length;

    expect(final).toBe(initial);
  });
});
