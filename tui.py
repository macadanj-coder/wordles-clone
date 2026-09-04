from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Footer, Header, Static
from textual.reactive import reactive



class Tile(Static):
    """Tile, can be filled or empty"""
    STATES = {"empty", "filled", "correct", "present", "absent"}
    letter: reactive[str] = reactive("")
    state: reactive[str] = reactive("empty")

    def watch_state(self, old: str, new: str) -> None:
        for name in self.STATES:
            self.set_class(name == new, f"-{name}")

    def render(self) -> str:
        return self.letter or " "


class GuessRow(Horizontal):
    """Grid representation of tiles"""
    TILES = 5

    def compose(self) -> ComposeResult:
        self._tiles = [Tile() for _ in range(self.TILES)]
        yield from self._tiles


class Keyboard(Vertical):
    """A repesentation of the keyboard."""
class Board(Vertical):
    """A grid to represent the guesses entered"""
    GUESSES = 6

    def compose(self) -> ComposeResult:
        self._guess_rows = [GuessRow() for _ in range(self.GUESSES)]
        yield from self._guess_rows

class Wordle(App):
    """A Textual app to play wordle."""

    CSS_PATH = "tui.tcss"
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Board()
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = Wordle()
    app.run()