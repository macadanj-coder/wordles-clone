from pathlib import Path
import random
from collections import Counter

GREEN = "🟩"
BLACK = "⬛"
YELLOW = "🟨"

WORD_LENGTH = 5
MAX_GUESSES = 6

ANSWERS_FILE = "answers.txt"
GUESSES_FILE = "word_list.txt"

PROJECT_DIR = Path(__file__).resolve().parent


def load_words(path: str | Path) -> set[str]:
    with open(PROJECT_DIR / path) as file:
        return {line.strip() for line in file}


def check_guess(guess: str, answer: str) -> str:
    marked = [BLACK] * WORD_LENGTH
    remaining = Counter(answer)
    for i, c in enumerate(guess):
        if c == answer[i]:
            marked[i] = GREEN
            remaining[c] -= 1

    for i, c in enumerate(guess):
        if marked[i] == BLACK and remaining[c] > 0:
            marked[i] = YELLOW
            remaining[c] -= 1
    return "".join(marked)


def get_answer(answers: set[str] | None = None, seed: str | int | None = None) -> str:
    """Pick the answer for a given seed without running the game loop.

    `answers` defaults to the bundled answer list; pass an already-loaded set to
    avoid re-reading the file. Seeding uses a private RNG, so callers' own
    `random` streams are untouched.
    """
    if answers is None:
        answers = load_words(ANSWERS_FILE)
    rng = random.Random(seed)
    return rng.choice(sorted(answers))

class Game:
    """One Wordle round. Holds state; renders nothing."""

    def __init__(self, answer: str, valid_guesses: set[str]) -> None:
        self.answer = answer
        self.valid_guesses = valid_guesses
        self.guesses: list[str] = []      # accepted guesses, in order
        self.rows: list[str] = []         # matching emoji rows, same length
        self.won = False

    @property
    def is_over(self) -> bool:
        return self.won or len(self.guesses) >= MAX_GUESSES

    def validate(self, guess: str) -> str | None:
        """Return an error message, or None if the guess is playable.

        The three messages are lifted unchanged from `get_input`, so the CLI and
        the TUI cannot drift apart on wording.
        """
        # len != WORD_LENGTH  -> f"Guesses must be {WORD_LENGTH} letters long"
        # not in valid_guesses -> "Not a valid word"
        # in self.guesses      -> "Already guessed"
        if len(guess) != WORD_LENGTH:
            return f"Guesses must be {WORD_LENGTH} letters long"
        if guess not in self.valid_guesses:
            return "Not a valid word"
        if guess in self.guesses:
            return "Already guessed"
        return None

    def submit(self, guess: str) -> str:
        """Score an already-validated guess, record it, return its emoji row."""
        row = check_guess(guess, self.answer)
        self.guesses.append(guess)
        self.rows.append(row)
        self.won = guess == self.answer
        return row
