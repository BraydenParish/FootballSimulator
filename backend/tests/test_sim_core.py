from __future__ import annotations

import random
import sqlite3

import pytest

from backend.app.services.simulation_service import SimulationService
from backend.tests.conftest import initialize_database
from shared.utils.rules import load_simulation_rules


@pytest.fixture()
def simulation_service() -> SimulationService:
    rules = load_simulation_rules()
    return SimulationService(rules)


class _StubRandom:
    def __init__(self, gauss_values: list[float], random_values: list[float]):
        self._gauss = list(gauss_values)
        self._random = list(random_values)

    def gauss(self, _mu: float, _sigma: float) -> float:
        return self._gauss.pop(0)

    def random(self) -> float:
        return self._random.pop(0)


def test_simulate_game_produces_reasonable_scores(db_connection: sqlite3.Connection, simulation_service: SimulationService) -> None:
    game_row = db_connection.execute("SELECT * FROM games WHERE id = 1").fetchone()
    result = simulation_service._simulate_game(db_connection, game_row, detailed=False)

    assert 10 <= result.home_team["score"] <= 60
    assert 10 <= result.away_team["score"] <= 60

    for team_stats in result.team_stats.values():
        assert team_stats["total_yards"] >= 0
        assert team_stats["turnovers"] >= 0
        for player in team_stats["players"]:
            for key in ("passing_yards", "passing_tds", "interceptions", "rushing_yards", "rushing_tds", "receiving_yards", "receiving_tds", "tackles", "sacks", "forced_turnovers"):
                value = player.get(key, 0) or 0
                assert value >= 0


def test_simulate_game_is_deterministic_with_seed(tmp_path, simulation_service: SimulationService) -> None:
    db_path = tmp_path / "repro.db"
    if db_path.exists():
        db_path.unlink()
    initialize_database(db_path)

    first_connection = sqlite3.connect(db_path)
    first_connection.row_factory = sqlite3.Row
    game = first_connection.execute("SELECT * FROM games WHERE id = 1").fetchone()
    first_result = simulation_service._simulate_game(first_connection, game, detailed=False)
    first_payload = {
        "home": first_result.home_team["score"],
        "away": first_result.away_team["score"],
        "stats": first_result.team_stats,
    }
    first_connection.close()

    if db_path.exists():
        db_path.unlink()
    initialize_database(db_path)

    second_connection = sqlite3.connect(db_path)
    second_connection.row_factory = sqlite3.Row
    repeat_game = second_connection.execute("SELECT * FROM games WHERE id = 1").fetchone()
    second_result = simulation_service._simulate_game(second_connection, repeat_game, detailed=False)
    second_payload = {
        "home": second_result.home_team["score"],
        "away": second_result.away_team["score"],
        "stats": second_result.team_stats,
    }
    second_connection.close()

    assert second_payload == first_payload


@pytest.mark.parametrize(
    "gauss_values, breaker",
    [([-3.0, 3.0], 0.8), ([-20.0, -15.0], 0.2)],
    ids=["mid_range", "clamped_min"],
)
def test_generate_scores_breaks_ties(
    simulation_service: SimulationService, gauss_values: list[float], breaker: float
) -> None:
    rng = _StubRandom(gauss_values=gauss_values, random_values=[breaker])

    home_score, away_score = simulation_service._generate_scores(rng, home_rating=80, away_rating=80)

    assert home_score != away_score
    assert simulation_service.rules.min_score <= home_score <= simulation_service.rules.max_score
    assert simulation_service.rules.min_score <= away_score <= simulation_service.rules.max_score


def test_impact_label_takes_lead_and_ties(simulation_service: SimulationService) -> None:
    takes_lead = simulation_service._impact_label(
        home_before=24,
        away_before=20,
        home_after=24,
        away_after=27,
        scoring_team="away",
    )
    assert takes_lead == "takes_lead"

    ties_game = simulation_service._impact_label(
        home_before=17,
        away_before=20,
        home_after=20,
        away_after=20,
        scoring_team="home",
    )
    assert ties_game == "ties_game"


def test_score_breakdown_conserves_points_property(simulation_service: SimulationService) -> None:
    for score in range(0, simulation_service.rules.max_score + 1):
        rng = random.Random(score)
        segments = simulation_service._score_breakdown(rng, score)

        assert sum(segments) == score
        assert all(segment > 0 for segment in segments)
