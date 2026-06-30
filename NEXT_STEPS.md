# envcontract — Launch Checklist & Next Steps

Status: code complete (v0.1.0), 29 tests passing, wheel + sdist built.
What's left is **verify locally → publish to GitHub → publish to PyPI → launch.**

---

## Step 1 — Verify it works on your machine (5 min)

Open the VS Code integrated terminal in the project root (the folder with `pyproject.toml`).

```bash
# (recommended) create a clean virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
# source .venv/bin/activate

pip install -e ".[dev]"

pytest -q              # expect: 29 passed
ruff check .           # expect: All checks passed!
envcontract --help         # should list init / check / diff / guard
```

If `pytest` shows 29 passed, the project transferred intact. ✅

### Smoke-test the actual commands

```bash
mkdir demo && cd demo
printf 'DATABASE_URL=postgres://localhost/db\nPORT=8080\nSTRIPE_KEY=sk_live_abc123\n' > .env

envcontract init           # creates .env.schema (values stripped, STRIPE_KEY flagged secret)
type .env.schema       # Windows (use `cat` on macOS/Linux)
envcontract check          # should pass
envcontract guard .env     # should BLOCK (real secret in .env)
cd .. 
```

---

## Step 2 — Fix the placeholders (2 min)

Before publishing, replace these with your real details:

- **`pyproject.toml`** → `Homepage` / `Issues` URLs currently use `github.com/hamza/envcontract`.
- **`README.md`** → the pre-commit example uses `https://github.com/hamzamansoorch/envcontract`. 
- **`LICENSE`** → confirm the copyright name/year.
- **`CONTRIBUTING.md`** → the clone URL uses `<you>`.


---

## Step 3 — Confirm the name is still free (2 min)

```bash
pip index versions envcontract      # "not found" = available
```

Also check `https://pypi.org/project/envcontract/` and `https://github.com/hamzamansoorch/envcontract` in a browser.
If taken, pick a fallback (`envguard`, `envschema`, `dotcheck`) and rename in `pyproject.toml` (`name =`) and the `[project.scripts]` entry.

---

## Step 4 — Put it on GitHub (5 min)

```bash
git init
git add .
git commit -m "envcontract v0.1.0 — validate .env, catch drift, guard secrets"
git branch -M main
# create an empty repo named 'envcontract' on github.com first, then:
git remote add origin https://github.com/hamzamansoorch/envcontract.git
git push -u origin main
```

Your `.gitignore` already excludes real `.env` files and build artifacts. Double-check no `.env` got committed: `git ls-files | findstr .env` (should only show `.env.schema.example`).

After pushing, the GitHub Actions CI (`.github/workflows/ci.yml`) runs automatically on Linux/macOS/Windows across Python 3.10–3.12.

---

## Step 5 — Publish to PyPI (10 min)

First test on **TestPyPI** so you don't waste the real name on a mistake.

```bash
pip install build twine
python -m build                       # rebuilds dist/ (wheel + sdist)

# 5a. Test upload
twine upload --repository testpypi dist/*
pip install --index-url https://test.pypi.org/simple/ envcontract   # try it in a fresh venv

# 5b. Real upload (once happy)
twine upload dist/*
```

You'll need a PyPI account + an API token (Account settings → API tokens). Use `__token__` as the username and the token as the password.

---

## Step 6 — Tag a release (2 min)

```bash
git tag v0.1.0
git push origin v0.1.0
```

Then on GitHub: Releases → Draft a new release → pick the tag → paste highlights from the README.
This is also the `rev:` users reference in the pre-commit example.

---

## How END USERS will install & use it (this is your "it works" demo)

Once it's on PyPI, anyone can do:

```bash
pipx install envcontract            # or: pip install envcontract

cd their-project
envcontract init                    # generate .env.schema from their .env
git add .env.schema             # commit the contract (no secrets in it)

envcontract check                   # validate their .env  → exit 1 if broken
envcontract diff                    # see what their .env is missing vs the schema
```

**As a pre-commit hook** (their `.pre-commit-config.yaml`):

```yaml
repos:
  - repo: https://github.com/<you>/envcontract
    rev: v0.1.0
    hooks:
      - id: envcontract-guard       # blocks committing real secret values
```

**In CI** (their GitHub Actions):

```yaml
- run: pip install envcontract
- run: envcontract check --json     # fails the build if .env is invalid
```

---

## Step 7 — Launch & get stars

- **Show HN**: title like "Show HN: envcontract – a local-only contract for your .env (validate, drift, secret guard)". Lead with the privacy promise.
- **r/Python and r/devops**: short post, link the repo, ask for feedback.
- **Add a demo GIF** to the top of the README (use asciinema + agg, or a screen recorder). A visual demo dramatically increases stars.
- Pin good first issues so contributors have an entry point.

---

## What's left to BUILD (optional, post-launch)

- Demo GIF/asciinema in README (high impact, do this before Show HN).
- `.vscode/settings.json` for contributors (interpreter, pytest, ruff).
- Multi-environment support (`.env.development`, `.env.production` against one schema).
- VS Code extension for inline schema validation.
- `envcontract sync` to interactively update a local `.env` to match schema additions.

---

## Quick status

| Item | State |
|------|-------|
| 4 commands (init/check/diff/guard) | ✅ done |
| 29 tests + lint | ✅ passing |
| Privacy invariants (no-network, no secret printing) | ✅ enforced by tests |
| README / CONTRIBUTING / LICENSE / CI / pre-commit | ✅ done |
| Wheel + sdist built | ✅ in `dist/` |
| Placeholders replaced | ⬜ you |
| GitHub repo | ⬜ you |
| PyPI publish | ⬜ you |
| Demo GIF + launch posts | ⬜ optional |
