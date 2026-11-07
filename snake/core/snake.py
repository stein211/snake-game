"""The snake entity: body segments, heading, buffered turns and growth."""
from __future__ import annotations

from collections import deque

from .geometry import Direction, Point


class Snake:
    """A snake made of grid segments, head first.

    Turns are buffered so that quick key presses (e.g. UP then LEFT within a
    single tick) are all honoured on consecutive ticks instead of being lost.
    """

    MAX_BUFFERED_TURNS = 3

    def __init__(self, head: Point, direction: Direction, length: int) -> None:
        if length < 1:
            raise ValueError("snake length must be at least 1")
        step = direction.vector
        self._body: deque[Point] = deque(head - step * i for i in range(length))
        self._direction = direction
        self._turns: deque[Direction] = deque()
        self._pending_growth = 0

    # ------------------------------------------------------------------ state
    @property
    def head(self) -> Point:
        return self._body[0]

    @property
    def body(self) -> tuple[Point, ...]:
        return tuple(self._body)

    @property
    def direction(self) -> Direction:
        return self._direction

    @property
    def will_vacate_tail(self) -> bool:
        """True if the tail cell becomes free on the next move."""
        return self._pending_growth == 0

    def __len__(self) -> int:
        return len(self._body)

    def occupies(self, point: Point) -> bool:
        return point in self._body

    # --------------------------------------------------------------- commands
    def queue_turn(self, direction: Direction) -> bool:
        """Buffer a turn. Reversals and no-op turns are rejected."""
        reference = self._turns[-1] if self._turns else self._direction
        if direction in (reference, reference.opposite):
            return False
        if len(self._turns) >= self.MAX_BUFFERED_TURNS:
            return False
        self._turns.append(direction)
        return True

    def apply_next_turn(self) -> None:
        if self._turns:
            self._direction = self._turns.popleft()

    def grow(self, segments: int = 1) -> None:
        self._pending_growth += segments

    def advance_to(self, new_head: Point) -> None:
        self._body.appendleft(new_head)
        if self._pending_growth:
            self._pending_growth -= 1
        else:
            self._body.pop()
