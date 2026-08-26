import os
from pathlib import Path
import sys
from collections import Counter

GREEN = "🟩"
BLACK = "⬛"
YELLOW = "🟨"

PROJECT_DIR = Path(__file__).resolve().parent
os.chdir(PROJECT_DIR)

with open(PROJECT_DIR / 'word_list.txt') as file:
    valid_guesses = set([line.strip() for line in file])

answer = "adieu"
guessed_words = []

def get_input(valid_guesses : set[str], guessed_words : list[str]) -> str:
    valid = False

    while not valid:
        guess = input(str("Enter your guess: ")).strip().lower()
        print(f"Your guess, {guess}")
        if len(guess) != 5:
            print("Too long, or too short")
        elif guess not in valid_guesses:
            print("Not a valid word")
        elif guess in guessed_words:
            print("Already guessed")
        else:
            valid = True
    return guess


def check_guess(guess: str, answer: str) -> str: 
    marked = [BLACK] * 5
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
        if num_guesses == 6:
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