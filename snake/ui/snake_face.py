"""The snake's face: big sparkly eyes, rosy cheeks, blinking and a flicking tongue.

Used by both the in-game renderer and the title screen so the character is
identical everywhere. All animation is a pure function of ``time``.
"""
from __future__ import annotations

import math

import pygame
from pygame import gfxdraw

from ..config import Theme
from .drawing import Vec, aa_circle

BLINK_PERIOD = 3.6    # seconds between blinks
BLINK_LENGTH = 0.14   # seconds the eyes stay closed
TONGUE_PERIOD = 2.8   # seconds between tongue flicks
TONGUE_LENGTH = 0.35  # seconds the tongue is out
CHEEK_COLOR = (255, 105, 150, 200)
TONGUE_COLOR = (255, 84, 118)


def draw_snake_face(surface: pygame.Surface, theme: Theme, center: Vec,
                    direction: tuple[float, float], size: float, time: float,
                    dead: bool = False) -> None:
    """Draw the face on a head block of ``size`` px centred at ``center``."""
    cx, cy = center
    dx, dy = direction
    px, py = -dy, dx  # perpendicular: the axis the two eyes sit on

    if not dead:
        _draw_tongue(surface, (cx, cy), (dx, dy), size, time)

    for side in (-1, 1):
        cheek = (cx - dx * size * 0.2 + px * size * 0.34 * side,
                 cy - dy * size * 0.2 + py * size * 0.34 * side)
        gfxdraw.filled_circle(surface, round(cheek[0]), round(cheek[1]),
                              max(1, round(size * 0.09)), CHEEK_COLOR)

    eye_r = size * 0.17
    blinking = (time % BLINK_PERIOD) < BLINK_LENGTH
    for side in (-1, 1):
        ex = cx + dx * size * 0.1 + px * size * 0.2 * side
        ey = cy + dy * size * 0.1 + py * size * 0.2 * side
        if dead:
            s = eye_r * 0.7
            pygame.draw.line(surface, theme.pupil, (ex - s, ey - s), (ex + s, ey + s), 2)
            pygame.draw.line(surface, theme.pupil, (ex - s, ey + s), (ex + s, ey - s), 2)
        elif blinking:
            s = eye_r * 0.8
            pygame.draw.line(surface, theme.pupil, (ex - dx * s, ey - dy * s),
                             (ex + dx * s, ey + dy * s), 2)
        else:
            aa_circle(surface, theme.eye, (ex, ey), eye_r)
            pupil = (ex + dx * eye_r * 0.3, ey + dy * eye_r * 0.3)
            aa_circle(surface, theme.pupil, pupil, eye_r * 0.6)
            # Sparkle always sits top-left, like a light source above the board.
            aa_circle(surface, theme.eye, (pupil[0] - eye_r * 0.25, pupil[1] - eye_r * 0.28),
                      max(1.0, eye_r * 0.22))


def _draw_tongue(surface: pygame.Surface, center: Vec, direction: tuple[float, float],
                 size: float, time: float) -> None:
    phase = time % TONGUE_PERIOD
    if phase >= TONGUE_LENGTH:
        return
    dx, dy = direction
    reach = math.sin(math.pi * phase / TONGUE_LENGTH) * size * 0.38
    if reach < 1:
        return
    base = (center[0] + dx * size * 0.45, center[1] + dy * size * 0.45)
    tip = (base[0] + dx * reach, base[1] + dy * reach)
    pygame.draw.line(surface, TONGUE_COLOR, base, tip, 3)
    fork = reach * 0.4
    angle = math.atan2(dy, dx)
    for spread in (-0.6, 0.6):
        a = angle + spread
        pygame.draw.line(surface, TONGUE_COLOR, tip,
                         (tip[0] + math.cos(a) * fork, tip[1] + math.sin(a) * fork), 2)
