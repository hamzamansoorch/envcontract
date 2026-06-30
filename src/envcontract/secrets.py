"""Heuristics for identifying secret-ish keys and safely masking values.

Used by `init` (auto-flag secrets), `guard` (detect committed secrets), and
`report` (never print a secret value).
"""

from __future__ import annotations

import re

_SECRET_KEY_PATTERN = re.compile(
    r"(SECRET|TOKEN|PASSWORD|PASSWD|PRIVATE|API[_-]?KEY|ACCESS[_-]?KEY|"
    r"CREDENTIAL|AUTH|CERT|SIGNING|_KEY$|^KEY$)",
    re.IGNORECASE,
)


def looks_like_secret_key(key: str) -> bool:
    """True if a variable name suggests it holds a secret."""
    return bool(_SECRET_KEY_PATTERN.search(key))


def mask(value: str) -> str:
    """Mask a secret value so it never appears in full in any output."""
    if value == "":
        return "(empty)"
    if len(value) <= 4:
        return "****"
    return f"{value[:2]}{'*' * 6}{value[-2:]}"
