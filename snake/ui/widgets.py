"""Reusable interactive widgets."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pygame

from ..config import Theme
from .drawing import FontBook, draw_text, lerp_color

_UP_KEYS = (pygame.K_UP, pygame.K_w)
_DOWN_KEYS = (pygame.K_DOWN, pygame.K_s)
_CONFIRM_KEYS = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)


@dataclass
class MenuItem:
    label: str | Callable[[], str]
    action: Callable[[], None]

    @property
    def text(self) -> str:
        return self.label() if callable(self.label) else self.label


class ButtonMenu:
    """A vertical list of buttons driven by keyboard *and* mouse."""

    def __init__(self, items: list[MenuItem], theme: Theme, fonts: FontBook, center_x: int,
                 top: int, width: int = 300, height: int = 52, gap: int = 14,
                 font_size: int = 22) -> None:
        self._items = items
        self._theme = theme
        self._font = fonts.get(font_size, bold=True)
        self._rects = [
            pygame.Rect(0, 0, width, height).move(center_x - width // 2, top + i * (height + gap))
            for i in range(len(items))
        ]
        self._hover = [0.0] * len(items)
        self.selected = 0

    @property
    def bottom(self) -> int:
        return self._rects[-1].bottom if self._rects else 0

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in _UP_KEYS:
                self.selected = (self.selected - 1) % len(self._items)
                return True
            if event.key in _DOWN_KEYS:
                self.selected = (self.selected + 1) % len(self._items)
                return True
            if event.key in _CONFIRM_KEYS:
                self._items[self.selected].action()
                return True
        elif event.type == pygame.MOUSEMOTION:
            for i, rect in enumerate(self._rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, rect in enumerate(self._rects):
                if rect.collidepoint(event.pos):
                    self.selected = i
                    self._items[i].action()
                    return True
        return False

    def update(self, dt: float) -> None:
        for i in range(len(self._hover)):
            target = 1.0 if i == self.selected else 0.0
            self._hover[i] += (target - self._hover[i]) * min(1.0, dt * 14)

    def draw(self, surface: pygame.Surface) -> None:
        t = self._theme
        for item, rect, h in zip(self._items, self._rects, self._hover):
            r = rect.move(0, round(-2 * h))
            pygame.draw.rect(surface, lerp_color(t.panel, t.accent, h), r, border_radius=14)
            pygame.draw.rect(surface, lerp_color(t.panel_border, t.accent, h), r, width=1,
                             border_radius=14)
            draw_text(surface, item.text, self._font, lerp_color(t.text, t.text_on_accent, h),
                      r.center)
