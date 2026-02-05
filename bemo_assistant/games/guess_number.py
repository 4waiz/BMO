import random
from games.base import GameBase, GameUpdate


class GuessNumberGame(GameBase):
    name = "guess_number"

    def __init__(self):
        self.target = None
        self.attempts = 0
        self.max_attempts = 5

    def start(self):
        self.target = random.randint(1, 20)
        self.attempts = 0
        status = "Guess a number between 1 and 20."
        quick = [(str(i), str(i)) for i in range(1, 11)]
        return GameUpdate(self.name, "I picked a number between 1 and 20. Try to guess!", status, quick)

    def handle_input(self, text: str):
        if "quit" in text.lower():
            return GameUpdate(self.name, "Exiting Guess the Number.", "", [], done=True)
        try:
            guess = int(text.strip())
        except Exception:
            return GameUpdate(self.name, "Please say a number between 1 and 20.", self._status(), self._quick())

        self.attempts += 1
        if guess == self.target:
            return GameUpdate(self.name, f"You got it! The number was {self.target}.", self._status(), self._quick(), done=True, score_event="win")
        if self.attempts >= self.max_attempts:
            return GameUpdate(self.name, f"Out of tries. The number was {self.target}.", self._status(), self._quick(), done=True, score_event="loss")
        if guess < self.target:
            return GameUpdate(self.name, "Higher.", self._status(), self._quick())
        return GameUpdate(self.name, "Lower.", self._status(), self._quick())

    def _status(self):
        return f"Attempts: {self.attempts}/{self.max_attempts}"

    def _quick(self):
        return [(str(i), str(i)) for i in range(1, 11)]
