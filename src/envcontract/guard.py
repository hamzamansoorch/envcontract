"""Detect real secret values about to be committed.

Narrow by design: we only flag keys the schema marks ``secret: true`` that
carry a real (non-placeholder, non-empty) value. We never print the value.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .parser import parse_file
from .schema import EnvSchema
from .secrets import looks_like_secret_key

# Common placeholders that are safe to commit.
_PLACEHOLDERS = {
    "", "changeme", "change_me", "your_value_here", "xxx", "todo",
    "placeholder", "example", "secret", "<your-key>", "...",
}


@dataclass
class Violation:
    file: str
    key: str
    line_no: int | None


def _is_real_secret_value(value: str) -> bool:
    v = value.strip().lower()
    if v in _PLACEHOLDERS:
        return False
    return len(value.strip()) >= 6


def scan_files(files: list[str], schema: EnvSchema | None) -> list[Violation]:
    """Return violations: secret-marked keys carrying a real value in staged files."""
    secret_keys = {k for k, r in schema.variables.items() if r.secret} if schema else set()
    violations: list[Violation] = []

    for f in files:
        path = Path(f)
        if not path.exists() or not path.is_file():
            continue
        try:
            parsed = parse_file(path)
        except (UnicodeDecodeError, OSError):
            continue
        for entry in parsed.entries:
            is_secret = entry.key in secret_keys or looks_like_secret_key(entry.key)
            if is_secret and _is_real_secret_value(entry.value):
                violations.append(Violation(file=f, key=entry.key, line_no=entry.line_no))
    return violations
