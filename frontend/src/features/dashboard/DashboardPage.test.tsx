import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import type { NavigateFunction } from "react-router-dom";
import { vi } from "vitest";
import { DashboardPage } from "./DashboardPage";
import { ResultsPage } from "../results/ResultsPage";
import { leagueApi } from "../../api/client";

let customNavigate: NavigateFunction | null = null;

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual<typeof import("react-router-dom")>("react-router-dom");
  const actualUseNavigate = actual.useNavigate;
  return {
    ...actual,
    useNavigate: () => customNavigate ?? actualUseNavigate(),
  };
});

function renderDashboard() {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/"]}>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/results/:week" element={<ResultsPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("DashboardPage", () => {
  it("runs a simulation and routes to the results page", async () => {
    const simulateSpy = vi.spyOn(leagueApi, "simulateWeek").mockResolvedValue({
      week: 5,
      playByPlay: ["Play"],
      summaries: [
        {
          gameId: 1,
          week: 5,
          homeTeam: { teamId: 1, points: 21, yards: 320, turnovers: 1, name: "Alpha" },
          awayTeam: { teamId: 2, points: 17, yards: 280, turnovers: 2, name: "Beta" },
          keyPlayers: [],
        },
      ],
    });

    renderDashboard();

    const simButton = await screen.findByRole("button", { name: /simulate week/i });
    await act(async () => {
      await userEvent.click(simButton);
    });

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Week 5 results/i })).toBeInTheDocument();
    });

    simulateSpy.mockRestore();
  });

  it("shows the latest results card when a simulation completes", async () => {
    const navigateMock = vi.fn();
    customNavigate = navigateMock;

    const simulateSpy = vi.spyOn(leagueApi, "simulateWeek").mockResolvedValue({
      week: 5,
      playByPlay: ["Play"],
      summaries: [
        {
          gameId: 1,
          week: 5,
          homeTeam: { teamId: 1, points: 21, yards: 320, turnovers: 1, name: "Alpha" },
          awayTeam: { teamId: 2, points: 17, yards: 280, turnovers: 2, name: "Beta" },
          keyPlayers: [],
        },
      ],
    });

    renderDashboard();

    const simButton = await screen.findByRole("button", { name: /simulate week/i });
    await act(async () => {
      await userEvent.click(simButton);
    });

    expect(await screen.findByText(/Week 5 Results/i)).toBeInTheDocument();
    expect(navigateMock).toHaveBeenCalledWith("/results/5", { state: { highlight: 1 } });

    simulateSpy.mockRestore();
    customNavigate = null;
  });
});
