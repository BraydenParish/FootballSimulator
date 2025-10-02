import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, it } from "vitest";
import { TradeCenterPage } from "./TradeCenterPage";
import { useMockDataStore } from "../../store/mockData";

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
});
