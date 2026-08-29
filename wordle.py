from pathlib import Path
import random
import sys
from collections import Counter
import argparse
from game import (
    ANSWERS_FILE,
    BLACK,
    GREEN,
    GUESSES_FILE,
    MAX_GUESSES,
    PROJECT_DIR,
    WORD_LENGTH,
    YELLOW,
    Game,
    check_guess,
    get_answer,
    load_words,
)

def get_input(valid_guesses: set[str], guessed_words: list[str]) -> str:
    """Re-prompt until the player types a playable guess, then echo it.

    Validation lives on `Game`, so the CLI and the TUI share one set of
    messages; the throwaway instance is just a carrier for the rules.
    """
    validator = Game("", valid_guesses)
    validator.guesses = list(guessed_words)

    while True:
        guess = input("Enter your guess: ").strip().lower()
        error = validator.validate(guess)
        if error is None:
            break
        print(error)
    print(f"Your guess, {guess}")
    return guess

def play(answer: str, valid_guesses: set[str], read_guess=get_input) -> list[str]:
    """Run one game and return the grid rows, newest last.

    `read_guess(valid_guesses, guessed_words) -> str` is injected so the loop
    can be driven by tests without touching stdin.
    """
    guessed_words: list[str] = []
    game = Game(answer, valid_guesses)

    while not game.is_over:
        guess = read_guess(valid_guesses, guessed_words)
        game.submit(guess)
        print("\n".join(game.rows))

    if game.won:
        print("Splendid!")
    else:
        print(f"Answer is {answer}")
        print("Better luck next time!")
    return game.rows


def main():
    print("Welcome to Wordle!")
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", help="determines the seed for randomnly shuffling the set of valid answers.")
    parser.add_argument("--tui", help="hands off to Textual app")
    args = parser.parse_args()
    valid_guesses = load_words(GUESSES_FILE)
    answer = get_answer(load_words(ANSWERS_FILE), seed=args.seed)
    play(answer, valid_guesses)


if __name__ == "__main__":
    try:
        main()
        sys.exit(0)
    except (KeyboardInterrupt, EOFError):
        print("\nExiting...")
        sys.exit(1)
    except FileNotFoundError as e:
        print(f"Could not find word list: {e.filename}")
        sys.exit(1)
