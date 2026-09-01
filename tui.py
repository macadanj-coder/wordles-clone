from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Footer, Header, Button


class Keyboard(Vertical):
    """A repesentation of the keyboard."""
class Board(Vertical):

    """A grid to represent the guesses entered"""
    def compose(self) -> ComposeResult:
        yield Button("PRESS ME!", id="button1")
class Wordle(App):
    """A Textual app to play wordle."""

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