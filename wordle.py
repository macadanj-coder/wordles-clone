import sys

answer = "adieu"
guessed_words = []

def get_input() -> str:
    valid = False

    while not valid:
        guess = input(str("Enter your guess: "))
        print(f"Your guess, {guess}")
        if len(guess) != 5:
            print("Too long, or too short")
        else:
            valid = True
    return guess


def check_guess(guess: str) -> str: 
    hint_string = ""
    for i, c in enumerate(guess):
        if c == answer[i]:  
            hint_string += "🟩"
        elif c in answer:
            hint_string += "🟨"
        else:
            hint_string += "⬛"
    return hint_string



def main():
    print("Welcome to Wordle!")
    # Add your game logic here
    # For example, you can prompt the user for input and check their guesses
    # You can also implement the logic to select a random word and provide feedback on guesses
    game = True
    num_guesses = 0
    answer_stack = ""

    while game:
        guess = get_input()
        hint_string = check_guess(guess)
        print(f"{hint_string}")
        answer_stack += hint_string
        answer_stack += "\n"
        if guess == answer:
            print("Congratulations! You've guessed the word!")
            game = False
        num_guesses+=1
        if num_guesses == 6:
            game = False
            print(f"Answer is {answer}")
            print("Better luck next time!")
    print(f"{answer_stack}")

    

if __name__ == "__main__":
    sys.exit(main())