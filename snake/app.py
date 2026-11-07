"""Application shell: window, main loop and scene navigation.

Scenes never import each other; they ask the App to navigate. That keeps the
scene graph acyclic and makes each scene independently replaceable.
"""
from __future__ import annotations

import pygame

from .config import Settings, Theme
from .core import GameMode, GameSummary
from .persistence import HighScoreStore, default_store_path
from .scenes import GameOverScene, MenuScene, PlayScene, Scene
from .ui.drawing import FontBook


class App:
    MAX_FRAME_DT = 0.1  # clamp long frames (window drag, breakpoints)

    def __init__(self, settings: Settings | None = None, theme: Theme | None = None,
                 scores: HighScoreStore | None = None) -> None:
        pygame.init()
        self.settings = settings or Settings()
        self.theme = theme or Theme()
        pygame.display.set_caption(self.settings.title)
        self.screen = pygame.display.set_mode(self.settings.window_size)
        self.clock = pygame.time.Clock()
        self.fonts = FontBook()
        self.scores = scores or HighScoreStore(default_store_path())
        self.mode = GameMode.CLASSIC
        self._running = False
        self._scene: Scene = MenuScene(self)

    # ------------------------------------------------------------- navigation
    @property
    def scene(self) -> Scene:
        return self._scene

    def show_menu(self) -> None:
        self._scene = MenuScene(self)

    def start_game(self) -> None:
        self._scene = PlayScene(self)

    def show_game_over(self, summary: GameSummary, mode: GameMode, new_record: bool,
                       backdrop: pygame.Surface) -> None:
        self._scene = GameOverScene(self, summary, mode, new_record, backdrop)

    def quit(self) -> None:
        self._running = False

    # -------------------------------------------------------------- main loop
    def step(self, dt: float, events: list[pygame.event.Event]) -> None:
        """Advance one frame. Separate from :meth:`run` so it can be driven in tests."""
        for event in events:
            if event.type == pygame.QUIT:
                self.quit()
            else:
                self._scene.handle_event(event)
        self._scene.update(dt)
        self._scene.draw(self.screen)

    def run(self) -> None:
        self._running = True
        try:
            while self._running:
                dt = min(self.clock.tick(self.settings.fps) / 1000.0, self.MAX_FRAME_DT)
                self.step(dt, pygame.event.get())
                pygame.display.flip()
        finally:
            pygame.quit()
