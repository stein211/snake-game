"""Juice: particles, floating score text and screen shake."""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

import pygame
from pygame import gfxdraw

from .drawing import FontBook, Vec, draw_text


@dataclass
class _Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    radius: float
    color: tuple[int, int, int]


class ParticleSystem:
    def __init__(self, rng: random.Random | None = None) -> None:
        self._particles: list[_Particle] = []
        self._rng = rng or random.Random()

    def burst(self, pos: Vec, color: tuple[int, int, int], count: int = 16,
              speed: tuple[float, float] = (60, 240), life: tuple[float, float] = (0.35, 0.8),
              radius: tuple[float, float] = (2.0, 4.5)) -> None:
        rnd = self._rng
        for _ in range(count):
            angle = rnd.uniform(0, math.tau)
            s = rnd.uniform(*speed)
            lifetime = rnd.uniform(*life)
            self._particles.append(_Particle(pos[0], pos[1], math.cos(angle) * s,
                                             math.sin(angle) * s, lifetime, lifetime,
                                             rnd.uniform(*radius), color))

    def update(self, dt: float) -> None:
        drag = max(0.0, 1 - 4 * dt)
        alive = []
        for p in self._particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vx *= drag
            p.vy *= drag
            p.life -= dt
            if p.life > 0:
                alive.append(p)
        self._particles = alive

    def draw(self, surface: pygame.Surface, offset: Vec = (0, 0)) -> None:
        for p in self._particles:
            k = p.life / p.max_life
            r = max(1, round(p.radius * (0.4 + 0.6 * k)))
            gfxdraw.filled_circle(surface, round(p.x + offset[0]), round(p.y + offset[1]), r,
                                  (*p.color, round(255 * k)))


@dataclass
class _FloatingText:
    text: str
    x: float
    y: float
    color: tuple[int, int, int]
    size: int
    life: float
    max_life: float


class FloatingTextLayer:
    RISE_SPEED = 46.0

    def __init__(self, fonts: FontBook) -> None:
        self._fonts = fonts
        self._items: list[_FloatingText] = []

    def spawn(self, text: str, pos: Vec, color: tuple[int, int, int], size: int = 22,
              life: float = 0.9) -> None:
        self._items.append(_FloatingText(text, pos[0], pos[1], color, size, life, life))

    def update(self, dt: float) -> None:
        for item in self._items:
            item.y -= self.RISE_SPEED * dt
            item.life -= dt
        self._items = [i for i in self._items if i.life > 0]

    def draw(self, surface: pygame.Surface, offset: Vec = (0, 0)) -> None:
        for item in self._items:
            k = item.life / item.max_life
            draw_text(surface, item.text, self._fonts.get(item.size, bold=True), item.color,
                      (item.x + offset[0], item.y + offset[1]), alpha=round(255 * min(1, k * 1.6)))


class ScreenShake:
    """Trauma-based shake: offset scales with trauma squared for a nice falloff."""

    def __init__(self, max_offset: float = 12.0, decay: float = 1.5,
                 rng: random.Random | None = None) -> None:
        self._max = max_offset
        self._decay = decay
        self._trauma = 0.0
        self._rng = rng or random.Random()
        self.offset: Vec = (0.0, 0.0)

    def add(self, trauma: float) -> None:
        self._trauma = min(1.0, self._trauma + trauma)

    def update(self, dt: float) -> None:
        self._trauma = max(0.0, self._trauma - self._decay * dt)
        m = self._max * self._trauma ** 2
        self.offset = (self._rng.uniform(-m, m), self._rng.uniform(-m, m)) if m else (0.0, 0.0)
