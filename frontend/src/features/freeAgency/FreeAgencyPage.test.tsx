import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { FreeAgencyPage } from "./FreeAgencyPage";

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
  it("filters players by position", async () => {
    renderPage();
    const filter = await screen.findByLabelText(/position/i);
    const qbOption = await screen.findByRole("option", { name: /qb/i });
    await userEvent.selectOptions(filter, qbOption);
    const rows = await screen.findAllByRole("row");
    expect(rows.some((row) => row.textContent?.includes("QB"))).toBe(true);
  });
});
