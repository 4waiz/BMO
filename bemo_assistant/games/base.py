from dataclasses import dataclass


@dataclass
class GameUpdate:
    game_name: str
    text: str
    status: str
    quick_buttons: list
    done: bool = False
    score_event: str = ""


class GameBase:
    name = "game"

    def start(self) -> GameUpdate:
        raise NotImplementedError

    def handle_input(self, text: str) -> GameUpdate:
        raise NotImplementedError
