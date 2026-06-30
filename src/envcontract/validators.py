"""Validate a parsed .env against an EnvSchema and produce findings."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from .parser import ParsedEnv
from .schema import EnvSchema, VariableRule

_URL_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s]+$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_BOOL_VALUES = {"true", "false", "1", "0", "yes", "no", "on", "off"}


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


def _fmt(n: float) -> str:
    """Render 65535.0 as '65535' but keep 3.5 as '3.5'."""
    return str(int(n)) if float(n).is_integer() else str(n)


@dataclass(frozen=True)
class Finding:
    severity: Severity
    key: str
    message: str
    line_no: int | None = None


def _check_type(value: str, rule: VariableRule) -> str | None:
    """Return an error message if the value doesn't match the declared type."""
    t = rule.type
    if t == "int":
        try:
            int(value)
        except ValueError:
            return f"expected an integer, got '{value}'"
    elif t == "float":
        try:
            float(value)
        except ValueError:
            return f"expected a number, got '{value}'"
    elif t == "bool":
        if value.lower() not in _BOOL_VALUES:
            return f"expected a boolean (true/false), got '{value}'"
    elif t == "url":
        if not _URL_RE.match(value):
            return f"expected a URL (scheme://...), got '{value}'"
    elif t == "email":
        if not _EMAIL_RE.match(value):
            return f"expected an email address, got '{value}'"
    elif t == "enum":
        if rule.values and value not in rule.values:
            return f"must be one of {rule.values}, got '{value}'"
    return None


def _check_rules(value: str, rule: VariableRule) -> list[str]:
    msgs: list[str] = []
    if rule.pattern is not None and not re.search(rule.pattern, value):
        msgs.append(f"does not match required pattern /{rule.pattern}/")
    if rule.min is not None or rule.max is not None:
        if rule.type in {"int", "float"}:
            try:
                num = float(value)
                if rule.min is not None and num < rule.min:
                    msgs.append(f"must be >= {_fmt(rule.min)}")
                if rule.max is not None and num > rule.max:
                    msgs.append(f"must be <= {_fmt(rule.max)}")
            except ValueError:
                pass  # type error already reported
        else:
            length = len(value)
            if rule.min is not None and length < rule.min:
                msgs.append(f"length must be >= {_fmt(rule.min)}")
            if rule.max is not None and length > rule.max:
                msgs.append(f"length must be <= {_fmt(rule.max)}")
    return msgs


def validate(parsed: ParsedEnv, schema: EnvSchema) -> list[Finding]:
    findings: list[Finding] = []
    env = parsed.as_dict()
    line_of = {e.key: e.line_no for e in parsed.entries}

    for err in parsed.errors:
        findings.append(Finding(Severity.WARNING, "(parse)", err.message, err.line_no))
    for dup in parsed.duplicate_keys:
        findings.append(
            Finding(Severity.WARNING, dup, "defined more than once (last value wins)", line_of.get(dup))
        )

    for key, rule in schema.variables.items():
        present = key in env
        if not present:
            if rule.required and rule.default is None:
                findings.append(Finding(Severity.ERROR, key, "required but missing"))
            continue

        value = env[key]
        if value == "" and rule.required:
            findings.append(Finding(Severity.ERROR, key, "required but empty", line_of.get(key)))
            continue

        type_err = _check_type(value, rule)
        if type_err:
            findings.append(Finding(Severity.ERROR, key, type_err, line_of.get(key)))
            continue

        for msg in _check_rules(value, rule):
            findings.append(Finding(Severity.ERROR, key, msg, line_of.get(key)))

    for key in env:
        if key not in schema.variables:
            findings.append(
                Finding(Severity.WARNING, key, "present in .env but not declared in schema", line_of.get(key))
            )

    return findings


def has_errors(findings: list[Finding]) -> bool:
    return any(f.severity is Severity.ERROR for f in findings)
