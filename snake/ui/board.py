"""Renders the board, food and snake for a :class:`World` snapshot.

Rendering is read-only with respect to the world. Between logic ticks the
snake is interpolated (``alpha`` in [0, 1]) so movement is smooth at any FPS.
"""
from __future__ import annotations

import math

import pygame

from ..config import Settings, Theme
from ..core import Food, FoodKind, GameMode, Point, World, WorldState
from .drawing import Vec, aa_polygon, blit_glow, lerp_color, progress_ring, rounded_block, shade
from .snake_face import draw_snake_face

# Board tiles and snake segments share one shape so the snake sits exactly on the grid.
TILE_INSET = 1    # px on each side of a tile -> 2 px gap between tiles
TILE_RADIUS = 7   # corner radius of tiles and snake segments
HEAD_RADIUS = 12  # the head is rounder: friendlier look


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
        self._coin: pygame.Surface | None = None

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
        self._draw_snake(surface, world, alpha, time, offset)

    def _build_board_surface(self) -> pygame.Surface:
        t, c = self._theme, self._cell
        surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        pygame.draw.rect(surf, t.board, surf.get_rect(), border_radius=14)
        inset = TILE_INSET
        for y in range(self._grid[1]):
            for x in range(self._grid[0]):
                color = t.tile_a if (x + y) % 2 == 0 else t.tile_b
                tile = pygame.Rect(x * c + inset, y * c + inset, c - 2 * inset, c - 2 * inset)
                pygame.draw.rect(surf, color, tile, border_radius=TILE_RADIUS)
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
            # Apple: a small rounded block with a darker base and a leaf.
            blit_glow(surface, t.apple, (cx, cy), round(c * (0.85 + 0.1 * pulse)), 90)
            size = round(c * (0.60 + 0.05 * pulse))
            rect = pygame.Rect(0, 0, size, size)
            rect.center = (round(cx), round(cy))
            radius = round(size * 0.3)
            pygame.draw.rect(surface, shade(t.apple, -0.3), rect.move(0, 2), border_radius=radius)
            rounded_block(surface, rect, t.apple, radius)
            top = rect.top
            pygame.draw.line(surface, shade(t.leaf, -0.45), (rect.centerx, top + 1),
                             (rect.centerx + 1, top - 3), 2)
            leaf = [(rect.centerx + 1, top - 2), (rect.centerx + 5, top - 7),
                    (rect.centerx + 10, top - 5), (rect.centerx + 6, top - 1)]
            aa_polygon(surface, t.leaf, leaf)
            return

        # Golden reward: a spinning gold coin with a countdown ring.
        # It blinks when it's about to vanish.
        ratio = food.remaining_ratio
        if ratio < 0.3 and int(time * 8) % 2 == 0:
            return
        blit_glow(surface, t.golden, (cx, cy), round(c * 1.1), 130)
        coin = self._coin_surface()
        spin = abs(math.cos(time * 2.4))  # 1 = facing us, 0 = edge-on
        width = max(2, round(coin.get_width() * (0.18 + 0.82 * spin)))
        coin = pygame.transform.smoothscale(coin, (width, coin.get_height()))
        surface.blit(coin, coin.get_rect(center=(round(cx), round(cy))))
        progress_ring(surface, shade(t.golden, -0.15), (cx, cy), c * 0.5, ratio)

    def _coin_surface(self) -> pygame.Surface:
        """Face-on coin, drawn 4x and scaled down once for smooth edges (cached)."""
        if self._coin is None:
            gold, ss = self._theme.golden, 4
            d = round(self._cell * 0.66) * ss
            r = d / 2
            big = pygame.Surface((d, d), pygame.SRCALPHA)
            pygame.draw.circle(big, shade(gold, -0.35), (r, r), r)            # rim
            pygame.draw.circle(big, gold, (r, r), r * 0.84)                    # face
            pygame.draw.circle(big, shade(gold, -0.12), (r, r), r * 0.64, ss)  # inner ring
            star = [(r + math.cos(-math.pi / 2 + i * math.pi / 5) * (r * 0.38 if i % 2 == 0 else r * 0.16),
                     r + math.sin(-math.pi / 2 + i * math.pi / 5) * (r * 0.38 if i % 2 == 0 else r * 0.16))
                    for i in range(10)]
            pygame.draw.polygon(big, shade(gold, -0.22), star)                 # embossed star
            pygame.draw.ellipse(big, (255, 255, 255, 130),                     # shine
                                pygame.Rect(r * 0.42, r * 0.3, r * 0.42, r * 0.24))
            self._coin = pygame.transform.smoothscale(big, (d // ss, d // ss))
        return self._coin

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

    def _segment_rect(self, x: float, y: float, offset: Vec) -> pygame.Rect:
        """Rounded-square segment, same size as a board tile, centred on (x, y)."""
        size = self._cell - 2 * TILE_INSET
        rect = pygame.Rect(0, 0, size, size)
        cx, cy = self.cell_center(x, y, offset)
        rect.center = (round(cx), round(cy))
        return rect

    def _draw_snake(self, surface: pygame.Surface, world: World, alpha: float, time: float,
                    offset: Vec) -> None:
        t = self._theme
        segments = self._interpolate(world.previous_body, world.snake.body, alpha)
        if not segments:
            return
        span = max(1, len(segments) - 1)
        dead = world.state is WorldState.DEAD
        head_color = lerp_color(t.snake_head, t.danger, 0.7) if dead else t.snake_head
        tail_first = list(enumerate(segments))[::-1]  # head is drawn last, on top

        # Soft drop shadow on a separate layer so overlaps don't darken.
        self._shadow.fill((0, 0, 0, 0))
        board_offset = (-self.rect.x, -self.rect.y + 4)
        for _, (x, y) in tail_first:
            pygame.draw.rect(self._shadow, (0, 0, 0), self._segment_rect(x, y, board_offset),
                             border_radius=TILE_RADIUS)
        self._shadow.set_alpha(70)
        surface.blit(self._shadow, (self.rect.x + offset[0], self.rect.y + offset[1]))

        for i, (x, y) in tail_first:
            color = lerp_color(head_color, t.snake_tail, i / span)
            rect = self._segment_rect(x, y, offset)
            rounded_block(surface, rect, color, HEAD_RADIUS if i == 0 else TILE_RADIUS)

        head = self._segment_rect(*segments[0], offset)
        draw_snake_face(surface, t, head.center, world.snake.direction.value, head.w, time, dead)
