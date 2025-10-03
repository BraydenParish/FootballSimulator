from __future__ import annotations

import pytest

try:
    from backend.app.services.player_progression import progress_player
except ImportError:  # pragma: no cover - module not yet implemented
    progress_player = None


@pytest.mark.xfail(reason="TODO: player progression model not implemented yet")
def test_running_backs_decline_after_twenty_nine() -> None:
    if progress_player is None:
        pytest.xfail("progress_player helper not available yet")
    player = {"position": "RB", "age": 29, "overall_rating": 88}
    updated = progress_player(player, recent_stats={"yards": 1400, "touchdowns": 12})
    assert updated["overall_rating"] < player["overall_rating"]


@pytest.mark.xfail(reason="TODO: player progression model not implemented yet")
def test_quarterbacks_peak_later() -> None:
    if progress_player is None:
        pytest.xfail("progress_player helper not available yet")
    player = {"position": "QB", "age": 30, "overall_rating": 90}
    updated = progress_player(player, recent_stats={"yards": 4200, "touchdowns": 32})
    assert updated["overall_rating"] >= player["overall_rating"]


@pytest.mark.xfail(reason="TODO: performance based bumps pending implementation")
def test_high_performance_generates_rating_boost() -> None:
    if progress_player is None:
        pytest.xfail("progress_player helper not available yet")
    baseline = progress_player({"position": "WR", "age": 25, "overall_rating": 85}, recent_stats={"yards": 900, "touchdowns": 6})
    breakout = progress_player({"position": "WR", "age": 25, "overall_rating": 85}, recent_stats={"yards": 1400, "touchdowns": 12})
    assert breakout["overall_rating"] >= baseline["overall_rating"] + 1
