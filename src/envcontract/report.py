"""Render validation findings as human-friendly terminal output or JSON.

Invariant: this module never prints a secret value. Findings carry messages,
not raw values, and any value echoed elsewhere is masked first.
"""

from __future__ import annotations

import json

from rich.console import Console
from rich.table import Table

from .validators import Finding, Severity

_ICON = {Severity.ERROR: "[red]✗[/red]", Severity.WARNING: "[yellow]![/yellow]"}


def render_human(findings: list[Finding], console: Console | None = None) -> None:
    console = console or Console()
    errors = [f for f in findings if f.severity is Severity.ERROR]
    warnings = [f for f in findings if f.severity is Severity.WARNING]

    if not findings:
        console.print("[bold green]✓ All variables valid.[/bold green] Your .env matches the schema.")
        return

    table = Table(show_header=True, header_style="bold", expand=False)
    table.add_column("")
    table.add_column("Variable", style="cyan", no_wrap=True)
    table.add_column("Line", justify="right", style="dim")
    table.add_column("Issue")
    for f in findings:
        table.add_row(_ICON[f.severity], f.key, str(f.line_no or "-"), f.message)
    console.print(table)

    parts = []
    if errors:
        parts.append(f"[red]{len(errors)} error(s)[/red]")
    if warnings:
        parts.append(f"[yellow]{len(warnings)} warning(s)[/yellow]")
    console.print("  ".join(parts))


def build_json(findings: list[Finding]) -> dict:
    return {
        "ok": not any(f.severity is Severity.ERROR for f in findings),
        "errors": sum(1 for f in findings if f.severity is Severity.ERROR),
        "warnings": sum(1 for f in findings if f.severity is Severity.WARNING),
        "findings": [
            {"severity": f.severity.value, "key": f.key, "line": f.line_no, "message": f.message}
            for f in findings
        ],
    }


def render_json(findings: list[Finding]) -> str:
    return json.dumps(build_json(findings), indent=2)
