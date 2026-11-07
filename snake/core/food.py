"""Food items and the strategy that decides where they appear."""
from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Protocol

from .geometry import Point


class FoodKind(Enum):
    """Each kind carries (points awarded, segments grown)."""

    APPLE = (1, 1)
    GOLDEN = (5, 3)

    @property
    def points(self) -> int:
        return self.value[0]

    @property
    def growth(self) -> int:
        return self.value[1]


@dataclass
class Food:
    position: Point
    kind: FoodKind
    ttl: int | None = None          # remaining ticks; None = never expires
    lifetime: int | None = None     # initial ttl, used for the timer ring

    @property
    def remaining_ratio(self) -> float:
        if self.ttl is None or not self.lifetime:
            return 1.0
        return max(0.0, self.ttl / self.lifetime)


class Spawner(Protocol):
    """Strategy interface; inject a deterministic one in tests."""

    def free_cell(self, width: int, height: int, occupied: Iterable[Point]) -> Point | None: ...

    def roll_bonus(self) -> bool: ...


class RandomSpawner:
    def __init__(self, bonus_chance: float = 0.25, rng: random.Random | None = None) -> None:
        self._bonus_chance = bonus_chance
        self._rng = rng or random.Random()

    def free_cell(self, width: int, height: int, occupied: Iterable[Point]) -> Point | None:
        taken = set(occupied)
        free = [Point(x, y) for y in range(height) for x in range(width) if Point(x, y) not in taken]
        return self._rng.choice(free) if free else None

    def roll_bonus(self) -> bool:
        return self._rng.random() < self._bonus_chance
