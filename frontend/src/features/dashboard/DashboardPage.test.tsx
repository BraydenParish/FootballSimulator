import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";
import { DashboardPage } from "./DashboardPage";
import { ResultsPage } from "../results/ResultsPage";
import { leagueApi } from "../../api/client";

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
  it("runs a quick simulation and routes to the results page", async () => {
    const simulateSpy = vi.spyOn(leagueApi, "simulateWeek");
    renderDashboard();

    const simButton = await screen.findByRole("button", { name: /simulate week/i });
    await act(async () => {
      await userEvent.click(simButton);
    });

    const quickSimButton = await screen.findByRole("button", { name: /quick sim/i });
    await act(async () => {
      await userEvent.click(quickSimButton);
    });

    await waitFor(() => {
      expect(screen.getByText(/Quick sim complete/i)).toBeInTheDocument();
    });
  });
});
