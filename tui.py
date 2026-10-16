from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Footer, Header, Static
from textual.reactive import reactive
from textual import events


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
    @property
    def filled(self) -> int:
        return sum(1 for tile in self._tiles if tile.state == "filled")
    
    def set_letter(self, char: str):
        if self.filled >= self.TILES:
            return False
        tile = self._tiles[self.filled]
        tile.letter = char
        tile.state = "filled"
        return True

    def pop_letter(self):
        if self.filled == 0:
            return False
        tile = self._tiles[self.filled]
        tile.letter = None
        tile.state = "empty"
        return True


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
    BINDINGS = [("ctrl+t", "toggle_dark", "Toggle dark mode"), 
                ("ctrl+shift+q", "quit", "Quit the app")]

    def __init__(self) -> None:
        super().__init__()
        self.current_row = 0
        self.locked = False

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

    @property
    def row(self) -> GuessRow:
        return self.query(GuessRow)[self.current_row]

    def on_key(self, event: events.Key) -> None:
        if self.locked:
            return
        if event.key == "backspace":
            self.row.pop_letter()
        if event.key == "enter":
            self.submit()
        if event.is_printable and event.key.isalpha():
            self.row.set_letter(event.character)
        else:
            return
        event.stop()

    def submit(self) -> None:
        if self.row.filled < GuessRow.TILES:
            return
        self.current_row += 1

if __name__ == "__main__":
    app = Wordle()
    app.run()