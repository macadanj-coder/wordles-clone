# Wordles Clone

A Wordle clone in Python — guess a hidden five-letter word in six tries, with
emoji feedback after every guess.

```
Enter your guess: audio
Your guess, audio
🟩🟨🟨🟨⬛
```

- 🟩 right letter, right place
- 🟨 right letter, wrong place
- ⬛ letter not in the word

Guesses are validated against a 14,855-word list (`word_list.txt`); answers are
drawn from the 2,315-word curated list (`answers.txt`), the way the original
game does it — so you never have to guess an obscurity.

## Requirements

Python 3.10+. The CLI itself is pure standard library; the only dependency
(`textual`) is there for the TUI front-end that is still in progress.

## Running

With [uv](https://docs.astral.sh/uv/):

```bash
uv run wordle.py
```

Or with any Python 3.10+ interpreter:

```bash
python wordle.py
```

### Reproducible games

`--seed` picks the answer deterministically — the same seed always yields the
same word, which is handy for testing or for racing a friend on the same puzzle:

```bash
python wordle.py --seed 42
```

Seeding uses a private RNG, so it leaves the global `random` stream alone.

## Tests

Standard-library `unittest`, no third-party dependencies:

```bash
python -m unittest test_wordle
```

Coverage includes the duplicate-letter scoring rules (a guess with two `e`s
against an answer with one may only claim one), the play loop's win/loss exits,
seeding behaviour, and word-list integrity — including that every answer is
itself a valid guess.

## Layout

| File | Purpose |
| --- | --- |
| `game.py` | Core rules: scoring, validation, and the `Game` state object. Renders nothing. |
| `wordle.py` | CLI front-end — prompting, printing, argument parsing. |
| `test_wordle.py` | Test suite. |
| `word_list.txt` | Accepted guesses. |
| `answers.txt` | Answers the game draws from (a strict subset of the guess list). |
| `PLAN.md` | Code-review remediation plan (applied). |
| `TUI_PLAN.md` | Design for the Textual front-end (in progress). |
| `REVIEW.md` | The review that produced `PLAN.md`. |

The split is deliberate: `game.py` holds the rules and the state, `wordle.py`
holds one way of showing them. Validation messages live on `Game` so the CLI and
the planned TUI cannot drift apart on wording.

## Status

The CLI is complete and tested. The Textual TUI described in `TUI_PLAN.md` — a
6×5 tile grid with flip-reveal, an on-screen keyboard tracking letter states,
and toast messages — is not implemented yet; `wordle.py` accepts a `--tui` flag
but currently ignores it.
