"""Unit tests for the pure game model (no pygame needed)."""
from __future__ import annotations

from typing import Iterable

import pytest

from snake.core import (Direction, EventKind, FoodKind, GameMode, Point, Snake, World,
                        WorldConfig, WorldState)


class ScriptedSpawner:
    """Deterministic spawner: hands out cells from a list, optional bonus."""

    def __init__(self, cells: list[Point], bonus: bool = False) -> None:
        self._cells = list(cells)
        self._bonus = bonus

    def free_cell(self, width: int, height: int, occupied: Iterable[Point]) -> Point | None:
        taken = set(occupied)
        while self._cells:
            cell = self._cells.pop(0)
            if cell not in taken:
                return cell
        return None

    def roll_bonus(self) -> bool:
        return self._bonus


def make_world(cells=None, mode=GameMode.CLASSIC, bonus=False, **kw) -> World:
    cfg = WorldConfig(width=10, height=10, mode=mode, start_length=3, **kw)
    return World(cfg, ScriptedSpawner(cells or [Point(0, 0), Point(0, 9)], bonus))


# --------------------------------------------------------------------- snake
def test_snake_starts_straight_behind_head():
    s = Snake(Point(5, 5), Direction.RIGHT, 3)
    assert s.body == (Point(5, 5), Point(4, 5), Point(3, 5))


def test_snake_rejects_reverse_and_duplicate_turns():
    s = Snake(Point(5, 5), Direction.RIGHT, 3)
    assert not s.queue_turn(Direction.LEFT)
    assert not s.queue_turn(Direction.RIGHT)
    assert s.queue_turn(Direction.UP)
    assert not s.queue_turn(Direction.DOWN)  # opposite of the *buffered* turn
    assert s.queue_turn(Direction.LEFT)       # legal after UP


def test_snake_growth_keeps_tail():
    s = Snake(Point(5, 5), Direction.RIGHT, 2)
    s.grow(1)
    s.advance_to(Point(6, 5))
    assert len(s) == 3


# --------------------------------------------------------------------- world
def test_tick_moves_forward():
    w = make_world()
    w.tick()
    assert w.snake.head == Point(6, 5)
    assert w.previous_body[0] == Point(5, 5)


def test_eating_apple_scores_grows_and_respawns():
    w = make_world(cells=[Point(7, 5), Point(0, 0)])
    w.tick()
    events = w.tick()
    assert [e.kind for e in events] == [EventKind.ATE]
    assert w.score == 1
    w.tick()
    assert len(w.snake) == 4
    assert w.foods[0].position == Point(0, 0)


def test_wall_collision_kills_in_classic_mode():
    w = make_world()
    for _ in range(4):
        w.tick()
    events = w.tick()  # head would move to x=10
    assert events[-1].kind is EventKind.DIED
    assert w.state is WorldState.DEAD
    assert w.tick() == []


def test_wrap_mode_wraps_around():
    w = make_world(mode=GameMode.WRAP)
    for _ in range(5):
        w.tick()
    assert w.snake.head == Point(0, 5)
    assert not w.is_over


def test_moving_into_vacating_tail_is_allowed():
    w = World(WorldConfig(width=10, height=10, start_length=4), ScriptedSpawner([Point(0, 0)]))
    for d in (Direction.DOWN, Direction.LEFT, Direction.UP):
        w.queue_turn(d)
        w.tick()
    assert not w.is_over


def test_self_collision_kills():
    w = World(WorldConfig(width=10, height=10, start_length=5), ScriptedSpawner([Point(0, 0)]))
    for d in (Direction.DOWN, Direction.LEFT, Direction.UP):
        w.queue_turn(d)
        w.tick()
    assert w.state is WorldState.DEAD


def test_bonus_spawns_expires_and_is_worth_more():
    w = make_world(cells=[Point(6, 5), Point(0, 0), Point(9, 9)], bonus=True, bonus_lifetime=3)
    events = w.tick()
    assert {e.kind for e in events} >= {EventKind.ATE, EventKind.BONUS_SPAWNED}
    golden = [f for f in w.foods if f.kind is FoodKind.GOLDEN]
    assert golden and golden[0].position == Point(9, 9)
    w.tick()
    events = w.tick()
    assert any(e.kind is EventKind.BONUS_EXPIRED for e in events)


def test_level_and_speed_increase_with_score():
    w = make_world(cells=[Point(x, 5) for x in range(6, 10)], points_per_level=2)
    start_interval = w.tick_interval
    events = []
    for _ in range(2):
        events += w.tick()
    assert w.level == 2
    assert any(e.kind is EventKind.LEVEL_UP for e in events)
    assert w.tick_interval < start_interval


def test_filling_the_board_wins():
    w = World(WorldConfig(width=4, height=1, start_length=3), ScriptedSpawner([Point(3, 0)]))
    events = w.tick()
    assert w.state is WorldState.WON
    assert events[-1].kind is EventKind.WON


def test_mode_cycles():
    assert GameMode.CLASSIC.next() is GameMode.WRAP
    assert GameMode.WRAP.next() is GameMode.CLASSIC


@pytest.mark.parametrize("d", list(Direction))
def test_opposite_is_involution(d):
    assert d.opposite.opposite is d
