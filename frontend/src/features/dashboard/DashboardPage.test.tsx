import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { DashboardPage } from "./DashboardPage";

function renderDashboard() {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("DashboardPage", () => {
  it("runs a quick simulation and displays the result banner", async () => {
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
