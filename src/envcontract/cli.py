"""Command-line entry point for envcontract."""

from __future__ import annotations

import sys
from pathlib import Path

import click
from rich.console import Console

from . import __version__
from .drift import compute_drift
from .generate import render_schema_yaml
from .guard import scan_files
from .parser import parse_file
from .report import render_human, render_json
from .schema import EnvSchema, SchemaError
from .validators import validate

_ENV_OPT = dict(default=".env", show_default=True, help="Path to the .env file.")
_SCHEMA_OPT = dict(default=".env.schema", show_default=True, help="Path to the .env.schema file.")


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, "-V", "--version", prog_name="envcontract")
def cli() -> None:
    """envcontract - the contract for your .env.

    Validate your .env against a committed schema, catch team drift, and
    never commit a secret. 100% local: your values never leave your machine.
    """


def _load_schema_or_exit(schema_path: str, console: Console) -> EnvSchema:
    try:
        return EnvSchema.from_file(schema_path)
    except SchemaError as exc:
        console.print(f"[red]X[/red] {exc}")
        sys.exit(2)


@cli.command()
@click.option("--env", "env_path", **_ENV_OPT)
@click.option("--schema", "schema_path", **_SCHEMA_OPT)
@click.option("--force", is_flag=True, help="Overwrite an existing schema file.")
def init(env_path: str, schema_path: str, force: bool) -> None:
    """Generate a .env.schema from an existing .env (values stripped)."""
    console = Console()
    if not Path(env_path).exists():
        Console(stderr=True).print(f"[red]X[/red] env file not found: {env_path}")
        sys.exit(2)
    if Path(schema_path).exists() and not force:
        Console(stderr=True).print(
            f"[yellow]![/yellow] {schema_path} already exists. Use --force to overwrite."
        )
        sys.exit(2)

    yaml_text = render_schema_yaml(parse_file(env_path))
    Path(schema_path).write_text(yaml_text, encoding="utf-8")
    n = yaml_text.count("\n    type:")
    console.print(f"[green]+[/green] Wrote {schema_path} with {n} variable(s). No values were copied.")


@cli.command()
@click.option("--env", "env_path", **_ENV_OPT)
@click.option("--schema", "schema_path", **_SCHEMA_OPT)
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON (for CI).")
def check(env_path: str, schema_path: str, as_json: bool) -> None:
    """Validate a .env against the schema (types, rules, required keys)."""
    err_console = Console(stderr=True)
    if not Path(env_path).exists():
        err_console.print(f"[red]X[/red] env file not found: {env_path}")
        sys.exit(2)
    schema = _load_schema_or_exit(schema_path, err_console)

    findings = validate(parse_file(env_path), schema)
    if as_json:
        click.echo(render_json(findings))
    else:
        render_human(findings, Console())
    sys.exit(1 if any(f.severity.value == "error" for f in findings) else 0)


@cli.command()
@click.option("--env", "env_path", **_ENV_OPT)
@click.option("--schema", "schema_path", **_SCHEMA_OPT)
def diff(env_path: str, schema_path: str) -> None:
    """Show what your local .env has vs. the schema (and vice versa)."""
    console = Console()
    err_console = Console(stderr=True)
    if not Path(env_path).exists():
        err_console.print(f"[red]X[/red] env file not found: {env_path}")
        sys.exit(2)
    schema = _load_schema_or_exit(schema_path, err_console)

    d = compute_drift(parse_file(env_path), schema)
    if not d.has_drift:
        console.print(f"[green]+[/green] In sync: {len(d.in_sync)} variable(s) match the schema.")
        sys.exit(0)

    if d.missing_locally:
        console.print("[red]Missing from your .env (declared in schema):[/red]")
        for k in d.missing_locally:
            console.print(f"  [red]-[/red] {k}")
    if d.not_in_schema:
        console.print("[yellow]In your .env but not in the schema:[/yellow]")
        for k in d.not_in_schema:
            console.print(f"  [yellow]+[/yellow] {k}")
    sys.exit(1)


@cli.command()
@click.argument("files", nargs=-1)
@click.option("--schema", "schema_path", **_SCHEMA_OPT)
def guard(files: tuple[str, ...], schema_path: str) -> None:
    """Pre-commit hook: block committing real values for secret keys."""
    console = Console(stderr=True)
    schema = None
    if Path(schema_path).exists():
        try:
            schema = EnvSchema.from_file(schema_path)
        except SchemaError:
            schema = None

    violations = scan_files(list(files), schema)
    if not violations:
        sys.exit(0)

    console.print("[red]X envcontract: blocked commit - real secret values detected:[/red]")
    for v in violations:
        loc = f"{v.file}:{v.line_no}" if v.line_no else v.file
        console.print(f"  [red]-[/red] {v.key}  ({loc})")
    console.print("\nRemove these values (or move them to a git-ignored .env) before committing.")
    sys.exit(1)


if __name__ == "__main__":
    cli()
