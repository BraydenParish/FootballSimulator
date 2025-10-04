from __future__ import annotations

import random
import sqlite3
from dataclasses import replace

import pytest

from backend.app.services.simulation_service import SimulationService
from shared.utils.rules import load_simulation_rules


def test_default_injury_probability_within_bounds() -> None:
    from backend.main import SIMULATION_RULES

    assert 0.0 <= SIMULATION_RULES.injury_probability <= 1.0


def test_apply_injuries_respects_probability_extremes(db_connection: sqlite3.Connection) -> None:
    players = db_connection.execute(
        "SELECT * FROM players ORDER BY id"
    ).fetchall()

    base_rules = load_simulation_rules()

    never_rules = replace(base_rules, injury_probability=0.0)
    never_service = SimulationService(never_rules)
    never_rng = random.Random(42)
    never_injuries = never_service._apply_injuries(db_connection, never_rng, players)
    assert never_injuries == []
    statuses = {row["injury_status"] for row in db_connection.execute("SELECT injury_status FROM players")}
    assert statuses == {"healthy"}

    db_connection.execute("UPDATE players SET injury_status = 'healthy'")
    db_connection.commit()

    always_rules = replace(base_rules, injury_probability=1.0)
    always_service = SimulationService(always_rules)
    always_rng = random.Random(42)
    always_injuries = always_service._apply_injuries(db_connection, always_rng, players)
    assert len(always_injuries) == len(players)
    statuses_after = {row["injury_status"] for row in db_connection.execute("SELECT injury_status FROM players")}
    assert statuses_after == {"questionable"}


@pytest.mark.xfail(reason="TODO: injury duration modeling pending implementation")
def test_injury_duration_within_expected_bounds() -> None:
    pytest.xfail("Injury duration modeling has not been implemented")


@pytest.mark.xfail(reason="TODO: track repeated injury risk once implemented")
def test_repeated_injury_risk_increases() -> None:
    pytest.xfail("Repeated injury modifiers not implemented")
