# AGENTS.md — Code Review, Testing, and Hardening Playbook

## Repository Guidelines (kept from existing file)
- Follow tests-first workflow: add or update tests before implementation whenever feasible.
- Keep diffs minimal and localized; avoid formatting unrelated lines.
- Do not introduce new dependencies unless absolutely necessary.
- Provide documentation citations for nontrivial API or framework usage.
- List maintained invariants in change summaries.

---

## Commands (fill these in once)
- Test: `pytest -q`
- Typecheck: `none`            # e.g., `mypy .` if enabled
- Lint/format: `none`          # e.g., `ruff check .` or `eslint .`
- Security (quick): `none`     # e.g., `semgrep scan --error --config p/ci`

## Process (every task)
1) **PLAN**: list target files, steps, risks; restate relevant invariants.
2) **TESTS-FIRST**: add/extend unit tests **and one property/invariant test** before code.
3) **IMPLEMENT**: apply the **smallest patch** that makes tests pass (unified diff).
4) **VERIFY**: run Test → Typecheck → Lint → (optional) Security; paste key output.
5) **REVIEWER MODE**: self-critique against invariants, edge cases, API correctness (cite docs),
   complexity, and security. If gaps, add 1–2 tests or a tiny follow-up diff, then re-run.
6) **REPORT**: produce required outputs (below).

Unless I reply “stop” or “revise”, auto-continue from PLAN → TESTS-FIRST → IMPLEMENT → VERIFY in the same task.

## Constraints
- **Diff-only**: don’t reformat untouched lines; no unrelated refactors.
- **No new deps** unless strictly required; justify and update lockfiles/scripts.
- **Docs grounding**: for nontrivial APIs, include `Source: <URL or path>` + a 1-line summary.
- **Change budget**: prefer smallest coherent change that satisfies tests & invariants.

## Invariants (example—adjust to your domain)
- Trade engine: **no duplicate elite QBs** on the same roster.
- **Conservation**: a 1-for-1 trade preserves the combined roster size of both teams.
- API responses may be **camelCase or snake_case**; tests/helpers must tolerate both.

## Rolling Sweeps (when time allows, within session)
- Prioritize tests touching **changed files**; if time remains, run a short sweep on `tests/backend/`
  with higher property-test iterations and summarize findings.

## Required Outputs (strict)
- **PLAN** – bullets with files/steps/risks.
- **TESTS_ADDED** – paths + brief purpose; **mark the property/invariant test**.
- **DIFF** – unified diffs only.
- **RUN_LOG** – key excerpts of Test / Typecheck / Lint / (Security) results.
- **SOURCES** – API/framework docs cited (URL/path + 1-line quote/summary).
- **CONFIDENCE** – number in [0,1] + 2 uncertainties + what would raise it.
- **SWEEP_REPORT** – what dirs/tests you swept and outcomes.
- **COMPREHENSIVE SUMMARY** – human-readable report:
  1) Overview & rationale,
  2) Files touched with 1–3 lines each about changes,
  3) Behavioral impact & edge cases,
  4) Test coverage (incl. the property) and any flakes,
  5) Security & quality notes (lint/type/security),
  6) Limitations/TODOs,
  7) Next steps (small, high-ROI follow-ups).
