"""Title screen."""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from ..ui.drawing import aa_circle, blur, draw_text, lerp_color
from ..ui.widgets import ButtonMenu, MenuItem
from .base import Scene

if TYPE_CHECKING:
    from ..app import App


class MenuScene(Scene):
    def __init__(self, app: App) -> None:
        super().__init__(app)
        w, h = app.screen.get_size()
        self._time = 0.0
        self._menu = ButtonMenu(
            [
                MenuItem("Play", app.start_game),
                MenuItem(lambda: f"Mode:  {app.mode.label}", self._toggle_mode),
                MenuItem("Quit", app.quit),
            ],
            app.theme, app.fonts, center_x=w // 2, top=round(h * 0.50),
        )
        title_font = app.fonts.get(108, bold=True)
        self._title = title_font.render("SNAKE", True, app.theme.accent)
        glow = pygame.transform.smoothscale(
            self._title, (self._title.get_width() + 40, self._title.get_height() + 24))
        self._title_glow = blur(glow, 12)
        self._title_glow.set_alpha(150)

    def _toggle_mode(self) -> None:
        self.app.mode = self.app.mode.next()

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.app.quit()
            return
        if (event.type == pygame.KEYDOWN and self._menu.selected == 1
                and event.key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_a, pygame.K_d)):
            self._toggle_mode()
            return
        self._menu.handle_event(event)

    def update(self, dt: float) -> None:
        self._time += dt
        self._menu.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        t, fonts = self.app.theme, self.app.fonts
        w, h = surface.get_size()
        surface.fill(t.background)
        self._draw_dot_grid(surface)
        self._draw_wave_snake(surface, w, round(h * 0.40))

        cy = round(h * 0.21)
        bob = math.sin(self._time * 1.6) * 4
        surface.blit(self._title_glow, self._title_glow.get_rect(center=(w // 2, cy + bob)))
        surface.blit(self._title, self._title.get_rect(center=(w // 2, cy + bob)))
        draw_text(surface, "eat · grow · don't bite yourself", fonts.get(18), t.text_dim,
                  (w // 2, cy + 70))

        self._menu.draw(surface)

        best = self.app.scores.best(self.app.mode)
        draw_text(surface, f"Best ({self.app.mode.label}):  {best}", fonts.get(17, bold=True),
                  t.golden if best else t.text_dim, (w // 2, self._menu.bottom + 36))
        draw_text(surface, "Arrows / WASD to move   ·   P / Esc to pause   ·   Enter to select",
                  fonts.get(14), t.text_dim, (w // 2, h - 30))

    def _draw_dot_grid(self, surface: pygame.Surface) -> None:
        color = self.app.theme.tile_a
        w, h = surface.get_size()
        for y in range(18, h, 36):
            for x in range(18, w, 36):
                pygame.draw.circle(surface, color, (x, y), 2)

    def _draw_wave_snake(self, surface: pygame.Surface, width: int, base_y: int) -> None:
        t = self.app.theme
        count, spacing = 22, 16
        travel = width + count * spacing + 120
        head_x = (self._time * 150) % travel - 60
        for i in range(count - 1, -1, -1):
            x = head_x - i * spacing
            if not -20 < x < width + 20:
                continue
            y = base_y + math.sin(x * 0.022 + self._time * 1.2) * 20
            k = i / (count - 1)
            aa_circle(surface, lerp_color(t.snake_head, t.snake_tail, k), (x, y), 12 - 5 * k)
        hx = head_x
        hy = base_y + math.sin(hx * 0.022 + self._time * 1.2) * 20
        if -20 < hx < width + 20:
            for side in (-1, 1):
                aa_circle(surface, t.eye, (hx + 3, hy + side * 5), 3.5)
                aa_circle(surface, t.pupil, (hx + 4.5, hy + side * 5), 1.8)
