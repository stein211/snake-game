from snake.core import GameMode
from snake.persistence import HighScoreStore


def test_scores_persist_per_mode(tmp_path):
    path = tmp_path / "scores.json"
    store = HighScoreStore(path)
    assert store.submit(GameMode.CLASSIC, 12)
    assert not store.submit(GameMode.CLASSIC, 5)
    assert HighScoreStore(path).best(GameMode.CLASSIC) == 12
    assert HighScoreStore(path).best(GameMode.WRAP) == 0


def test_corrupt_file_is_ignored(tmp_path):
    path = tmp_path / "scores.json"
    path.write_text("{not json")
    assert HighScoreStore(path).best(GameMode.CLASSIC) == 0
