import asyncio

from textual import work
from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Footer, Header, Static
from textual.reactive import reactive
from textual import events
from textual.message import Message
from textual.css.scalar import ScalarOffset

from game import (ANSWERS_FILE, BLACK, GREEN, GUESSES_FILE, YELLOW, Game,
                  get_answer, load_words)

MARK_STATES = {GREEN: "correct", YELLOW: "present", BLACK: "absent"}
RANK = {"unused": 0, "absent": 1, "present": 2, "correct": 3}

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

class Key(Static):
    """One on-screen key. Same state classes as Tile, minus the typing ones."""
    STATES = {"unused", "correct", "present", "absent"}
    state: reactive[str] = reactive("unused")

    class Pressed(Message):
        """Posted when the key is clicked; bubbles up to the app."""

        def __init__(self, value: str) -> None:
            super().__init__()
            self.value = value

    def __init__(self, value: str, label: str | None = None) -> None:
        super().__init__((label or value).upper())
        self.value = value          # what the key sends: "a".."z", "enter", "backspace"
        self.set_class(len(value) > 1, "-wide")

    def watch_state(self, old: str, new: str) -> None:
        for name in self.STATES:
            self.set_class(name == new, f"-{name}")

    def on_click(self) -> None:
        self.post_message(self.Pressed(self.value))



class Keyboard(Vertical):
    """A repesentation of the keyboard."""
    ROWS = ("qwertyuiop", "asdfghjkl", "zxcvbnm")

    def compose(self) -> ComposeResult:
        self._keys: dict[str, Key] = {}
        for i, letters in enumerate(self.ROWS):
            with Horizontal(classes="key-row"):
                if i == len(self.ROWS) - 1:
                    yield Key("enter", "⏎")
                for c in letters:
                    self._keys[c] = key = Key(c)
                    yield key
                if i == len(self.ROWS) - 1:
                    yield Key("backspace", "⌫")

    def reveal(self, guess: str, marks: str) -> None:
        for letter, mark in zip(guess, marks):
            key = self._keys[letter]
            new = MARK_STATES[mark]
            if RANK[new] > RANK[key.state]:
                key.state = new

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
        yield Keyboard()
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    @property
    def row(self) -> GuessRow:
        return self.query(GuessRow)[self.current_row]

    @property
    def keyboard(self) -> Keyboard:
        return self.query_one(Keyboard)

    def on_key(self, event: events.Key) -> None:
        if event.key in ("backspace", "enter"):
            value = event.key
        elif event.is_printable and event.key.isalpha():
            value = event.character.lower()
        else:
            return
        self.handle_input(value)
        event.stop()

    def on_key_pressed(self, message: Key.Pressed) -> None:
        self.handle_input(message.value)

    def handle_input(self, value: str) -> None:
        """Shared by physical typing and on-screen clicks."""
        if self.locked or self.game is None or self.game.is_over:
            return
        if value == "backspace":
            self.row.pop_letter()
        elif value == "enter":
            self.submit()
        else:
            self.row.set_letter(value)

    def submit(self) -> None:
        guess = self.row.word
        err = self.game.validate(guess)
        if err:
            self.notify(err, severity="warning")
            self.row.shake()
            return
        self.locked = True  # lock now, not in the worker, so no keypress slips in before it starts
        self.run_reveal(self.row, self.keyboard, guess, self.game.submit(guess))

    @work(exclusive=True)
    async def run_reveal(self, row: GuessRow, keyboard: Keyboard, guess: str, marks: str) -> None:
        try:
            await row.reveal(marks)
        finally:
            self.locked = False
        keyboard.reveal(guess, marks)
        if self.game.won:
            self.notify("Splendid!")
        elif self.game.is_over:
            self.notify(f"The word was {self.game.answer.upper()}")
        else:
            self.current_row += 1

if __name__ == "__main__":
    app = Wordle()
    app.run()