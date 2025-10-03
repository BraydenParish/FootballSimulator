import { beforeEach, describe, expect, it, vi } from "vitest";
import userEvent from "@testing-library/user-event";
import { act, screen, waitFor, within } from "@testing-library/react";
import App from "../../App";
import { leagueApi } from "../../api/client";
import { renderWithProviders } from "../../test/testUtils";
import { useMockDataStore } from "../../store/mockData";

const resetStore = () => {
  act(() => {
    useMockDataStore.getState().reset();
  });
};

describe("NFL GM simulator app flows", () => {
  beforeEach(() => {
    resetStore();
  });

  it("simulates a week and navigates to results", async () => {
    const simulateSpy = vi.spyOn(leagueApi, "simulateWeek");
    const user = userEvent.setup();
    renderWithProviders(<App />);

    const simulateButton = await screen.findByRole("button", { name: /simulate week/i });
    await user.click(simulateButton);

    await waitFor(() => expect(simulateSpy).toHaveBeenCalledTimes(1));
    expect(await screen.findByRole("heading", { name: /week \d+ results/i })).toBeInTheDocument();
    expect(await screen.findByText(/Team Alpha/i)).toBeInTheDocument();

    simulateSpy.mockRestore();
  });

  it("signs a free agent and removes them from the market", async () => {
    const user = userEvent.setup();
    renderWithProviders(<App />, { routerProps: { initialEntries: ["/free-agency"] } });

    const freeAgentRow = (await screen.findByText("Free Agent Quarterback")).closest("tr");
    if (!freeAgentRow) {
      throw new Error("Unable to locate free agent row");
    }
    const signButton = within(freeAgentRow).getByRole("button", { name: /sign/i });
    await user.click(signButton);

    expect(await screen.findByText(/Player signed to roster/i)).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByText(/Free Agent Quarterback/i)).not.toBeInTheDocument());
  });

  it("updates the depth chart and persists the new order", async () => {
    const user = userEvent.setup();
    renderWithProviders(<App />, { routerProps: { initialEntries: ["/depth-chart"] } });

    const qbCell = await screen.findByText("Alpha Quarterback");
    const qbRow = qbCell.closest("tr");
    if (!qbRow) {
      throw new Error("Unable to locate quarterback row");
    }
    const qbSelect = within(qbRow).getByRole("combobox");
    await user.selectOptions(qbSelect, "QB2");

    await user.click(screen.getByRole("button", { name: /save depth chart/i }));

    expect(await screen.findByText(/Depth chart saved/i)).toBeInTheDocument();
    await waitFor(() => {
      const player = useMockDataStore.getState().players.find((p) => p.id === 1);
      expect(player?.depthChartSlot).toBe("QB2");
    });
  });

  it("validates and executes a trade offer", async () => {
    const user = userEvent.setup();
    renderWithProviders(<App />, { routerProps: { initialEntries: ["/trade-center"] } });

    const offeringSelect = (await screen.findByLabelText(/Offering team/i)) as HTMLSelectElement;
    const receivingSelect = screen.getByLabelText(/Receiving team/i) as HTMLSelectElement;

    await waitFor(() => {
      expect(offeringSelect.querySelectorAll("option").length).toBeGreaterThan(0);
    });
    const getOption = (select: HTMLSelectElement, text: string) => {
      const option = Array.from(select.querySelectorAll("option")).find((node) =>
        node.textContent?.toLowerCase().includes(text.toLowerCase())
      );
      if (!option) {
        throw new Error(`Option ${text} not found`);
      }
      return option as HTMLOptionElement;
    };

    await user.selectOptions(offeringSelect, getOption(offeringSelect, "Team Alpha"));
    await user.selectOptions(receivingSelect, getOption(receivingSelect, "Team Alpha"));
    await user.click(screen.getByRole("button", { name: /validate proposal/i }));
    expect(await screen.findByText(/Teams must be different/i)).toBeInTheDocument();

    await user.selectOptions(receivingSelect, getOption(receivingSelect, "Team Beta"));
    await user.click(screen.getByLabelText(/Alpha Quarterback/i));
    await user.click(screen.getByLabelText(/Beta Quarterback/i));
    await user.click(screen.getByRole("button", { name: /validate proposal/i }));
    expect(await screen.findByText(/Proposal passes mock validation/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /execute trade/i }));
    expect(await screen.findByText(/Trade completed/i)).toBeInTheDocument();
  });

  it("shows updated standings after games are simulated", async () => {
    const user = userEvent.setup();
    renderWithProviders(<App />);

    await user.click(await screen.findByRole("button", { name: /simulate week/i }));
    await waitFor(() => expect(screen.getByRole("heading", { name: /results/i })).toBeInTheDocument());

    await user.click(screen.getByRole("link", { name: /standings/i }));
    expect(await screen.findByRole("heading", { name: /division standings/i })).toBeInTheDocument();
    expect(
      await screen.findByText(/each table highlights the current division leader based on backend win percentage data/i)
    ).toBeInTheDocument();
    const rows = await screen.findAllByRole("row");
    expect(rows.length).toBeGreaterThan(1);
    const winColumns = await screen.findAllByText(/Win %/i);
    expect(winColumns.length).toBeGreaterThan(0);
  });
});
