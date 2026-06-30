# envcontract

**The contract for your `.env`.** Validate it, catch team drift, and never commit a secret — **100% local, your values never leave your machine.**

> Status: early development (v0.1.0). Built in the open.

## Why

Teammates add an env var and forget to tell anyone. Secrets get committed by accident. `.env.example` drifts out of sync and was never a real schema. `envcontract` fixes this with one committed contract — `.env.schema` — that lists your variables and their rules, but **never their secret values**.

## Install

```bash
pipx install envcontract   # recommended (isolated)
# or
pip install envcontract
```

## Commands

| Command | What it does |
|---------|--------------|
| `envcontract init`  | Generate a `.env.schema` from your existing `.env` (values stripped). |
| `envcontract check` | Validate your `.env` against the schema: missing keys, wrong types, failed rules. |
| `envcontract diff`  | Show what your local `.env` has vs. the schema (catches team drift). |
| `envcontract guard` | Pre-commit hook that blocks committing real values for secret keys. |

## Privacy promise

`envcontract` makes **zero network calls** and has **no telemetry**. It reads files on your machine and prints to your terminal. Nothing else. This is enforced by a test that fails if any network socket is opened.

## License

MIT
