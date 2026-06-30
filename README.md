# envcontract

**The contract for your `.env`.** Validate it, catch team drift, and never commit a secret — **100% local, your values never leave your machine.**

[![PyPI version](https://img.shields.io/pypi/v/envcontract.svg)](https://pypi.org/project/envcontract/)
[![Python](https://img.shields.io/pypi/pyversions/envcontract.svg)](https://pypi.org/project/envcontract/)
[![Downloads](https://static.pepy.tech/badge/envcontract)](https://pepy.tech/project/envcontract)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![CI](https://github.com/hamzamansoorch/envcontract/actions/workflows/ci.yml/badge.svg)](https://github.com/hamzamansoorch/envcontract/actions)


---

## Table of contents

- [What is this?](#what-is-this)
- [The problem it solves](#the-problem-it-solves)
- [Install](#install)
- [60-second quick start](#60-second-quick-start)
- [The four commands](#the-four-commands)
- [The schema file explained](#the-schema-file-explained)
- [Using it in CI](#using-it-in-ci)
- [Using it as a pre-commit hook](#using-it-as-a-pre-commit-hook)
- [How it works & the privacy promise](#how-it-works--the-privacy-promise)
- [FAQ](#faq)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## What is this?

Most apps read their settings — database URLs, ports, API keys — from a file called `.env`.
That file is handy but fragile: it holds **secrets**, and **everyone on the team keeps their own copy**.

`envcontract` is a tiny command-line tool that treats your `.env` like it has a **contract**:
a committed file (`.env.schema`) that lists which variables are required and what each should look like —
**without storing any secret values.** It then helps you:

- generate that contract automatically,
- check any `.env` against it,
- spot when your `.env` has fallen out of sync with the team, and
- block secrets from being committed to git by mistake.

It runs entirely on your computer. No account, no server, no telemetry.

## The problem it solves

If you've worked on a team, you've hit these:

1. **"Works on my machine."** A teammate adds a new variable but forgets to tell anyone. Everyone else's app breaks with a confusing error.
2. **Silent typos.** Someone sets `PORT=eighty` instead of `PORT=8080`, and the app crashes deep in startup with no clear reason.
3. **Leaked secrets.** Someone accidentally commits their real `.env` to GitHub, exposing live credentials. This is a genuine security incident and happens constantly.
4. **Stale `.env.example`.** The old habit of keeping a `.env.example` file drifts out of date and was never a real, enforceable spec.

`envcontract` turns the informal "ask a teammate what goes in your .env" into a checked, committed contract.

## Install

Requires Python 3.10 or newer.

```bash
pip install envcontract
```

Or, to keep it isolated from your other Python packages (recommended for command-line tools):

```bash
pipx install envcontract
```

Verify it installed:

```bash
envcontract --help
```

## 60-second quick start

From inside a project that already has a `.env` file:

```bash
# 1. Create the contract from your existing .env (secret VALUES are stripped out)
envcontract init

# 2. Commit the contract so your whole team shares one source of truth
git add .env.schema && git commit -m "Add env contract"

# 3. Anytime, check that a .env is valid
envcontract check

# 4. See what your local .env is missing compared to the contract
envcontract diff
```

That's the whole core loop. Everything below is detail.

## The four commands

### `envcontract init`

Looks at your `.env` and writes a `.env.schema` file. It **infers a type** for each variable,
**flags likely secrets** (names containing KEY, TOKEN, SECRET, PASSWORD, etc.), and **removes every value.**

```bash
$ envcontract init
+ Wrote .env.schema with 6 variable(s). No values were copied.
```

Given this `.env`:

```
DATABASE_URL=postgres://localhost/app
PORT=8080
STRIPE_SECRET_KEY=sk_live_abc123
```

it produces this safe-to-commit `.env.schema`:

```yaml
version: 1
variables:
  DATABASE_URL:
    type: url
    required: true
  PORT:
    type: int
    required: true
  STRIPE_SECRET_KEY:
    type: string
    required: true
    secret: true
```

Options: `--env <path>` (default `.env`), `--schema <path>` (default `.env.schema`), `--force` (overwrite an existing schema).

### `envcontract check`

Compares a `.env` against the schema and reports problems: missing required variables, wrong types, failed patterns, out-of-range numbers, and values not declared in the schema.

```bash
$ envcontract check
┏━━━┳━━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃   ┃ Variable     ┃ Line ┃ Issue                                  ┃
┡━━━╇━━━━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ ✗ │ DATABASE_URL │    1 │ expected a URL (scheme://...)          │
│ ✗ │ PORT         │    2 │ expected an integer, got 'eighty'      │
│ ✗ │ DEBUG        │    - │ required but missing                   │
└───┴──────────────┴──────┴────────────────────────────────────────┘
3 error(s)
```

It exits with code `1` when there are errors and `0` when everything is valid, so it works as a gate in scripts and CI. Add `--json` for machine-readable output.

### `envcontract diff`

Shows the difference between your local `.env` and the committed schema — the fastest way to answer "what changed that I don't have yet?"

```bash
$ envcontract diff
Missing from your .env (declared in schema):
  - REDIS_URL
```

### `envcontract guard`

Scans files for **real values of secret variables** and is meant to run as a pre-commit hook. It blocks the commit if you're about to check in a secret — and it never prints the secret value itself.

```bash
$ envcontract guard .env
X envcontract: blocked commit - real secret values detected:
  - STRIPE_SECRET_KEY  (.env:4)

Remove these values (or move them to a git-ignored .env) before committing.
```

## The schema file explained

`.env.schema` is a small YAML file. Each variable can declare these rules:

| Field | Meaning | Example |
|-------|---------|---------|
| `type` | One of `string`, `int`, `float`, `bool`, `url`, `email`, `enum` | `type: int` |
| `required` | Whether the variable must be present (default `true`) | `required: false` |
| `default` | A default value (its absence is then not an error) | `default: "3000"` |
| `secret` | Marks the value as sensitive; guarded against commits, never printed | `secret: true` |
| `pattern` | A regular expression the value must match | `pattern: "^sk_(test\|live)_"` |
| `min` / `max` | For numbers: value range. For strings: length range | `min: 1` / `max: 65535` |
| `values` | The allowed values for an `enum` | `values: [debug, info, warn, error]` |
| `description` | A human note about the variable | `description: Postgres URL` |

Full example:

```yaml
version: 1
variables:
  DATABASE_URL:
    type: url
    required: true
    secret: true
    description: Postgres connection string.
  PORT:
    type: int
    default: "3000"
    min: 1
    max: 65535
  LOG_LEVEL:
    type: enum
    values: [debug, info, warn, error]
    default: info
  STRIPE_KEY:
    type: string
    required: true
    secret: true
    pattern: "^sk_(test|live)_[A-Za-z0-9]+$"
```

You can hand-edit this file anytime to tighten the rules. A copy of this example ships as `.env.schema.example`.

## Using it in CI

Make your pipeline fail if someone's environment config is invalid. GitHub Actions example:

```yaml
name: env
on: [push, pull_request]
jobs:
  env-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install envcontract
      - run: envcontract check --json
```

## Using it as a pre-commit hook

### Option A — with the [pre-commit](https://pre-commit.com) framework

Add to your project's `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/hamzamansoorch/envcontract
    rev: v0.1.0
    hooks:
      - id: envcontract-guard
```

Then run `pre-commit install` once. Now every commit is checked automatically.

### Option B — plain git hook (no extra tools)

From your project root:

```bash
cat > .git/hooks/pre-commit <<'HOOK'
#!/bin/sh
staged=$(git diff --cached --name-only | grep -E '(^|/)\.env($|\.)' || true)
[ -z "$staged" ] && exit 0
envcontract guard $staged
HOOK
chmod +x .git/hooks/pre-commit
```

Now if you try to `git commit` a file containing a real secret, the commit is blocked.

> Tip: keep your real `.env` in `.gitignore` so it's never committed, and only commit `.env.schema`.

## How it works & the privacy promise

`envcontract` only reads files on your machine and prints to your terminal. It makes **zero network calls** and collects **no telemetry** — there's nothing to phone home to. This is enforced by an automated test that fails the build if any network connection is attempted. Values for variables marked `secret` are never printed in any output, masked or otherwise.

This is intentional and is the core promise of the tool: a thing that touches your secrets must never send them anywhere.

## FAQ

**Does this store or upload my secrets?**
No. It never reads values into anything that leaves your machine, and `.env.schema` contains no values at all.

**Is this a secrets manager like Vault or Doppler?**
No. It doesn't store, encrypt, or distribute secrets. It validates structure and guards commits. Use it alongside whatever secret storage you already have.

**Is it a generic secret scanner like gitleaks?**
No. `guard` is narrow on purpose — it checks the variables your schema marks `secret`, plus obvious secret-looking names. For full repo-wide scanning, keep using gitleaks; envcontract complements it.

**Does it work with any language/framework?**
Yes. It reads plain `.env` files, so it works for Node, Python, Go, Ruby, PHP — anything that uses `.env`.

**Will it change my `.env`?**
Never. It only reads your `.env`. The only file it writes is `.env.schema` (via `init`).

## Troubleshooting

- **`envcontract: command not found`** — your Python scripts folder isn't on PATH. Try `python -m envcontract.cli --help`, or reinstall with `pipx install envcontract`.
- **`schema file not found`** — run `envcontract init` first to create `.env.schema`, or pass `--schema <path>`.
- **`env file not found`** — run the command from your project folder, or pass `--env <path>`.

## Contributing

Contributions are welcome! Please keep the two core principles intact: **zero network** and **never print a secret value**. See [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup and guidelines. Bug reports and feature ideas: open an issue.

## License

MIT — see [LICENSE](LICENSE). Use it freely.
