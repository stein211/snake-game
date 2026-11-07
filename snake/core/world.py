"""Game rules. Pure logic: no rendering, no timing, no pygame.

The world advances one discrete step per :meth:`World.tick` and reports what
happened as a list of :class:`GameEvent` objects. The presentation layer reacts
to those events (particles, sounds, screen shake) without the rules having to
know anything about it.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

from .food import Food, FoodKind, RandomSpawner, Spawner
from .geometry import Direction, Point
from .snake import Snake


class GameMode(Enum):
    CLASSIC = "classic"   # walls kill
    WRAP = "wrap"         # edges wrap around

    @property
    def label(self) -> str:
        return {"classic": "Classic", "wrap": "No Walls"}[self.value]

    def next(self) -> GameMode:
        members = list(GameMode)
        return members[(members.index(self) + 1) % len(members)]


class WorldState(Enum):
    RUNNING = auto()
    DEAD = auto()
    WON = auto()


class EventKind(Enum):
    ATE = auto()
    ATE_BONUS = auto()
    BONUS_SPAWNED = auto()
    BONUS_EXPIRED = auto()
    LEVEL_UP = auto()
    DIED = auto()
    WON = auto()


@dataclass(frozen=True)
class GameEvent:
    kind: EventKind
    position: Point | None = None
    value: int = 0


@dataclass(frozen=True)
class WorldConfig:
    width: int = 24
    height: int = 18
    mode: GameMode = GameMode.CLASSIC
    start_length: int = 4
    base_interval: float = 0.13     # seconds per tick at level 1
    min_interval: float = 0.05
    interval_step: float = 0.008    # speed-up per level
    points_per_level: int = 10
    bonus_lifetime: int = 45        # ticks


@dataclass(frozen=True)
class GameSummary:
    score: int
    length: int
    level: int
    won: bool


class World:
    def __init__(self, config: WorldConfig, spawner: Spawner | None = None) -> None:
        self.config = config
        self._spawner = spawner or RandomSpawner()
        self.reset()

    # ---------------------------------------------------------------- set-up
    def reset(self) -> None:
        cfg = self.config
        start = Point(cfg.width // 2, cfg.height // 2)
        self._snake = Snake(start, Direction.RIGHT, cfg.start_length)
        self._previous_body = self._snake.body
        self._score = 0
        self._state = WorldState.RUNNING
        self._bonus: Food | None = None
        self._apple: Food | None = None
        self._apple = self._spawn(FoodKind.APPLE)

    # -------------------------------------------------------------- read API
    @property
    def snake(self) -> Snake:
        return self._snake

    @property
    def previous_body(self) -> tuple[Point, ...]:
        """Body before the latest tick; lets the renderer interpolate."""
        return self._previous_body

    @property
    def foods(self) -> tuple[Food, ...]:
        return tuple(f for f in (self._apple, self._bonus) if f is not None)

    @property
    def score(self) -> int:
        return self._score

    @property
    def state(self) -> WorldState:
        return self._state

    @property
    def is_over(self) -> bool:
        return self._state is not WorldState.RUNNING

    @property
    def level(self) -> int:
        return 1 + self._score // self.config.points_per_level

    @property
    def level_progress(self) -> float:
        ppl = self.config.points_per_level
        return (self._score % ppl) / ppl

    @property
    def tick_interval(self) -> float:
        cfg = self.config
        return max(cfg.min_interval, cfg.base_interval - (self.level - 1) * cfg.interval_step)

    def summary(self) -> GameSummary:
        return GameSummary(self._score, len(self._snake), self.level, self._state is WorldState.WON)

    # --------------------------------------------------------------- commands
    def queue_turn(self, direction: Direction) -> bool:
        return not self.is_over and self._snake.queue_turn(direction)

    def tick(self) -> list[GameEvent]:
        if self.is_over:
            return []
        events: list[GameEvent] = []
        snake = self._snake
        self._previous_body = snake.body

        snake.apply_next_turn()
        head = snake.head + snake.direction.vector
        if self.config.mode is GameMode.WRAP:
            head = head.wrapped(self.config.width, self.config.height)
        elif not head.within(self.config.width, self.config.height):
            return self._finish(WorldState.DEAD, events)

        eaten = next((f for f in self.foods if f.position == head), None)
        if eaten:
            snake.grow(eaten.kind.growth)

        # The tail cell is legal to enter only if the tail moves away this tick.
        blocking = snake.body if not snake.will_vacate_tail else snake.body[:-1]
        if head in blocking:
            return self._finish(WorldState.DEAD, events)

        snake.advance_to(head)
        if eaten:
            self._consume(eaten, events)
        self._age_bonus(events)
        return events

    # -------------------------------------------------------------- internals
    def _consume(self, food: Food, events: list[GameEvent]) -> None:
        level_before = self.level
        self._score += food.kind.points

        if food.kind is FoodKind.APPLE:
            events.append(GameEvent(EventKind.ATE, food.position, food.kind.points))
            self._apple = None
            self._apple = self._spawn(FoodKind.APPLE)
            if self._apple is None:
                self._finish(WorldState.WON, events)
                return
            if self._bonus is None and self._spawner.roll_bonus():
                self._bonus = self._spawn(FoodKind.GOLDEN, ttl=self.config.bonus_lifetime)
                if self._bonus:
                    events.append(GameEvent(EventKind.BONUS_SPAWNED, self._bonus.position))
        else:
            events.append(GameEvent(EventKind.ATE_BONUS, food.position, food.kind.points))
            self._bonus = None

        if self.level > level_before:
            events.append(GameEvent(EventKind.LEVEL_UP, value=self.level))

    def _age_bonus(self, events: list[GameEvent]) -> None:
        bonus = self._bonus
        if bonus is None or bonus.ttl is None:
            return
        bonus.ttl -= 1
        if bonus.ttl <= 0:
            events.append(GameEvent(EventKind.BONUS_EXPIRED, bonus.position))
            self._bonus = None

    def _spawn(self, kind: FoodKind, ttl: int | None = None) -> Food | None:
        occupied = set(self._snake.body) | {f.position for f in self.foods}
        cell = self._spawner.free_cell(self.config.width, self.config.height, occupied)
        return Food(cell, kind, ttl, ttl) if cell else None

    def _finish(self, state: WorldState, events: list[GameEvent]) -> list[GameEvent]:
        self._state = state
        kind = EventKind.DIED if state is WorldState.DEAD else EventKind.WON
        events.append(GameEvent(kind, self._snake.head))
        return events
