"""Top bar with score, best and level cards."""
from __future__ import annotations

from dataclasses import dataclass

import pygame

from ..config import Theme
from .drawing import FontBook, draw_text, ease_out_cubic, lerp_color


@dataclass(frozen=True)
class HudData:
    score: int
    best: int
    level: int
    level_progress: float
    mode_label: str
    score_flash: float = 0.0  # 0..1, briefly tints the score after eating


class Hud:
    GAP = 14

    def __init__(self, theme: Theme, fonts: FontBook, area: pygame.Rect) -> None:
        self._theme = theme
        self._label_font = fonts.get(13, bold=True)
        self._value_font = fonts.get(30, bold=True)
        w = (area.w - 2 * self.GAP) // 3
        self._cards = [pygame.Rect(area.x + i * (w + self.GAP), area.y, w, area.h) for i in range(3)]
        self._shown_progress = 0.0

    def draw(self, surface: pygame.Surface, data: HudData, dt: float = 0.0) -> None:
        t = self._theme
        self._shown_progress += (data.level_progress - self._shown_progress) * min(1.0, dt * 8)
        if data.level_progress < self._shown_progress - 0.5:  # wrapped to a new level
            self._shown_progress = data.level_progress

        flash = ease_out_cubic(data.score_flash)
        score_color = lerp_color(t.text, t.accent, flash)
        self._card(surface, self._cards[0], "SCORE", str(data.score), score_color)
        self._card(surface, self._cards[1], f"BEST · {data.mode_label.upper()}", str(data.best),
                   t.golden if data.score and data.score >= data.best else t.text)
        level_rect = self._cards[2]
        self._card(surface, level_rect, "LEVEL", str(data.level), t.text)

        bar = pygame.Rect(level_rect.x + 72, level_rect.y + 42, level_rect.w - 90, 6)
        pygame.draw.rect(surface, t.tile_a, bar, border_radius=3)
        fill = bar.copy()
        fill.w = max(0, round(bar.w * self._shown_progress))
        if fill.w:
            pygame.draw.rect(surface, t.accent, fill, border_radius=3)

    def _card(self, surface: pygame.Surface, rect: pygame.Rect, label: str, value: str,
              value_color: tuple[int, int, int]) -> None:
        t = self._theme
        pygame.draw.rect(surface, t.panel, rect, border_radius=14)
        pygame.draw.rect(surface, t.panel_border, rect, width=1, border_radius=14)
        draw_text(surface, label, self._label_font, t.text_dim, (rect.x + 16, rect.y + 12),
                  anchor="topleft")
        draw_text(surface, value, self._value_font, value_color, (rect.x + 16, rect.y + 28),
                  anchor="topleft")
