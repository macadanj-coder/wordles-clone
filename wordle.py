from pathlib import Path
import random
import sys
from collections import Counter
import argparse

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


def get_input(valid_guesses: set[str], guessed_words: list[str]) -> str:
    valid = False

    while not valid:
        guess = input("Enter your guess: ").strip().lower()
        if len(guess) != WORD_LENGTH:
            print(f"Guesses must be {WORD_LENGTH} letters long")
        elif guess not in valid_guesses:
            print("Not a valid word")
        elif guess in guessed_words:
            print("Already guessed")
        else:
            valid = True
    print(f"Your guess, {guess}")
    return guess


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


def play(answer: str, valid_guesses: set[str], read_guess=get_input) -> list[str]:
    """Run one game and return the grid rows, newest last.

    `read_guess(valid_guesses, guessed_words) -> str` is injected so the loop
    can be driven by tests without touching stdin.
    """
    guessed_words: list[str] = []
    rows: list[str] = []

    for num_guesses in range(1, MAX_GUESSES + 1):
        guess = read_guess(valid_guesses, guessed_words)
        rows.append(check_guess(guess, answer))
        print("\n".join(rows))
        if guess == answer:
            print("Congratulations! You've guessed the word!")
            break
        guessed_words.append(guess)
        if num_guesses == MAX_GUESSES:
            print(f"Answer is {answer}")
            print("Better luck next time!")
    return rows


def main():
    print("Welcome to Wordle!")
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", help="determines the seed for randomnly shuffling the set of valid answers.")
    args = parser.parse_args()
    if args.seed is not None:
        print(f"seed is {args.seed}")
    valid_guesses = load_words(GUESSES_FILE)
    answer = get_answer(load_words(ANSWERS_FILE), seed=args.seed)
    play(answer, valid_guesses)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nExiting...")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Could not find word list: {e.filename}")
        sys.exit(1)
