"""Tests for wordle.py — stdlib unittest, no third-party dependencies.

Run from anywhere:  python -m unittest test_wordle
"""

import errno
import os
import tempfile
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
        path = PROJECT_DIR / "word_list.txt"
        words = path.read_text(encoding="utf-8").split()
        self.assertEqual(set(wordle.load_words(path)), set(words))


class LoadWordsMissingFileTests(unittest.TestCase):
    """`load_words` must surface a missing word list as FileNotFoundError.

    The handler at wordle.py:86 prints `errno`, `strerror` and `filename` off
    the exception, so these tests pin both the exception type and the
    attributes that message depends on.
    """

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_dir = Path(tmp.name)

    def test_missing_file_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            wordle.load_words(self.tmp_dir / "no_such_list.txt")

    def test_exception_carries_the_details_the_handler_prints(self):
        missing = self.tmp_dir / "no_such_list.txt"
        with self.assertRaises(FileNotFoundError) as ctx:
            wordle.load_words(missing)
        self.assertEqual(ctx.exception.errno, errno.ENOENT)
        self.assertEqual(Path(ctx.exception.filename), missing)
        self.assertTrue(ctx.exception.strerror, "strerror must not be empty")

    def test_missing_relative_name_raises_file_not_found(self):
        # Relative names are joined onto PROJECT_DIR inside load_words.
        with self.assertRaises(FileNotFoundError):
            wordle.load_words("definitely_not_a_word_list.txt")

    def test_missing_parent_directory_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            wordle.load_words(self.tmp_dir / "nested" / "word_list.txt")

    def test_string_path_raises_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            wordle.load_words(str(self.tmp_dir / "no_such_list.txt"))

    def test_directory_is_a_different_failure_than_a_missing_file(self):
        # The path exists, so this must not masquerade as FileNotFoundError.
        # POSIX raises IsADirectoryError here, Windows raises PermissionError.
        with self.assertRaises((IsADirectoryError, PermissionError)):
            wordle.load_words(self.tmp_dir)

    def test_existing_file_loads_without_error(self):
        # Control: proves the cases above fail because the file is absent, not
        # because load_words raises for every path handed to it.
        path = self.tmp_dir / "word_list.txt"
        path.write_text("crane\nadieu\n", encoding="utf-8")
        self.assertEqual(wordle.load_words(path), {"adieu", "crane"})

    def test_relative_name_resolves_against_project_dir_not_cwd(self):
        # Regression for REVIEW.md #4: the real word list must still be found
        # when the game is launched from another directory.
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.tmp_dir)
        self.assertTrue(wordle.load_words("word_list.txt"))


class TestSeeds(unittest.TestCase):
    def test_same_seed(self):
        """Same seed should produce the same answer."""
        answer1 = wordle.get_answer(seed="42")
        answer2 = wordle.get_answer(seed="42")
        self.assertEqual(answer1, answer2)

    def test_different_seeds_produce_different_answers(self):
        """Different seeds should produce different answers (most of the time)."""
        answer1 = wordle.get_answer(seed="42")
        answer2 = wordle.get_answer(seed="123")
        # Very unlikely for different seeds to produce the same answer
        self.assertNotEqual(answer1, answer2)

    def test_seed_consistency_across_multiple_runs(self):
        """Verify seed consistency with multiple runs."""
        seed = "999"
        expected = wordle.get_answer(seed=seed)
        for _ in range(3):
            self.assertEqual(wordle.get_answer(seed=seed), expected)

if __name__ == "__main__":
    unittest.main()
