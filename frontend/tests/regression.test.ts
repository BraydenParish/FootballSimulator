/**
 * Regression test placeholders for previously reported bugs.
 *
 * Switch each skipped test to an active assertion once the
 * corresponding issue is resolved so future regressions are caught.
 */
import { describe, test } from "vitest";

describe.skip("Roster overflow guards", () => {
  test("should reject signings that exceed 53-man roster limit", () => {
    throw new Error("Pending roster limit enforcement fix.");
  });
});

describe.skip("Impossible stat lines", () => {
  test("should never surface negative rushing yards in weekly summaries", () => {
    throw new Error("Awaiting stat normalization patch.");
  });
});

describe.skip("Trade validation", () => {
  test("should prevent trades that break salary cap floor", () => {
    throw new Error("Pending cap validation improvements.");
  });
});
