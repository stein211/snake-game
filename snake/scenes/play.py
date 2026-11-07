"""The game itself: drives the World with a fixed timestep and renders it."""
from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from ..core import Direction, EventKind, GameEvent, RandomSpawner, World
from ..ui.board import BoardRenderer
from ..ui.drawing import dim, draw_text, panel
from ..ui.effects import FloatingTextLayer, ParticleSystem, ScreenShake
from ..ui.hud import Hud, HudData
from ..ui.widgets import ButtonMenu, MenuItem
from .base import Scene

if TYPE_CHECKING:
    from ..app import App

KEY_TO_DIRECTION = {
    pygame.K_UP: Direction.UP, pygame.K_w: Direction.UP,
    pygame.K_DOWN: Direction.DOWN, pygame.K_s: Direction.DOWN,
    pygame.K_LEFT: Direction.LEFT, pygame.K_a: Direction.LEFT,
    pygame.K_RIGHT: Direction.RIGHT, pygame.K_d: Direction.RIGHT,
}
PAUSE_KEYS = (pygame.K_p, pygame.K_ESCAPE)


class PlayScene(Scene):
    END_DELAY = 1.1  # seconds to linger on the crash before showing results

    def __init__(self, app: App) -> None:
        super().__init__(app)
        s, t = app.settings, app.theme
        self.mode = app.mode
        self.world = World(s.world_config(self.mode), RandomSpawner(s.bonus_chance))
        self.board = BoardRenderer(s, t, (s.padding, s.hud_height), self.mode)
        self.hud = Hud(t, app.fonts, pygame.Rect(s.padding, s.padding, s.board_size[0],
                                                s.hud_height - s.padding - 18))
        self.particles = ParticleSystem()
        self.texts = FloatingTextLayer(app.fonts)
        self.shake = ScreenShake()

        self._accumulator = 0.0
        self._time = 0.0
        self._dt = 0.0
        self._started = False
        self._paused = False
        self._end_timer: float | None = None
        self._score_flash = 0.0

        w, h = app.screen.get_size()
        self._pause_menu = ButtonMenu(
            [MenuItem("Resume", self._toggle_pause), MenuItem("Restart", app.start_game),
             MenuItem("Main Menu", app.show_menu)],
            t, app.fonts, center_x=w // 2, top=h // 2 - 40, width=260, height=48, gap=12,
        )

    # ------------------------------------------------------------------ input
    def handle_event(self, event: pygame.event.Event) -> None:
        if self._paused:
            if event.type == pygame.KEYDOWN and event.key in PAUSE_KEYS:
                self._toggle_pause()
            else:
                self._pause_menu.handle_event(event)
            return
        if event.type != pygame.KEYDOWN or self.world.is_over:
            return
        if event.key in PAUSE_KEYS and self._started:
            self._toggle_pause()
        elif event.key in KEY_TO_DIRECTION:
            self.world.queue_turn(KEY_TO_DIRECTION[event.key])
            self._started = True
        elif event.key == pygame.K_SPACE:
            self._started = True

    def _toggle_pause(self) -> None:
        self._paused = not self._paused
        self._pause_menu.selected = 0

    # ----------------------------------------------------------------- update
    def update(self, dt: float) -> None:
        self._dt = dt
        self._time += dt
        self.particles.update(dt)
        self.texts.update(dt)
        self.shake.update(dt)
        self._score_flash = max(0.0, self._score_flash - dt * 2.5)

        if self._paused:
            self._pause_menu.update(dt)
            return
        if self._end_timer is not None:
            self._end_timer -= dt
            if self._end_timer <= 0:
                self._finish()
            return
        if not self._started:
            return

        self._accumulator += dt
        interval = self.world.tick_interval
        while self._accumulator >= interval and not self.world.is_over:
            self._accumulator -= interval
            for event in self.world.tick():
                self._on_event(event)
            interval = self.world.tick_interval

    def _on_event(self, event: GameEvent) -> None:
        t = self.app.theme
        pos = self.board.point_center(event.position) if event.position else self.board.rect.center
        if event.kind is EventKind.ATE:
            self.particles.burst(pos, t.apple, count=14)
            self.texts.spawn(f"+{event.value}", (pos[0], pos[1] - 14), t.text)
            self._score_flash = 1.0
        elif event.kind is EventKind.ATE_BONUS:
            self.particles.burst(pos, t.golden, count=30, speed=(80, 320))
            self.texts.spawn(f"+{event.value}", (pos[0], pos[1] - 14), t.golden, size=28)
            self.shake.add(0.25)
            self._score_flash = 1.0
        elif event.kind is EventKind.BONUS_EXPIRED:
            self.particles.burst(pos, t.golden, count=8, speed=(20, 80))
        elif event.kind is EventKind.LEVEL_UP:
            c = self.board.rect.center
            self.texts.spawn(f"Level {event.value}", c, t.accent, size=40, life=1.4)
        elif event.kind is EventKind.DIED:
            self.particles.burst(pos, t.danger, count=40, speed=(60, 360), life=(0.5, 1.1))
            self.shake.add(0.9)
            self._end_timer = self.END_DELAY
        elif event.kind is EventKind.WON:
            self.particles.burst(pos, t.golden, count=60, speed=(80, 400))
            self._end_timer = self.END_DELAY

    def _finish(self) -> None:
        summary = self.world.summary()
        new_record = self.app.scores.submit(self.mode, summary.score)
        self.app.show_game_over(summary, self.mode, new_record, self.app.screen.copy())

    # ------------------------------------------------------------------- draw
    def draw(self, surface: pygame.Surface) -> None:
        t, world = self.app.theme, self.world
        surface.fill(t.background)
        best = max(self.app.scores.best(self.mode), world.score)
        self.hud.draw(surface, HudData(world.score, best, world.level, world.level_progress,
                                       self.mode.label, self._score_flash), self._dt)

        running = self._started and not world.is_over
        alpha = min(1.0, self._accumulator / world.tick_interval) if running else 1.0
        offset = self.shake.offset
        self.board.draw(surface, world, alpha, self._time, offset)
        self.particles.draw(surface, offset)
        self.texts.draw(surface, offset)

        if not self._started:
            self._draw_hint(surface, "Press an arrow key to start")
        if self._paused:
            self._draw_pause(surface)

    def _draw_hint(self, surface: pygame.Surface, text: str) -> None:
        t, fonts = self.app.theme, self.app.fonts
        font = fonts.get(18, bold=True)
        rect = pygame.Rect(0, 0, font.size(text)[0] + 48, 44)
        rect.midbottom = (self.board.rect.centerx, self.board.rect.bottom - 28)
        panel(surface, rect, t.panel, t.panel_border, radius=22)
        draw_text(surface, text, font, t.text, rect.center)

    def _draw_pause(self, surface: pygame.Surface) -> None:
        t, fonts = self.app.theme, self.app.fonts
        dim(surface, 170)
        w, h = surface.get_size()
        card = pygame.Rect(0, 0, 340, 300)
        card.center = (w // 2, h // 2 + 10)
        panel(surface, card, t.panel, t.panel_border, radius=20)
        draw_text(surface, "Paused", fonts.get(36, bold=True), t.text, (w // 2, card.y + 46))
        self._pause_menu.draw(surface)
