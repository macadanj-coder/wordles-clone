import sys

with open('word_list.txt') as file:
    valid_guesses = [line.strip() for line in file]

list_valid_guesses = sorted(valid_guesses)

answer = "adieu"
guessed_words = []

def get_input() -> str:
    valid = False

    while not valid:
        guess = input(str("Enter your guess: "))
        print(f"Your guess, {guess}")
        if len(guess) != 5:
            print("Too long, or too short")
        elif guess not in list_valid_guesses:
            print("Not a valid word")
        elif guess in guessed_words:
            print("Already guessed")
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
    num_guesses = 0
    answer_stack = ""

    while True:
        guess = get_input()
        answer_stack += check_guess(guess)
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
    sys.exit(main())