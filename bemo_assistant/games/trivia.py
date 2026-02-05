import json
import random
from pathlib import Path
from games.base import GameBase, GameUpdate


class TriviaGame(GameBase):
    name = "trivia"

    def __init__(self):
        self.questions = self._load_questions()
        self.current = None

    def _load_questions(self):
        path = Path(__file__).parent / "trivia_questions.json"
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def start(self):
        self.current = random.choice(self.questions) if self.questions else None
        return self._question_update("Let's do trivia!")

    def handle_input(self, text: str):
        if "quit" in text.lower():
            return GameUpdate(self.name, "Exiting Trivia.", "", [], done=True)
        if not self.current:
            self.current = random.choice(self.questions) if self.questions else None
            return self._question_update("No questions loaded.")

        answer = self._parse_answer(text)
        if answer is None:
            return GameUpdate(self.name, "Please answer A, B, C, or D.", self._status(), self._quick())

        correct = self.current["answer"]
        if answer == correct:
            msg = "Correct!"
            score = "win"
        else:
            msg = f"Oops, the correct answer was {chr(65 + correct)}."
            score = "loss"

        explanation = self.current.get("explanation", "")
        if explanation:
            msg += " " + explanation

        self.current = random.choice(self.questions) if self.questions else None
        update = self._question_update(msg)
        update.score_event = score
        return update

    def _parse_answer(self, text: str):
        t = text.strip().lower()
        if not t:
            return None
        if t in ("a", "b", "c", "d"):
            return ord(t) - 97
        if t.isdigit():
            val = int(t)
            if 1 <= val <= 4:
                return val - 1
        choices = self.current.get("choices", []) if self.current else []
        for idx, choice in enumerate(choices):
            if choice.lower() in t:
                return idx
        return None

    def _question_update(self, prefix: str):
        if not self.current:
            return GameUpdate(self.name, "No trivia questions available.", "", [], done=True)
        q = self.current
        choices = q.get("choices", [])
        question_text = f"{q.get('question', '')}\nA) {choices[0]}  B) {choices[1]}  C) {choices[2]}  D) {choices[3]}"
        text = f"{prefix} {question_text}"
        return GameUpdate(self.name, text, self._status(), self._quick())

    def _status(self):
        return "Answer A, B, C, or D. Say 'quit' to stop."

    def _quick(self):
        return [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]
