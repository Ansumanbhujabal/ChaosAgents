"""CLI entry point for Chaos Agents."""

from __future__ import annotations

import asyncio
import os

import click
from rich.console import Console

from chaos_agents.config import load_config


@click.group()
@click.version_option(version="0.1.0", prog_name="chaos-agents")
def cli():
    """Chaos Agents — AI Red Team Framework.

    Chaos Monkey for AI Agent Systems. Test prompt injection, memory poisoning,
    tool abuse, RAG poisoning, stress testing, and more.
    """
    pass


@cli.command()
@click.argument("target", type=click.Path(exists=True))
def scan(target: str):
    """Scan a target codebase and produce a ThreatModel."""
    console = Console()
    try:
        config = load_config()
    except ValueError as e:
        console.print(f"[red]Config error: {e}[/red]")
        raise SystemExit(1)

    from chaos_agents.agents.commander import run_scan_only

    console.print(f"[bold]Scanning: {target}[/bold]")
    threat_model = asyncio.run(run_scan_only(config, os.path.abspath(target)))

    console.print(f"\n[green]Scan complete![/green]")
    console.print(f"  Target: {threat_model.target_name}")
    console.print(f"  Domain: {threat_model.domain_context.domain}")
    console.print(f"  Agents: {len(threat_model.agents_found)}")
    console.print(f"  Tools: {len(threat_model.tool_surfaces)}")
    console.print(f"  RAG surfaces: {len(threat_model.rag_surfaces)}")
    console.print(f"  Recommended attacks: {len(threat_model.recommended_attacks)}")

    for rec in threat_model.recommended_attacks:
        console.print(f"    [{rec.severity}] {rec.attack_type} -> {rec.target_component}: {rec.rationale}")


@cli.command()
@click.argument("target", type=click.Path(exists=True))
@click.option("--category", "-c", type=str, default=None, help="Specific attack category to run")
@click.option("--output", "-o", type=str, default="reports", help="Output directory for reports")
def run(target: str, category: str | None, output: str):
    """Run full scan + attack pipeline against a target."""
    console = Console()
    try:
        config = load_config()
    except ValueError as e:
        console.print(f"[red]Config error: {e}[/red]")
        raise SystemExit(1)

    from chaos_agents.agents.commander import run_full_pipeline

    asyncio.run(run_full_pipeline(
        config=config,
        target_path=os.path.abspath(target),
        category=category,
        output_dir=output,
    ))


@cli.command()
@click.option("--output", "-o", type=str, default="reports", help="Output directory for reports")
def demo(output: str):
    """Run Chaos Agents against the built-in HelpDesk Bot victim app."""
    console = Console()
    try:
        config = load_config()
    except ValueError as e:
        console.print(f"[red]Config error: {e}[/red]")
        raise SystemExit(1)

    from chaos_agents.agents.commander import run_full_pipeline

    victim_path = os.path.join(os.path.dirname(__file__), "victim")

    console.print("[bold]Running Chaos Agents demo against built-in HelpDesk Bot[/bold]")
    asyncio.run(run_full_pipeline(
        config=config,
        target_path=victim_path,
        output_dir=output,
        use_victim=True,
    ))


@cli.command()
@click.argument("target", type=click.Path(exists=True))
def interactive(target: str):
    """Start interactive REPL mode."""
    console = Console()
    try:
        config = load_config()
    except ValueError as e:
        console.print(f"[red]Config error: {e}[/red]")
        raise SystemExit(1)

    console.print("[bold]Chaos Agents Interactive Mode[/bold]")
    console.print(f"Target: {os.path.abspath(target)}")
    console.print("Commands: scan, plan, attack [category|all], report, status, help, exit")
    console.print("-" * 50)

    threat_model = None
    attack_results = []

    while True:
        try:
            user_input = console.input("[bold cyan]chaos>[/bold cyan] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            break

        if user_input == "exit":
            break
        elif user_input == "help":
            console.print("  scan     — Scan target codebase")
            console.print("  plan     — Show attack plan from scan")
            console.print("  attack <category|all> — Run attacks")
            console.print("  report   — Generate report")
            console.print("  status   — Show progress")
            console.print("  exit     — Quit")
        elif user_input == "scan":
            from chaos_agents.agents.commander import run_scan_only
            console.print("[blue]Scanning...[/blue]")
            threat_model = asyncio.run(run_scan_only(config, os.path.abspath(target)))
            console.print(f"[green]Done! Found {len(threat_model.agents_found)} agents, "
                          f"{len(threat_model.recommended_attacks)} recommended attacks[/green]")
        elif user_input == "plan":
            if not threat_model:
                console.print("[yellow]Run 'scan' first[/yellow]")
            else:
                for rec in threat_model.recommended_attacks:
                    console.print(f"  [{rec.severity}] {rec.attack_type} -> {rec.target_component}")
        elif user_input.startswith("attack"):
            if not threat_model:
                console.print("[yellow]Run 'scan' first[/yellow]")
            else:
                parts = user_input.split()
                category = parts[1] if len(parts) > 1 and parts[1] != "all" else None
                from chaos_agents.agents.commander import run_full_pipeline
                console.print("[blue]Attacking...[/blue]")
                asyncio.run(run_full_pipeline(
                    config=config,
                    target_path=os.path.abspath(target),
                    category=category,
                    output_dir="reports",
                ))
        elif user_input == "status":
            console.print(f"  Scan: {'Done' if threat_model else 'Not started'}")
            console.print(f"  Attacks: {len(attack_results)} completed")
        else:
            console.print(f"[yellow]Unknown command: {user_input}. Type 'help'.[/yellow]")


def main():
    """Entry point for the chaos-agents CLI."""
    cli()


if __name__ == "__main__":
    main()
