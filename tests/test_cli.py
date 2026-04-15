"""Smoke tests for CLI commands."""

from click.testing import CliRunner

from chaos_agents.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Chaos Agents" in result.output


def test_cli_scan_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["scan", "--help"])
    assert result.exit_code == 0
    assert "target" in result.output.lower()


def test_cli_run_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "--help"])
    assert result.exit_code == 0


def test_cli_demo_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["demo", "--help"])
    assert result.exit_code == 0
