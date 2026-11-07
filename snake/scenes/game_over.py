"""Results screen shown over a blurred snapshot of the final frame."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from ..core import GameMode, GameSummary
from ..ui.drawing import blur, dim, draw_text, ease_out_cubic, panel
from ..ui.widgets import ButtonMenu, MenuItem
from .base import Scene

if TYPE_CHECKING:
    from ..app import App


class GameOverScene(Scene):
    INTRO = 0.45  # seconds for the card to slide in

    def __init__(self, app: App, summary: GameSummary, mode: GameMode, new_record: bool,
                 backdrop: pygame.Surface) -> None:
        super().__init__(app)
        self._summary = summary
        self._mode = mode
        self._new_record = new_record
        self._time = 0.0
        self._backdrop = blur(backdrop, 10)
        dim(self._backdrop, 140)

        w, h = app.screen.get_size()
        self._card = pygame.Rect(0, 0, 400, 420)
        self._card.center = (w // 2, h // 2)
        self._menu = ButtonMenu(
            [MenuItem("Play Again", app.start_game), MenuItem("Main Menu", app.show_menu)],
            app.theme, app.fonts, center_x=w // 2, top=self._card.bottom - 140,
            width=300, height=50, gap=12,
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:
                self.app.start_game()
                return
            if event.key == pygame.K_ESCAPE:
                self.app.show_menu()
                return
        if self._time >= self.INTRO:  # ignore input until the card has landed
            self._menu.handle_event(event)

    def update(self, dt: float) -> None:
        self._time += dt
        self._menu.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        t, fonts, s = self.app.theme, self.app.fonts, self._summary
        surface.blit(self._backdrop, (0, 0))

        slide = round((1 - ease_out_cubic(self._time / self.INTRO)) * 60)
        card = self._card.move(0, slide)
        panel(surface, card, t.panel, t.panel_border, radius=22)
        cx = card.centerx

        title, color = ("You Win!", t.golden) if s.won else ("Game Over", t.danger)
        draw_text(surface, title, fonts.get(40, bold=True), color, (cx, card.y + 52))
        draw_text(surface, "SCORE", fonts.get(14, bold=True), t.text_dim, (cx, card.y + 104))
        draw_text(surface, str(s.score), fonts.get(64, bold=True), t.text, (cx, card.y + 148))

        if self._new_record:
            badge_font = fonts.get(15, bold=True)
            badge = pygame.Rect(0, 0, badge_font.size("NEW BEST")[0] + 28, 28)
            badge.center = (cx, card.y + 198)
            pygame.draw.rect(surface, t.golden, badge, border_radius=14)
            draw_text(surface, "NEW BEST", badge_font, t.text_on_accent, badge.center)
        else:
            best = self.app.scores.best(self._mode)
            draw_text(surface, f"Best: {best}", fonts.get(16, bold=True), t.text_dim,
                      (cx, card.y + 198))

        stats = f"Length {s.length}   ·   Level {s.level}   ·   {self._mode.label}"
        draw_text(surface, stats, fonts.get(15), t.text_dim, (cx, card.y + 236))

        menu_surface_offset = slide
        if menu_surface_offset:
            layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            self._menu.draw(layer)
            surface.blit(layer, (0, menu_surface_offset))
        else:
            self._menu.draw(surface)
