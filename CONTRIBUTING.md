# Contributing to envcontract

Thanks for your interest! envcontract aims to stay small, fast, and **100% local**.

## Core principles (please don't break these)

1. **Zero network.** envcontract must never make a network call. There's a test
   (`tests/test_invariants.py`) that fails if any socket is opened.
2. **Never print a secret value.** Output carries keys, line numbers, and
   messages — never raw values for keys marked `secret`.
3. **Small surface area.** We are not a secrets manager and not a generic
   secret scanner. Keep the scope tight.

## Dev setup

```bash
git clone https://github.com/hamzamansoorch/envcontract
cd envcontract
pip install -e ".[dev]"
pytest -q
ruff check .
```

## Adding a new variable type or rule

1. Add the type to `VarType` in `schema.py`.
2. Add validation in `validators.py` (`_check_type` / `_check_rules`).
3. Add inference (if sensible) in `generate.py`.
4. Add tests and update the schema reference in the README.

## Pull requests

Keep PRs focused. Include tests. Run `pytest` and `ruff check .` before pushing.
