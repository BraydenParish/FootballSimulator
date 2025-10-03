import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, it } from "vitest";
import { TradeCenterPage } from "./TradeCenterPage";
import { useMockDataStore, ROSTER_LIMIT } from "../../store/mockData";

const baseState = useMockDataStore.getState();
const DEFAULT_TEAM_B = 2;

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
        <TradeCenterPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("TradeCenterPage", () => {
  beforeEach(() => {
    resetStore();
  });

  it("requires both teams to provide assets", async () => {
    renderPage();
    const validateButton = await screen.findByRole("button", { name: /validate proposal/i });
    await userEvent.click(validateButton);
    await screen.findByText(/both teams must include at least one asset/i);
  });

  it("approves a balanced trade", async () => {
    renderPage();
    const offeringPlayer = await screen.findByLabelText("Alpha Linebacker");
    await userEvent.click(offeringPlayer);
    const requestingPlayer = await screen.findByLabelText("Beta Linebacker");
    await userEvent.click(requestingPlayer);
    const validateButton = await screen.findByRole("button", { name: /validate proposal/i });
    await userEvent.click(validateButton);
    await screen.findByText(/proposal passes local validation/i);
  });

  it("blocks trades that exceed salary cap", async () => {
    useMockDataStore.setState((state) => ({
      ...state,
      teams: state.teams.map((team) =>
        team.id === 2 ? { ...team, salaryCap: 150, salarySpent: 150 } : team
      ),
    }));

    renderPage();
    const offeringPlayer = await screen.findByLabelText("Alpha Linebacker");
    await userEvent.click(offeringPlayer);
    const requestingPlayer = await screen.findByLabelText("Beta Tight End");
    await userEvent.click(requestingPlayer);
    const validateButton = await screen.findByRole("button", { name: /validate proposal/i });
    await userEvent.click(validateButton);
    await screen.findByText(/trade would exceed salary cap for team beta/i);
  });

  it("blocks trades that overflow a roster", async () => {
    useMockDataStore.setState((state) => {
      const existing = state.players.filter((player) => player.teamId === DEFAULT_TEAM_B);
      const needed = Math.max(0, ROSTER_LIMIT - existing.length);
      if (!needed) {
        return state;
      }
      const extras = Array.from({ length: needed }, (_, index) => ({
        id: state.nextPlayerId + index,
        name: `Beta Reserve ${index + 1}`,
        position: index % 2 === 0 ? "LB" : "CB",
        overall: 60,
        age: 24,
        contractValue: 1,
        contractYears: 1,
        teamId: DEFAULT_TEAM_B,
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
    const offeringPlayer = await screen.findByLabelText("Alpha Linebacker");
    await userEvent.click(offeringPlayer);
    const secondOffer = await screen.findByLabelText("Alpha Corner");
    await userEvent.click(secondOffer);
    const requestingPlayer = await screen.findByLabelText("Beta Tight End");
    await userEvent.click(requestingPlayer);
    const validateButton = await screen.findByRole("button", { name: /validate proposal/i });
    await userEvent.click(validateButton);
    await screen.findByText(/Team Beta would exceed the roster limit/i);
  });
});
