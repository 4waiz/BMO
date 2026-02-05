import json
from pathlib import Path


class Scoreboard:
    def __init__(self, data_dir: Path):
        self.path = data_dir / "scoreboard.json"
        self.scores = {}
        self._load()

    def _load(self):
        if not self.path.exists():
            self.scores = {}
            return
        with self.path.open("r", encoding="utf-8") as f:
            self.scores = json.load(f)

    def _save(self):
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.scores, f, indent=2)

    def record(self, game: str, result: str):
        game_scores = self.scores.setdefault(game, {"win": 0, "loss": 0, "tie": 0})
        if result not in game_scores:
            game_scores[result] = 0
        game_scores[result] += 1
        self._save()

    def summary(self, game: str) -> str:
        game_scores = self.scores.get(game, {"win": 0, "loss": 0, "tie": 0})
        return f"Wins: {game_scores.get('win',0)}  Losses: {game_scores.get('loss',0)}  Ties: {game_scores.get('tie',0)}"
