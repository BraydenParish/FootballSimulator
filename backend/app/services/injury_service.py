from __future__ import annotations

"""Helpers for generating consistent injury metadata during simulations."""

from dataclasses import dataclass
from random import Random


@dataclass(slots=True)
class InjuryMetadata:
    """Structured payload describing an in-game injury."""

    player_id: int
    team_id: int
    name: str
    status: str
    duration_weeks: int
    games_missed: int


class InjuryService:
    """Enforce baseline rules around simulated injuries and stat sanity."""

    def __init__(self, *, min_duration_weeks: int = 1, max_duration_weeks: int = 6) -> None:
        self.min_duration_weeks = max(1, int(min_duration_weeks))
        self.max_duration_weeks = max(self.min_duration_weeks, int(max_duration_weeks))

    # Injury helpers -----------------------------------------------------

    def generate_injury(self, rng: Random, player) -> InjuryMetadata:
        """Create an injury payload with a minimum enforced duration."""

        base = int(round(rng.gauss(self.min_duration_weeks + 1, 1)))
        duration = self._clamp_duration(base)
        games_missed = max(0, duration - 1)

        return InjuryMetadata(
            player_id=player["id"],
            team_id=player["team_id"],
            name=player["name"],
            status="questionable",
            duration_weeks=duration,
            games_missed=games_missed,
        )

    def _clamp_duration(self, value: int) -> int:
        duration = max(self.min_duration_weeks, value)
        duration = min(self.max_duration_weeks, duration)
        return duration

    # Stat helpers -------------------------------------------------------

    def clamp_yards(self, yards: int) -> int:
        """Ensure yardage-based statistics are never negative."""

        return max(0, int(yards))

    def clamp_touchdowns(self, touchdowns: int) -> int:
        return max(0, int(touchdowns))

    def clamp_sacks(self, sacks: float) -> float:
        return max(0.0, float(sacks))

    def clamp_turnovers(self, turnovers: int) -> int:
        return max(0, int(turnovers))

