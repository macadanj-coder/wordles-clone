"""Tests for wordle.py — stdlib unittest, no third-party dependencies.

Run from anywhere:  python -m unittest test_wordle
"""

import contextlib
import errno
import io
import os
import random
import tempfile
import unittest
from pathlib import Path
from unittest import mock

PROJECT_DIR = Path(__file__).resolve().parent

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
        self.assert_word_file_is_clean(PROJECT_DIR / wordle.GUESSES_FILE)

    def test_answers_entries_are_five_lowercase_letters(self):
        self.assert_word_file_is_clean(PROJECT_DIR / wordle.ANSWERS_FILE)

    def test_every_answer_is_a_guessable_word(self):
        # REVIEW.md R16: an answer missing from the guess list would be
        # unguessable — the player would be told "Not a valid word" for typing
        # the correct answer.
        answers = wordle.load_words(wordle.ANSWERS_FILE)
        guesses = wordle.load_words(wordle.GUESSES_FILE)
        self.assertTrue(
            answers <= guesses,
            f"answers missing from the guess list: {sorted(answers - guesses)[:10]}",
        )

    def test_loaded_guesses_match_the_file(self):
        path = PROJECT_DIR / "word_list.txt"
        words = path.read_text(encoding="utf-8").split()
        self.assertEqual(set(wordle.load_words(path)), set(words))


class LoadWordsMissingFileTests(unittest.TestCase):
    """`load_words` must surface a missing word list as FileNotFoundError.

    The handler prints `e.filename`, so these tests pin both the exception type
    and the attributes that message depends on.
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
    @classmethod
    def setUpClass(cls):
        # Load once and pass it in, so no test pays for re-reading the file.
        cls.answers = wordle.load_words(wordle.ANSWERS_FILE)

    def test_same_seed(self):
        """Same seed should produce the same answer."""
        answer1 = wordle.get_answer(self.answers, seed="42")
        answer2 = wordle.get_answer(self.answers, seed="42")
        self.assertEqual(answer1, answer2)

    def test_different_seeds_produce_different_answers(self):
        """Different seeds should produce different answers (most of the time)."""
        answer1 = wordle.get_answer(self.answers, seed="42")
        answer2 = wordle.get_answer(self.answers, seed="123")
        # Very unlikely for different seeds to produce the same answer
        self.assertNotEqual(answer1, answer2)

    def test_seed_consistency_across_multiple_runs(self):
        """Verify seed consistency with multiple runs."""
        seed = "999"
        expected = wordle.get_answer(self.answers, seed=seed)
        for _ in range(3):
            self.assertEqual(wordle.get_answer(self.answers, seed=seed), expected)

    def test_seed_zero_is_honoured(self):
        # Regression for REVIEW.md R5: `if seed:` treated 0 as "no seed".
        first = wordle.get_answer(self.answers, seed=0)
        for _ in range(3):
            self.assertEqual(wordle.get_answer(self.answers, seed=0), first)

    def test_does_not_disturb_the_global_random_stream(self):
        # Regression for REVIEW.md R6: get_answer used to call random.seed().
        random.seed(1234)
        expected = [random.random() for _ in range(3)]
        random.seed(1234)
        wordle.get_answer(self.answers, seed="42")
        self.assertEqual([random.random() for _ in range(3)], expected)

    def test_default_answers_come_from_the_bundled_list(self):
        self.assertIn(wordle.get_answer(seed="42"), self.answers)


class PlayLoopTests(unittest.TestCase):
    """REVIEW.md R15: the game loop itself, with input injected."""

    VALID = {"adieu", "crane", "spell", "level", "sport", "kebab", "abbey"}

    def play(self, answer, guesses):
        """Run one game on a scripted guess sequence; return (rows, stdout)."""
        scripted = iter(guesses)
        self.calls = 0

        def read_guess(valid_guesses, guessed_words):
            self.calls += 1
            return next(scripted)

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rows = wordle.play(answer, self.VALID, read_guess)
        return rows, out.getvalue()

    def test_win_on_the_sixth_guess_does_not_print_the_loss_message(self):
        # Regression for REVIEW.md #2.
        wrong = ["crane", "spell", "level", "sport", "kebab"]
        rows, out = self.play("adieu", wrong + ["adieu"])
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[-1], GREEN * 5)
        self.assertIn("Splendid!", out)
        self.assertNotIn("Better luck next time!", out)
        self.assertNotIn("Answer is", out)

    def test_loss_prints_the_grid_exactly_once_at_the_end(self):
        # Regression for REVIEW.md R1: the grid used to be printed twice.
        guesses = ["crane", "spell", "level", "sport", "kebab", "abbey"]
        rows, out = self.play("adieu", guesses)
        self.assertEqual(len(rows), 6)
        grid = "\n".join(rows)
        self.assertEqual(out.count(grid), 1)
        self.assertIn("Answer is adieu", out)
        self.assertIn("Better luck next time!", out)
        self.assertNotIn("Splendid!", out)

    def test_win_stops_reading_guesses(self):
        rows, out = self.play("adieu", ["crane", "spell", "adieu", "sport"])
        self.assertEqual(self.calls, 3)
        self.assertEqual(len(rows), 3)
        self.assertIn("Splendid!", out)

    def test_guessed_words_are_local_to_each_game(self):
        # Regression for REVIEW.md R3: history used to leak between games via a
        # module global, so a second game rejected the first game's guesses.
        seen = []

        def read_guess(valid_guesses, guessed_words):
            seen.append(list(guessed_words))
            return "adieu"

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            wordle.play("adieu", self.VALID, read_guess)
            wordle.play("adieu", self.VALID, read_guess)
        self.assertEqual(seen, [[], []])


class GetInputTests(unittest.TestCase):
    """Validation re-prompts without consuming a guess (REVIEW.md #12, R10)."""

    VALID = {"adieu", "crane"}

    def get_input(self, typed, guessed_words=()):
        scripted = iter(typed)
        out = io.StringIO()
        with mock.patch("builtins.input", lambda _prompt="": next(scripted)):
            with contextlib.redirect_stdout(out):
                guess = wordle.get_input(self.VALID, list(guessed_words))
        return guess, out.getvalue()

    def test_rejected_then_accepted(self):
        guess, out = self.get_input(["toolong", "zzzzz", "crane", "adieu"])
        self.assertEqual(guess, "crane")
        self.assertIn(f"Guesses must be {wordle.WORD_LENGTH} letters long", out)
        self.assertIn("Not a valid word", out)

    def test_already_guessed_is_rejected(self):
        guess, out = self.get_input(["crane", "adieu"], guessed_words=["crane"])
        self.assertEqual(guess, "adieu")
        self.assertIn("Already guessed", out)

    def test_input_is_normalized(self):
        guess, _ = self.get_input(["  CrAnE \n"])
        self.assertEqual(guess, "crane")

    def test_only_the_accepted_guess_is_echoed(self):
        # REVIEW.md #12: rejected input must not be echoed back.
        _, out = self.get_input(["zzzzz", "crane"])
        self.assertNotIn("Your guess, zzzzz", out)
        self.assertIn("Your guess, crane", out)


if __name__ == "__main__":
    unittest.main()
