"""Regression test placeholders for known bugs.

These tests should be flipped from xfail to pass once the associated
issues are resolved. They exist so we can lock in fixes and prevent
future regressions.
"""

import pytest


@pytest.mark.xfail(reason="Awaiting fix: trades can overfill rosters with too many active players.", strict=False)
def test_trade_prevents_roster_overflow():
    """Ensure trade proposals don't leave either team above the roster limit."""
    pytest.xfail("Pending roster overflow guard implementation.")


@pytest.mark.xfail(reason="Awaiting fix: injury generator sometimes yields impossible zero-week injuries.", strict=False)
def test_injury_duration_has_minimum_one_week():
    """Lock in fix so players always miss at least one week when flagged as injured."""
    pytest.xfail("Pending injury duration minimum enforcement.")


@pytest.mark.xfail(reason="Awaiting fix: stats parser occasionally outputs negative rushing yards.", strict=False)
def test_box_scores_have_non_negative_stats():
    """Regression guard for impossible negative stat lines."""
    pytest.xfail("Pending stat normalization fix.")
