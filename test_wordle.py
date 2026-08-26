"""Tests for wordle.py — stdlib unittest, no third-party dependencies.

Run from anywhere:  python -m unittest test_wordle
"""

import os
import unittest
from pathlib import Path

# wordle.py opens 'word_list.txt' at import time relative to the CWD (REVIEW.md
# #4/#7). Until that is fixed, anchor the CWD to the project directory so these
# tests run from any working directory.
PROJECT_DIR = Path(__file__).resolve().parent
os.chdir(PROJECT_DIR)

import wordle
from wordle import BLACK, GREEN, YELLOW, check_guess


class CheckGuessTests(unittest.TestCase):
    """Scoring behaviour, including the duplicate-letter regression (#1)."""

    def test_exact_match_is_all_green(self):
        self.assertEqual(check_guess("adieu", "adieu"), GREEN * 5)

    def test_no_overlap_is_all_black(self):
        self.assertEqual(check_guess("sport", "adieu"), BLACK * 5)

    def test_duplicate_guess_letters_do_not_over_claim(self):
        # Regression for REVIEW.md #1: "adieu" has a single 'e', so only the
        # first 'e' in "eerie" may score yellow.
        self.assertEqual(
            check_guess("eerie", "adieu"),
            YELLOW + BLACK + BLACK + YELLOW + BLACK,
        )

    def test_mixed_greens_and_yellows(self):
        self.assertEqual(
            check_guess("audio", "adieu"),
            GREEN + YELLOW + YELLOW + YELLOW + BLACK,
        )

    def test_green_consumes_letter_before_yellow(self):
        # "abbey" has two 'b's: one is taken by the green at index 2, leaving
        # exactly one for the trailing 'b' to claim as yellow.
        self.assertEqual(
            check_guess("kebab", "abbey"),
            BLACK + YELLOW + GREEN + YELLOW + YELLOW,
        )

    def test_double_letter_with_one_green(self):
        # "spell" has two 'l's: index 4 greens, the leading 'l' yellows.
        # Only one 'e' remains, so the second 'e' in "level" scores black.
        self.assertEqual(
            check_guess("level", "spell"),
            YELLOW + YELLOW + BLACK + BLACK + GREEN,
        )

    def test_result_is_always_five_tiles(self):
        for guess in ("adieu", "eerie", "sport", "kebab", "level"):
            with self.subTest(guess=guess):
                result = check_guess(guess, "adieu")
                self.assertEqual(len(result), 5)
                self.assertTrue(set(result) <= {GREEN, YELLOW, BLACK})


class WordListTests(unittest.TestCase):
    """Every entry in the word list files must be five lowercase letters."""

    def assert_word_file_is_clean(self, path):
        words = path.read_text(encoding="utf-8").splitlines()
        self.assertTrue(words, f"{path.name} is empty")
        for line_no, word in enumerate(words, start=1):
            with self.subTest(file=path.name, line=line_no, word=word):
                self.assertEqual(len(word), 5, "must be 5 characters")
                self.assertTrue(word.isalpha(), "must be letters only")
                self.assertEqual(word, word.lower(), "must be lowercase")

    def test_word_list_entries_are_five_lowercase_letters(self):
        self.assert_word_file_is_clean(PROJECT_DIR / "word_list.txt")

    def test_answers_entries_are_five_lowercase_letters(self):
        answers = PROJECT_DIR / "answers.txt"
        if not answers.exists():
            self.skipTest("answers.txt does not exist yet (REVIEW.md #10)")
        self.assert_word_file_is_clean(answers)

    def test_loaded_guesses_match_the_file(self):
        words = (PROJECT_DIR / "word_list.txt").read_text(encoding="utf-8").split()
        self.assertEqual(set(wordle.list_valid_guesses), set(words))


if __name__ == "__main__":
    unittest.main()
