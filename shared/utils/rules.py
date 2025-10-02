from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from .parsers import _read_lines


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@dataclass(frozen=True)
class GameRules:
    roster_min: int
    roster_max: int
    salary_cap: int
    salary_base: int
    salary_per_rating: int
    max_contract_years: int
    elite_qb_rating: int
    max_elite_qbs: int
    min_position_depth: Dict[str, int]


@dataclass(frozen=True)
class SimulationRules:
    base_points: float
    rating_factor: float
    home_field_advantage: float
    random_variance: float
    min_score: int
    max_score: int
    passing_yards_per_rating: float
    rushing_yards_per_rating: float
    receiving_yards_per_rating: float
    defense_big_play_factor: float
    injury_probability: float


def _load_key_values(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in _read_lines(path):
        if "=" not in line:
            continue
        key, raw = line.split("=", 1)
        values[key.strip()] = raw.strip()
    return values


def load_game_rules(path: Path | None = None) -> GameRules:
    path = path or (DATA_DIR / "GameRules.txt")
    values = _load_key_values(path)

    min_depth_raw = values.get("min_position_depth", "")
    min_depth: dict[str, int] = {}
    if min_depth_raw:
        for part in min_depth_raw.split(","):
            if not part:
                continue
            position, depth = part.split(":")
            min_depth[position.strip().upper()] = int(depth)

    return GameRules(
        roster_min=int(values.get("roster_min", 46)),
        roster_max=int(values.get("roster_max", 53)),
        salary_cap=int(values.get("salary_cap", 210_000_000)),
        salary_base=int(values.get("salary_base", 750_000)),
        salary_per_rating=int(values.get("salary_per_rating", 120_000)),
        max_contract_years=int(values.get("max_contract_years", 4)),
        elite_qb_rating=int(values.get("elite_qb_rating", 92)),
        max_elite_qbs=int(values.get("max_elite_qbs", 1)),
        min_position_depth=min_depth,
    )


def load_simulation_rules(path: Path | None = None) -> SimulationRules:
    path = path or (DATA_DIR / "simulationrules.txt")
    values = _load_key_values(path)

    return SimulationRules(
        base_points=float(values.get("base_points", 24)),
        rating_factor=float(values.get("rating_factor", 0.35)),
        home_field_advantage=float(values.get("home_field_advantage", 3.0)),
        random_variance=float(values.get("random_variance", 7.5)),
        min_score=int(values.get("min_score", 10)),
        max_score=int(values.get("max_score", 48)),
        passing_yards_per_rating=float(values.get("passing_yards_per_rating", 7.0)),
        rushing_yards_per_rating=float(values.get("rushing_yards_per_rating", 4.5)),
        receiving_yards_per_rating=float(values.get("receiving_yards_per_rating", 5.5)),
        defense_big_play_factor=float(values.get("defense_big_play_factor", 0.05)),
        injury_probability=float(values.get("injury_probability", 0.07)),
    )

