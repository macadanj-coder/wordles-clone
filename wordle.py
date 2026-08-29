import os
from pathlib import Path
import random
import sys
from collections import Counter

GREEN = "🟩"
BLACK = "⬛"
YELLOW = "🟨"

WORD_LENGTH = 5
MAX_GUESSES = 6

PROJECT_DIR = Path(__file__).resolve().parent
os.chdir(PROJECT_DIR)

answer = "adieu"
guessed_words = []

def load_words(path :str) -> set[str]:
    with open(PROJECT_DIR / path) as file:
        return set([line.strip() for line in file])

def get_input(valid_guesses : set[str], guessed_words : list[str]) -> str:
    valid = False

    while not valid:
        guess = input(str("Enter your guess: ")).strip().lower()
        print(f"Your guess, {guess}")
        if len(guess) != WORD_LENGTH:
            print("Too long, or too short")
        elif guess not in valid_guesses:
            print("Not a valid word")
        elif guess in guessed_words:
            print("Already guessed")
        else:
            valid = True
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



def main():
    print("Welcome to Wordle!")
    # Add your game logic here
    # For example, you can prompt the user for input and check their guesses
    # You can also implement the logic to select a random word and provide feedback on guesses
    num_guesses = 0
    answer_stack = ""
    valid_guesses = load_words("word_list.txt")
    answer_set = load_words("wordle-answers-alphabetical.txt")
    answers = random.sample(list(answer_set), len(answer_set))
    answer = answers[0]
    while True:
        guess = get_input(valid_guesses, guessed_words)
        answer_stack += check_guess(guess, answer)
        answer_stack += "\n"
        if guess == answer:
            print("Congratulations! You've guessed the word!")
            break
        else:
            print(f"{answer_stack}")
        num_guesses+=1
        if num_guesses == MAX_GUESSES:
            print(f"Answer is {answer}")
            print("Better luck next time!")
            break
        guessed_words.append(guess)
    print(f"{answer_stack}")

    

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print("\nExiting...")
        sys.exit(1)
    except FileNotFoundError as e :
        print(f"System Error Code: {e.errno}")      # Outputs: 2 (ENOENT)
        print(f"System Message: {e.strerror}")      # Outputs: No such file or directory
        print(f"Attempted Path: {e.filename}")      