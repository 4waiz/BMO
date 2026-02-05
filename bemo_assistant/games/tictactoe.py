import random
from games.base import GameBase, GameUpdate


class TicTacToeGame(GameBase):
    name = "tictactoe"

    def __init__(self):
        self.board = [" "] * 9
        self.player = "X"
        self.ai = "O"

    def start(self):
        self.board = [" "] * 9
        return GameUpdate(self.name, "Tic Tac Toe! You are X. Pick a spot 1-9.", self._status(), self._quick())

    def handle_input(self, text: str):
        if "quit" in text.lower():
            return GameUpdate(self.name, "Exiting Tic Tac Toe.", "", [], done=True)
        move = self._parse_move(text)
        if move is None:
            return GameUpdate(self.name, "Pick a square 1-9 or say top left, center, etc.", self._status(), self._quick())
        if self.board[move] != " ":
            return GameUpdate(self.name, "That spot is taken. Try another.", self._status(), self._quick())
        self.board[move] = self.player
        if self._check_win(self.player):
            return GameUpdate(self.name, f"You win!\n{self._board_text()}", self._status(), self._quick(), done=True, score_event="win")
        if self._is_draw():
            return GameUpdate(self.name, f"It's a draw.\n{self._board_text()}", self._status(), self._quick(), done=True, score_event="tie")
        self._ai_move()
        if self._check_win(self.ai):
            return GameUpdate(self.name, f"I win!\n{self._board_text()}", self._status(), self._quick(), done=True, score_event="loss")
        if self._is_draw():
            return GameUpdate(self.name, f"It's a draw.\n{self._board_text()}", self._status(), self._quick(), done=True, score_event="tie")
        return GameUpdate(self.name, self._board_text(), self._status(), self._quick())

    def _ai_move(self):
        for idx in self._available():
            self.board[idx] = self.ai
            if self._check_win(self.ai):
                return
            self.board[idx] = " "
        for idx in self._available():
            self.board[idx] = self.player
            if self._check_win(self.player):
                self.board[idx] = self.ai
                return
            self.board[idx] = " "
        if self.board[4] == " ":
            self.board[4] = self.ai
            return
        self.board[random.choice(self._available())] = self.ai

    def _available(self):
        return [i for i, v in enumerate(self.board) if v == " "]

    def _check_win(self, symbol):
        b = self.board
        wins = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6),
        ]
        return any(b[a] == b[b_] == b[c] == symbol for a, b_, c in wins)

    def _is_draw(self):
        return all(v != " " for v in self.board)

    def _board_text(self):
        def cell(i):
            return self.board[i] if self.board[i] != " " else str(i + 1)
        rows = [
            f"{cell(0)} | {cell(1)} | {cell(2)}",
            f"{cell(3)} | {cell(4)} | {cell(5)}",
            f"{cell(6)} | {cell(7)} | {cell(8)}",
        ]
        return "\n".join(rows)

    def _status(self):
        return "Say a number 1-9 or 'quit' to stop."

    def _quick(self):
        return [(str(i + 1), str(i + 1)) for i in range(9)]

    def _parse_move(self, text: str):
        t = text.lower().strip()
        if t.isdigit():
            val = int(t)
            if 1 <= val <= 9:
                return val - 1
        mapping = {
            "top left": 0, "top center": 1, "top right": 2,
            "middle left": 3, "center": 4, "middle right": 5,
            "bottom left": 6, "bottom center": 7, "bottom right": 8,
        }
        for key, idx in mapping.items():
            if key in t:
                return idx
        return None
