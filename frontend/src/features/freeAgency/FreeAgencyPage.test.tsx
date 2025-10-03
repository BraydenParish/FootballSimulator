import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, it } from "vitest";
import { FreeAgencyPage } from "./FreeAgencyPage";
import { useMockDataStore, ROSTER_LIMIT } from "../../store/mockData";

const DEFAULT_TEAM_ID = 1;
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

function renderPage() {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <FreeAgencyPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("FreeAgencyPage", () => {
  beforeEach(() => {
    resetStore();
  });

  it("filters players by position", async () => {
    renderPage();
    const filter = await screen.findByLabelText(/position/i);
    const qbOption = await screen.findByRole("option", { name: /qb/i });
    await userEvent.selectOptions(filter, qbOption);
    const rows = await screen.findAllByRole("row");
    expect(rows.some((row) => row.textContent?.includes("QB"))).toBe(true);
  });

  it("prevents signings when the roster is full", async () => {
    useMockDataStore.setState((state) => {
      const existing = state.players.filter((player) => player.teamId === DEFAULT_TEAM_ID);
      const needed = Math.max(0, ROSTER_LIMIT - existing.length);
      if (!needed) {
        return state;
      }
      const extras = Array.from({ length: needed }, (_, index) => ({
        id: state.nextPlayerId + index,
        name: `Alpha Reserve ${index + 1}`,
        position: index % 2 === 0 ? "LB" : "CB",
        overall: 60,
        age: 24,
        contractValue: 1,
        contractYears: 1,
        teamId: DEFAULT_TEAM_ID,
        depthChartSlot: null,
        status: "active" as const,
      }));
      return {
        ...state,
        players: [...state.players, ...extras],
        nextPlayerId: state.nextPlayerId + extras.length,
      };
    });

    renderPage();
    const signButtons = await screen.findAllByRole("button", { name: /sign/i });
    await userEvent.click(signButtons[0]);
    await screen.findByText(/roster limit reached/i);
  });
});
