"""Parse .env files into ordered key/value entries with line numbers.

Aims to be compatible with python-dotenv conventions: ``export`` prefixes,
single/double quotes, inline comments on unquoted values, and blank/comment
lines. We deliberately keep this small and predictable.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EnvEntry:
    """A single ``KEY=value`` line from a .env file."""

    key: str
    value: str
    line_no: int
    quoted: bool = False


@dataclass(frozen=True)
class ParseError:
    """A malformed line we could not interpret as a key/value pair."""

    line_no: int
    raw: str
    message: str


@dataclass
class ParsedEnv:
    entries: list[EnvEntry]
    errors: list[ParseError]

    def as_dict(self) -> dict[str, str]:
        """Later entries win, matching how shells/dotenv resolve duplicates."""
        return {e.key: e.value for e in self.entries}

    @property
    def duplicate_keys(self) -> list[str]:
        seen: set[str] = set()
        dupes: list[str] = []
        for e in self.entries:
            if e.key in seen and e.key not in dupes:
                dupes.append(e.key)
            seen.add(e.key)
        return dupes


def _strip_inline_comment(value: str) -> str:
    """Remove an unquoted trailing ``# comment`` (must be preceded by space)."""
    result = []
    for i, ch in enumerate(value):
        if ch == "#" and (i == 0 or value[i - 1].isspace()):
            break
        result.append(ch)
    return "".join(result).strip()


def _parse_value(raw: str) -> tuple[str, bool]:
    """Return (value, quoted). Handles single/double quotes and inline comments."""
    raw = raw.strip()
    if not raw:
        return "", False
    if raw[0] in {'"', "'"}:
        quote = raw[0]
        end = raw.find(quote, 1)
        if end != -1:
            inner = raw[1:end]
            if quote == '"':
                inner = inner.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
            return inner, True
        # Unterminated quote: treat the rest literally.
        return raw[1:], True
    return _strip_inline_comment(raw), False


def parse_text(text: str) -> ParsedEnv:
    entries: list[EnvEntry] = []
    errors: list[ParseError] = []

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[len("export ") :].lstrip()

        if "=" not in line:
            errors.append(ParseError(line_no, raw_line, "missing '=' (not a KEY=value line)"))
            continue

        key, _, value_part = line.partition("=")
        key = key.strip()
        if not key:
            errors.append(ParseError(line_no, raw_line, "empty key before '='"))
            continue
        if not all(c.isalnum() or c == "_" for c in key):
            errors.append(
                ParseError(line_no, raw_line, f"invalid key name '{key}' (use A-Z, 0-9, _)")
            )
            continue

        value, quoted = _parse_value(value_part)
        entries.append(EnvEntry(key=key, value=value, line_no=line_no, quoted=quoted))

    return ParsedEnv(entries=entries, errors=errors)


def parse_file(path: str | Path) -> ParsedEnv:
    return parse_text(Path(path).read_text(encoding="utf-8"))
