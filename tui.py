import asyncio

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Footer, Header, Static
from textual.reactive import reactive
from textual import events
from textual.css.scalar import ScalarOffset

from game import (ANSWERS_FILE, BLACK, GREEN, GUESSES_FILE, YELLOW, Game,
                  get_answer, load_words)

MARK_STATES = {GREEN: "correct", YELLOW: "present", BLACK: "absent"}

class Tile(Static):
    """Tile, can be filled or empty"""
    STATES = {"empty", "filled", "correct", "present", "absent"}
    letter: reactive[str] = reactive("")
    state: reactive[str] = reactive("empty")

    def watch_state(self, old: str, new: str) -> None:
        for name in self.STATES:
            self.set_class(name == new, f"-{name}")

    def render(self) -> str:
        return (self.letter or " ").upper()

    async def flip(self, state: str) -> None:
        """Fade out, swap to the scored colour, fade back in."""
        half = 0.12
        self.styles.animate("opacity", 0.0, duration=half)
        await asyncio.sleep(half)
        self.state = state
        self.styles.animate("opacity", 1.0, duration=half)
        await asyncio.sleep(half)

class GuessRow(Horizontal):
    """Grid representation of tiles"""
    TILES = 5
    SHAKE = (2, -2, 1, -1, 0)   # x offsets in terminal cells
    _shaking = False

    def compose(self) -> ComposeResult:
        self._tiles = [Tile() for _ in range(self.TILES)]
        yield from self._tiles

    @property
    def filled(self) -> int:
        return sum(1 for tile in self._tiles if tile.state == "filled")
    
    @property
    def word(self) -> str:
        return "".join(tile.letter or "" for tile in self._tiles).lower()

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
        tile = self._tiles[self.filled-1]
        tile.letter = None
        tile.state = "empty"
        return True

    async def reveal(self, marks: str) -> None:
        if len(marks) != self.TILES:
            raise ValueError(f"expected {self.TILES} marks, got {len(marks)}")
        for tile, mark in zip(self._tiles, marks):
            await tile.flip(MARK_STATES[mark])

    def shake(self) -> None:
        if self._shaking:          # pressing Enter repeatedly won't stack shakes
            return
        self._shaking = True
        self._shake_step(0)

    def _shake_step(self, i: int) -> None:
        if i == len(self.SHAKE):
            self._shaking = False
            return
        self.styles.animate(
            "offset",
            value=ScalarOffset.from_offset((self.SHAKE[i], 0)),
            duration=0.05,
            on_complete=lambda: self._shake_step(i + 1),
        )

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
        self.game: Game | None = None

    def on_mount(self) -> None:
        answers = load_words(ANSWERS_FILE)
        self.game = Game(get_answer(answers), load_words(GUESSES_FILE) | answers)

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
        if self.locked or self.game is None or self.game.is_over:
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
        guess = self.row.word
        err = self.game.validate(guess)
        if err:
            self.notify(err, severity="warning")
            self.row.shake()
            return
        self.locked = True  # lock now, not in the worker, so no keypress slips in before it starts
        self.run_reveal(self.row, self.game.submit(guess))

    @work(exclusive=True)
    async def run_reveal(self, row: GuessRow, marks: str) -> None:
        try:
            await row.reveal(marks)
        finally:
            self.locked = False
        if self.game.won:
            self.notify("Splendid!")
        elif self.game.is_over:
            self.notify(f"The word was {self.game.answer.upper()}")
        else:
            self.current_row += 1

if __name__ == "__main__":
    app = Wordle()
    app.run()