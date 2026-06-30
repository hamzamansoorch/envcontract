"""Smoke tests for the CLI skeleton (Phase 1)."""

from click.testing import CliRunner

from envcontract.cli import cli


def test_help_lists_all_commands():
    result = CliRunner().invoke(cli, ["--help"])
    assert result.exit_code == 0
    for command in ("init", "check", "diff", "guard"):
        assert command in result.output


def test_version():
    result = CliRunner().invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output
