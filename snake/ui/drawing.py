"""Low-level drawing helpers: fonts, text, anti-aliased shapes, glow, blur."""
from __future__ import annotations

from functools import lru_cache
from typing import Sequence

import pygame
from pygame import gfxdraw

Color = tuple[int, ...]
Vec = tuple[float, float]

_FONT_FAMILIES = "inter,segoeui,sfprodisplay,helveticaneue,helvetica,arial,dejavusans"


class FontBook:
    """Caches fonts by (size, bold) so they are only loaded once."""

    def __init__(self, families: str = _FONT_FAMILIES) -> None:
        self._families = families
        self._cache: dict[tuple[int, bool], pygame.font.Font] = {}

    def get(self, size: int, bold: bool = False) -> pygame.font.Font:
        key = (size, bold)
        if key not in self._cache:
            self._cache[key] = pygame.font.SysFont(self._families, size, bold=bold)
        return self._cache[key]


def draw_text(surface: pygame.Surface, text: str, font: pygame.font.Font, color: Color,
              pos: Vec, anchor: str = "center", alpha: int = 255) -> pygame.Rect:
    image = font.render(text, True, color)
    if alpha < 255:
        image.set_alpha(alpha)
    rect = image.get_rect(**{anchor: (round(pos[0]), round(pos[1]))})
    surface.blit(image, rect)
    return rect


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_color(a: Sequence[int], b: Sequence[int], t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(round(lerp(x, y, t)) for x, y in zip(a[:3], b[:3]))  # type: ignore[return-value]


def shade(color: Sequence[int], amount: float) -> tuple[int, int, int]:
    """Lighten (amount > 0) or darken (amount < 0) a color."""
    target = (255, 255, 255) if amount > 0 else (0, 0, 0)
    return lerp_color(color, target, abs(amount))


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def aa_circle(surface: pygame.Surface, color: Color, center: Vec, radius: float) -> None:
    x, y, r = round(center[0]), round(center[1]), max(1, round(radius))
    gfxdraw.aacircle(surface, x, y, r, color)
    gfxdraw.filled_circle(surface, x, y, r, color)


def aa_polygon(surface: pygame.Surface, color: Color, points: Sequence[Vec]) -> None:
    pts = [(round(x), round(y)) for x, y in points]
    gfxdraw.aapolygon(surface, pts, color)
    gfxdraw.filled_polygon(surface, pts, color)


@lru_cache(maxsize=64)
def glow_surface(color: tuple[int, int, int], radius: int, intensity: int = 120) -> pygame.Surface:
    """A soft radial glow, cached per color/radius."""
    surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    for r in range(radius, 0, -1):
        alpha = int(intensity * (1 - r / radius) ** 2)
        pygame.draw.circle(surf, (*color, alpha), (radius, radius), r)
    return surf


def blit_glow(surface: pygame.Surface, color: Sequence[int], center: Vec, radius: int,
              intensity: int = 120) -> None:
    glow = glow_surface(tuple(color[:3]), radius, intensity)
    surface.blit(glow, glow.get_rect(center=(round(center[0]), round(center[1]))))


def blur(surface: pygame.Surface, factor: int = 8) -> pygame.Surface:
    """Cheap blur by down- then up-scaling."""
    w, h = surface.get_size()
    small = pygame.transform.smoothscale(surface, (max(1, w // factor), max(1, h // factor)))
    return pygame.transform.smoothscale(small, (w, h))


def panel(surface: pygame.Surface, rect: pygame.Rect, fill: Color, border: Color | None = None,
          radius: int = 16, shadow: bool = True) -> None:
    if shadow:
        shadow_surf = pygame.Surface((rect.w + 24, rect.h + 24), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surf, (0, 0, 0, 90), shadow_surf.get_rect().inflate(-16, -16),
                         border_radius=radius + 4)
        shadow_surf = blur(shadow_surf, 4)
        surface.blit(shadow_surf, (rect.x - 12, rect.y - 6))
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surface, border, rect, width=1, border_radius=radius)


def dim(surface: pygame.Surface, alpha: int = 150, color: Color = (8, 10, 16)) -> None:
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((*color[:3], alpha))
    surface.blit(overlay, (0, 0))
