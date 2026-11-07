"""Application settings and visual theme."""
from __future__ import annotations

from dataclasses import dataclass

from .core import GameMode, WorldConfig

Color = tuple[int, int, int]


@dataclass(frozen=True)
class Settings:
    title: str = "Snake"
    grid_width: int = 24
    grid_height: int = 18
    cell_size: int = 30
    padding: int = 24
    hud_height: int = 104
    fps: int = 120

    # gameplay tuning
    start_length: int = 4
    base_tick: float = 0.13
    min_tick: float = 0.05
    tick_step: float = 0.008
    points_per_level: int = 10
    bonus_chance: float = 0.25
    bonus_lifetime_ticks: int = 45

    @property
    def board_size(self) -> tuple[int, int]:
        return self.grid_width * self.cell_size, self.grid_height * self.cell_size

    @property
    def window_size(self) -> tuple[int, int]:
        bw, bh = self.board_size
        return bw + 2 * self.padding, self.hud_height + bh + self.padding

    def world_config(self, mode: GameMode) -> WorldConfig:
        return WorldConfig(
            width=self.grid_width,
            height=self.grid_height,
            mode=mode,
            start_length=self.start_length,
            base_interval=self.base_tick,
            min_interval=self.min_tick,
            interval_step=self.tick_step,
            points_per_level=self.points_per_level,
            bonus_lifetime=self.bonus_lifetime_ticks,
        )


@dataclass(frozen=True)
class Theme:
    background: Color = (13, 15, 24)
    board: Color = (20, 24, 36)
    board_frame: Color = (38, 45, 66)
    tile_a: Color = (25, 30, 45)
    tile_b: Color = (22, 27, 40)
    panel: Color = (27, 32, 48)
    panel_border: Color = (46, 54, 80)

    text: Color = (232, 236, 245)
    text_dim: Color = (128, 140, 168)
    text_on_accent: Color = (12, 22, 22)

    accent: Color = (94, 234, 176)       # mint
    snake_head: Color = (110, 240, 186)
    snake_tail: Color = (64, 120, 240)   # mint -> blue gradient
    eye: Color = (250, 252, 255)
    pupil: Color = (16, 20, 30)

    apple: Color = (255, 99, 132)
    leaf: Color = (120, 220, 120)
    golden: Color = (255, 205, 60)
    danger: Color = (255, 90, 100)
