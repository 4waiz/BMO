import random
from games.base import GameBase, GameUpdate


class RPSGame(GameBase):
    name = "rock_paper_scissors"

    def start(self):
        status = "Choose rock, paper, or scissors."
        quick = [("Rock", "rock"), ("Paper", "paper"), ("Scissors", "scissors")]
        return GameUpdate(self.name, "Rock, paper, or scissors?", status, quick)

    def handle_input(self, text: str):
        if "quit" in text.lower():
            return GameUpdate(self.name, "Exiting Rock Paper Scissors.", "", [], done=True)
        choice = self._parse_choice(text)
        if not choice:
            return GameUpdate(self.name, "Say rock, paper, or scissors.", "", self._quick())
        ai = random.choice(["rock", "paper", "scissors"])
        result = self._decide(choice, ai)
        if result == "win":
            msg = f"I picked {ai}. You win!"
        elif result == "loss":
            msg = f"I picked {ai}. I win!"
        else:
            msg = f"I picked {ai}. It's a tie."
        return GameUpdate(self.name, msg, "Play again?", self._quick(), score_event=result)

    def _parse_choice(self, text: str):
        t = text.lower()
        for c in ("rock", "paper", "scissors"):
            if c in t:
                return c
        return None

    def _decide(self, player, ai):
        if player == ai:
            return "tie"
        wins = {"rock": "scissors", "paper": "rock", "scissors": "paper"}
        return "win" if wins[player] == ai else "loss"

    def _quick(self):
        return [("Rock", "rock"), ("Paper", "paper"), ("Scissors", "scissors")]
