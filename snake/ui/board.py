"""Renders the board, food and snake for a :class:`World` snapshot.

Rendering is read-only with respect to the world. Between logic ticks the
snake is interpolated (``alpha`` in [0, 1]) so movement is smooth at any FPS.
"""
from __future__ import annotations

import math

import pygame

from ..config import Settings, Theme
from ..core import Food, FoodKind, GameMode, Point, World, WorldState
from .drawing import Vec, aa_circle, aa_polygon, blit_glow, lerp, lerp_color, shade

_SUBSTEPS = 10  # circles drawn between neighbouring segments -> smooth tube


class BoardRenderer:
    def __init__(self, settings: Settings, theme: Theme, origin: tuple[int, int],
                 mode: GameMode) -> None:
        self._theme = theme
        self._cell = settings.cell_size
        self._grid = (settings.grid_width, settings.grid_height)
        self.rect = pygame.Rect(origin, settings.board_size)
        self._mode = mode
        self._board = self._build_board_surface()
        self._shadow = pygame.Surface(self.rect.size, pygame.SRCALPHA)

    # ------------------------------------------------------------ coordinates
    def cell_center(self, gx: float, gy: float, offset: Vec = (0, 0)) -> Vec:
        c = self._cell
        return (self.rect.x + (gx + 0.5) * c + offset[0], self.rect.y + (gy + 0.5) * c + offset[1])

    def point_center(self, p: Point) -> Vec:
        return self.cell_center(p.x, p.y)

    # ------------------------------------------------------------------- draw
    def draw(self, surface: pygame.Surface, world: World, alpha: float, time: float,
             offset: Vec = (0, 0)) -> None:
        self._draw_frame(surface, offset)
        for food in world.foods:
            self._draw_food(surface, food, time, offset)
        self._draw_snake(surface, world, alpha, offset)

    def _build_board_surface(self) -> pygame.Surface:
        t, c = self._theme, self._cell
        surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, t.board, surf.get_rect(), border_radius=14)
        inset = 2
        for y in range(self._grid[1]):
            for x in range(self._grid[0]):
                color = t.tile_a if (x + y) % 2 == 0 else t.tile_b
                tile = pygame.Rect(x * c + inset, y * c + inset, c - 2 * inset, c - 2 * inset)
                pygame.draw.rect(surf, color, tile, border_radius=6)
        return surf

    def _draw_frame(self, surface: pygame.Surface, offset: Vec) -> None:
        t = self._theme
        frame = self.rect.move(round(offset[0]), round(offset[1])).inflate(12, 12)
        pygame.draw.rect(surface, shade(t.board_frame, -0.35), frame.move(0, 4), border_radius=20)
        border = t.board_frame if self._mode is GameMode.CLASSIC else shade(t.accent, -0.55)
        pygame.draw.rect(surface, border, frame, border_radius=20)
        surface.blit(self._board, frame.inflate(-12, -12))

    # ------------------------------------------------------------------- food
    def _draw_food(self, surface: pygame.Surface, food: Food, time: float, offset: Vec) -> None:
        t, c = self._theme, self._cell
        cx, cy = self.cell_center(food.position.x, food.position.y, offset)
        pulse = 0.5 + 0.5 * math.sin(time * 5 + food.position.x)

        if food.kind is FoodKind.APPLE:
            blit_glow(surface, t.apple, (cx, cy), round(c * (0.85 + 0.1 * pulse)), 90)
            r = c * (0.30 + 0.025 * pulse)
            aa_circle(surface, shade(t.apple, -0.25), (cx, cy + 1.5), r)
            aa_circle(surface, t.apple, (cx, cy), r)
            aa_circle(surface, shade(t.apple, 0.45), (cx - r * 0.35, cy - r * 0.35), r * 0.28)
            leaf = [(cx + 1, cy - r * 0.9), (cx + r * 0.75, cy - r * 1.45),
                    (cx + r * 0.95, cy - r * 0.95)]
            aa_polygon(surface, t.leaf, leaf)
            return

        # Golden star with countdown ring; blinks when about to vanish.
        ratio = food.remaining_ratio
        if ratio < 0.3 and int(time * 8) % 2 == 0:
            return
        blit_glow(surface, t.golden, (cx, cy), round(c * 1.1), 130)
        outer, inner, spin = c * 0.40, c * 0.18, time * 1.8
        star = [(cx + math.cos(spin + i * math.pi / 5) * (outer if i % 2 == 0 else inner),
                 cy + math.sin(spin + i * math.pi / 5) * (outer if i % 2 == 0 else inner))
                for i in range(10)]
        aa_polygon(surface, t.golden, star)
        aa_circle(surface, shade(t.golden, 0.6), (cx, cy), c * 0.08)
        ring = pygame.Rect(0, 0, c * 1.15, c * 1.15)
        ring.center = (round(cx), round(cy))
        pygame.draw.arc(surface, shade(t.golden, -0.15), ring, math.pi / 2,
                        math.pi / 2 + math.tau * ratio, 2)

    # ------------------------------------------------------------------ snake
    @staticmethod
    def _interpolate(previous: tuple[Point, ...], current: tuple[Point, ...],
                     alpha: float) -> list[Vec]:
        points: list[Vec] = []
        for i, cur in enumerate(current):
            prev = previous[min(i, len(previous) - 1)] if previous else cur
            dx, dy = cur.x - prev.x, cur.y - prev.y
            if abs(dx) > 1 or abs(dy) > 1:  # wrapped around an edge: snap
                points.append((cur.x, cur.y))
            else:
                points.append((prev.x + dx * alpha, prev.y + dy * alpha))
        return points

    def _draw_snake(self, surface: pygame.Surface, world: World, alpha: float,
                    offset: Vec) -> None:
        t, c = self._theme, self._cell
        segments = self._interpolate(world.previous_body, world.snake.body, alpha)
        n = len(segments)

        # Sample a dense path head -> tail, (grid_x, grid_y, index_along_body).
        samples: list[tuple[float, float, float]] = []
        for i, (x, y) in enumerate(segments):
            samples.append((x, y, float(i)))
            if i + 1 < n:
                nx, ny = segments[i + 1]
                if abs(nx - x) + abs(ny - y) <= 1.05:
                    for k in range(1, _SUBSTEPS):
                        f = k / _SUBSTEPS
                        samples.append((lerp(x, nx, f), lerp(y, ny, f), i + f))
        samples.reverse()  # draw tail first so the head ends up on top

        span = max(1.0, n - 1)
        dead = world.state is WorldState.DEAD

        # Soft drop shadow on a separate layer so overlaps don't darken.
        self._shadow.fill((0, 0, 0, 0))
        for x, y, idx in samples:
            px, py = (x + 0.5) * c, (y + 0.5) * c + 4
            pygame.draw.circle(self._shadow, (0, 0, 0), (px, py), c * (0.46 - 0.12 * idx / span))
        self._shadow.set_alpha(70)
        surface.blit(self._shadow, (self.rect.x + offset[0], self.rect.y + offset[1]))

        head_color = lerp_color(t.snake_head, t.danger, 0.7) if dead else t.snake_head
        for x, y, idx in samples:
            k = idx / span
            radius = c * (0.46 - 0.12 * k)
            color = lerp_color(head_color, t.snake_tail, k)
            cx, cy = self.cell_center(x, y, offset)
            # Only the outermost samples need an AA edge; interior overlaps would
            # otherwise draw visible rings (stripes).
            if idx == 0 or idx == span:
                aa_circle(surface, color, (cx, cy), radius)
            else:
                pygame.draw.circle(surface, color, (cx, cy), radius)

        # Glossy highlight along the spine.
        for x, y, idx in samples:
            k = idx / span
            cx, cy = self.cell_center(x, y, offset)
            color = shade(lerp_color(head_color, t.snake_tail, k), 0.22)
            pygame.draw.circle(surface, color, (cx - c * 0.07, cy - c * 0.09), c * (0.13 - 0.05 * k))

        if segments:
            self._draw_eyes(surface, self.cell_center(*segments[0], offset),
                            world.snake.direction.value, dead)

    def _draw_eyes(self, surface: pygame.Surface, head: Vec, direction: tuple[int, int],
                   dead: bool) -> None:
        t, c = self._theme, self._cell
        dx, dy = direction
        px, py = -dy, dx  # perpendicular
        for side in (-1, 1):
            ex = head[0] + dx * c * 0.12 + px * c * 0.19 * side
            ey = head[1] + dy * c * 0.12 + py * c * 0.19 * side
            aa_circle(surface, t.eye, (ex, ey), c * 0.12)
            if dead:
                s = c * 0.07
                pygame.draw.line(surface, t.pupil, (ex - s, ey - s), (ex + s, ey + s), 2)
                pygame.draw.line(surface, t.pupil, (ex - s, ey + s), (ex + s, ey - s), 2)
            else:
                aa_circle(surface, t.pupil, (ex + dx * c * 0.04, ey + dy * c * 0.04), c * 0.065)
