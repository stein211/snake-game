"""High-score storage (one record per game mode) in a small JSON file."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .core import GameMode


def default_store_path() -> Path:
    base = os.environ.get("SNAKE_DATA_DIR")
    root = Path(base) if base else Path.home() / ".snake_game"
    return root / "highscores.json"


class HighScoreStore:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._scores: dict[str, int] = self._load()

    def best(self, mode: GameMode) -> int:
        return self._scores.get(mode.value, 0)

    def submit(self, mode: GameMode, score: int) -> bool:
        """Record ``score``; return True if it is a new best."""
        if score <= self.best(mode):
            return False
        self._scores[mode.value] = score
        self._save()
        return True

    def _load(self) -> dict[str, int]:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return {k: int(v) for k, v in data.items()}
        except (OSError, ValueError, AttributeError):
            return {}

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(self._scores, indent=2), encoding="utf-8")
        except OSError:
            pass  # a read-only home directory must never crash the game
