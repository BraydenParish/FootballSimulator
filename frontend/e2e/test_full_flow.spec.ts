import { test, expect } from "@playwright/test";
import seed from "./test_seed.json";

test.beforeEach(async ({ page }) => {
  page.on("console", (msg) => {
    console.log(`[browser] ${msg.type()}: ${msg.text()}`);
  });
  await page.addInitScript((initialSeed) => {
    window.__E2E_SEED__ = initialSeed;
  }, seed);
});

test("user can complete the GM loop via mock backend", async ({ page }) => {
  await page.goto("/", { waitUntil: "networkidle" });

  await expect(page.getByRole("heading", { name: "League Operations Console" })).toBeVisible();

  await page.getByRole("button", { name: /Simulate Week/i }).click();
  await expect(page).toHaveURL(/\/results\/1$/);
  await expect(page.getByRole("heading", { name: /Week 1 results/i })).toBeVisible();
  const sharksMatchup = page
    .getByTestId("game-card")
    .filter({ hasText: /Metro Sharks/i, has: page.getByText(/Desert Scorpions/i) });
  await expect(sharksMatchup).toBeVisible();

  await page.getByRole("link", { name: "Free Agency" }).click();
  await expect(page.getByRole("heading", { name: "Free agency center" })).toBeVisible();
  const rocketRow = page.getByRole("row", { name: /Ricky Rocket/ });
  await expect(rocketRow).toBeVisible();
  await rocketRow.getByRole("button", { name: "Sign" }).click();
  await expect(page.getByText("Player signed to roster.")).toBeVisible();
  await expect(page.getByRole("row", { name: /Ricky Rocket/ })).toHaveCount(0);

  await page.getByRole("link", { name: "Depth Chart" }).click();
  await expect(page.getByRole("heading", { name: "Depth chart management" })).toBeVisible();
  const rocketDepthRow = page.getByRole("row", { name: /Ricky Rocket/ });
  await rocketDepthRow.getByRole("combobox").selectOption("RB1");
  await page.getByRole("button", { name: "Save Depth Chart" }).click();
  await expect(page.getByText("Depth chart saved.")).toBeVisible();

  await page.getByRole("link", { name: "Trade Center" }).click();
  await expect(page.getByRole("heading", { name: "Trade center" })).toBeVisible();
  await page.getByRole("checkbox", { name: "Darius Dash" }).check();
  await page.getByRole("checkbox", { name: "Trent Talon" }).check();
  await page.getByRole("button", { name: "Validate Proposal" }).click();
  await expect(page.getByText(/Proposal passes mock validation/i)).toBeVisible();
  await page.getByRole("button", { name: "Execute Trade" }).click();
  await expect(page.getByText("Trade completed.")).toBeVisible();

  await page.getByRole("link", { name: "Depth Chart" }).click();
  await expect(page.getByRole("row", { name: /Trent Talon/ })).toBeVisible();
  await page.getByLabel("Team").selectOption("2");
  await expect(page.getByRole("row", { name: /Darius Dash/ })).toBeVisible();

  await page.getByRole("link", { name: "Dashboard" }).click();
  await page.getByRole("button", { name: /Simulate Week/i }).click();
  await expect(page).toHaveURL(/\/results\/2$/);
  await expect(page.getByRole("heading", { name: /Week 2 results/i })).toBeVisible();

  await page.getByRole("link", { name: "Depth Chart" }).click();
  await expect(page.getByRole("heading", { name: "Depth chart management" })).toBeVisible();
  const rocketStarter = page.getByRole("row", { name: /Ricky Rocket/ });
  await expect(rocketStarter.getByRole("combobox")).toHaveValue("RB1");

  await page.getByRole("link", { name: "Standings" }).click();
  await expect(page.getByRole("heading", { name: "Division standings" })).toBeVisible();
  const sharksRow = page.getByRole("row", { name: /Metro Sharks/ });
  const sharkCells = sharksRow.getByRole("cell");
  await expect(sharkCells.nth(1)).toHaveText("2");
  await expect(sharkCells.nth(2)).toHaveText("0");
  await expect(sharkCells.nth(4)).toHaveText("1.000");
});
