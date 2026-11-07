"""Grid primitives: integer points and the four movement directions."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True, slots=True)
class Point:
    """An immutable cell coordinate on the game grid."""

    x: int
    y: int

    def __add__(self, other: Point) -> Point:
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: Point) -> Point:
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, factor: int) -> Point:
        return Point(self.x * factor, self.y * factor)

    def wrapped(self, width: int, height: int) -> Point:
        """Return this point folded back onto a ``width`` x ``height`` torus."""
        return Point(self.x % width, self.y % height)

    def within(self, width: int, height: int) -> bool:
        return 0 <= self.x < width and 0 <= self.y < height


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def vector(self) -> Point:
        return Point(*self.value)

    @property
    def opposite(self) -> Direction:
        dx, dy = self.value
        return Direction((-dx, -dy))
