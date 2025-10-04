import { test, expect } from '@playwright/test';

test.describe('GM Full Flow', () => {
  test('simulate → free agency → trade → standings', async ({ page }) => {
    await page.goto('/');

    await page.getByRole('button', { name: 'Simulate Week' }).click();
    await page.getByRole('button', { name: 'Quick Sim' }).click();
    await expect(page.locator('[data-test=simulation-results] h2')).toContainText('Week 1 Results');
    await expect(page.locator('[data-test=game-result]').first()).toBeVisible();

    await page.getByRole('link', { name: 'Free Agency' }).click();
    const freeAgents = page.locator('[data-test=free-agent-row]');
    await expect(freeAgents.first()).toBeVisible();

    await freeAgents
      .first()
      .locator('button:has-text("Sign")')
      .click();
    await expect(page.locator('[data-test=depth-chart]')).toContainText('Signed');

    await page.getByRole('link', { name: 'Trade Center' }).click();
    await page.locator('button:has-text("Propose Trade")').click();
    await expect(page.locator('[data-test=trade-result]')).toContainText('Trade Accepted');

    await page.getByRole('link', { name: 'Standings' }).click();
    await expect(page.locator('[data-test=standings-row]').first()).toBeVisible();
  });
});
