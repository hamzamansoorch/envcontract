# envcontract — Full Setup & Launch Checklist

Follow these in order. Commands assume **Windows + VS Code terminal** (PowerShell).
For macOS/Linux, swap the venv-activate line and use `cat` instead of `type`.

Project status: code complete (v0.1.0), 29 tests passing, wheel + sdist built.

---

## ✅ Step 0 — Clean the folder (1 min)

In the `envcontract` folder, delete three leftover dirs the build tool left
(they're safe but tidier gone): `.git`, `.pytest_cache`, `.ruff_cache`.

PowerShell:
```powershell
Remove-Item -Recurse -Force .git, .pytest_cache, .ruff_cache -ErrorAction SilentlyContinue
```

---

## ✅ Step 1 — Verify it runs on your machine (5 min)

Open the VS Code terminal in the project root (folder with `pyproject.toml`).

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"

pytest -q            # EXPECT: 29 passed
ruff check .         # EXPECT: All checks passed!
envcontract --help   # should list: init  check  diff  guard
```

If `pytest` shows **29 passed**, the project is intact. ✅

---

## ✅ Step 2 — Try the 4 commands yourself (3 min)

```powershell
mkdir demo
cd demo
"DATABASE_URL=postgres://localhost/db`nPORT=8080`nSTRIPE_KEY=sk_live_abc123" | Out-File -Encoding ascii .env

envcontract init        # creates .env.schema (values stripped, STRIPE_KEY flagged secret)
type .env.schema        # look at the generated contract
envcontract check       # validates .env  -> should pass
envcontract diff        # compares .env vs schema
envcontract guard .env  # should BLOCK (real secret in .env) and exit 1
cd ..
```

---

## ✅ Step 3 — Replace placeholders (2 min)

Use VS Code search (Ctrl+Shift+F) and replace in these files:

- `pyproject.toml` → change `github.com/hamzamansoorch/envcontract` → `github.com/hamzamansoorch/envcontract` (2 URLs)
- `README.md` → replace `hamzamansoorch` in the pre-commit example
- `CONTRIBUTING.md` → replace `hamzamansoorch` in the clone URL
- `LICENSE` → confirm your name + year

Search for `hamza` and `hamzamansoorch` to catch them all.

---

## ✅ Step 4 — Confirm the name is still free (1 min)

```powershell
pip index versions envcontract
```
"not found / no matching distribution" = available. Also open
`https://pypi.org/project/envcontract/` in a browser (404 = free).
If taken, fall back to `dotcontract` or `envpledge` (rename `name=` and the
`[project.scripts]` line in `pyproject.toml`, plus the package folder `src/<name>`).

---

## ✅ Step 5 — Push to GitHub (5 min)

Create an empty repo named `envcontract` on github.com first (no README), then:

```powershell
git init
git add .
git commit -m "envcontract v0.1.0 - validate .env, catch drift, guard secrets"
git branch -M main
git remote add origin https://github.com/hamzamansoorch/envcontract.git
git push -u origin main
```

Safety check — make sure no real `.env` got committed (only the example should appear):
```powershell
git ls-files | findstr .env
```
Expected output: only `.env.schema.example`.

After the push, GitHub Actions CI runs automatically (Linux/macOS/Windows, Py 3.10-3.12).

---

## ✅ Step 6 — Publish to PyPI (10 min)

Make a PyPI account + an API token (pypi.org → Account settings → API tokens).

```powershell
pip install build twine
python -m build                  # rebuilds dist\ (wheel + sdist)
```

Test on TestPyPI first (so a mistake doesn't burn the real name):
```powershell
twine upload --repository testpypi dist/*
# then in a fresh venv:
pip install --index-url https://test.pypi.org/simple/ envcontract
```

When happy, the real upload:
```powershell
twine upload dist/*
```
Username: `__token__`   Password: your API token (paste the whole `pypi-...` string).

Verify:
```powershell
pip install envcontract
envcontract --version
```

---

## ✅ Step 7 — Tag a release (2 min)

```powershell
git tag v0.1.0
git push origin v0.1.0
```
On GitHub: Releases → Draft new release → choose tag `v0.1.0` → paste README highlights.
(This tag is what pre-commit users reference as `rev:`.)

---

## 🚀 Step 8 — Launch (optional but high impact)

- Add a demo GIF to the top of `README.md` (asciinema, or any screen recorder). Biggest driver of stars.
- Post "Show HN: envcontract — a local-only contract for your .env". Lead with the privacy promise.
- Post to r/Python and r/devops. Short, link the repo, ask for feedback.
- Add a few "good first issue" labels so contributors have an entry point.

---

## 📦 How END USERS install & use it (after Step 6)

```bash
pipx install envcontract        # or: pip install envcontract

cd their-project
envcontract init                # generate .env.schema from their .env
git add .env.schema             # commit the contract (no secrets inside)

envcontract check               # validate .env  -> exit 1 if broken
envcontract diff                # show what's missing vs the schema
```

Pre-commit hook (their `.pre-commit-config.yaml`):
```yaml
repos:
  - repo: https://github.com/hamzamansoorch/envcontract
    rev: v0.1.0
    hooks:
      - id: envcontract-guard
```

CI (their GitHub Actions):
```yaml
- run: pip install envcontract
- run: envcontract check --json
```

---

## Status summary

| Item | State |
|------|-------|
| 4 commands (init/check/diff/guard) | ✅ done |
| 29 tests + lint clean | ✅ |
| Privacy invariants (no-network, no secret printing) | ✅ enforced by tests |
| Docs / CI / pre-commit / LICENSE | ✅ |
| Wheel + sdist built | ✅ dist\ |
| Replace placeholders | ⬜ you (Step 3) |
| GitHub repo | ⬜ you (Step 5) |
| PyPI publish | ⬜ you (Step 6) |
| Tag + release | ⬜ you (Step 7) |
| Demo GIF + launch | ⬜ optional (Step 8) |
