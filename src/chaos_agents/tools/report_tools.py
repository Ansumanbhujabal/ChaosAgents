"""Report generation tools — terminal, markdown, JSON output."""

from __future__ import annotations

import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from chaos_agents.models import ChaosReport


def print_terminal_report(report: ChaosReport) -> None:
    """Print a Rich-formatted terminal report."""
    console = Console()

    # Header
    severity_colors = {"Critical": "red bold", "High": "red", "Medium": "yellow", "Low": "green"}
    risk_style = severity_colors.get(report.overall_risk, "white")

    console.print()
    console.print(Panel(
        f"[bold]Chaos Agents Security Report[/bold]\n"
        f"Target: {report.target} | Domain: {report.domain}\n"
        f"Scan: {report.scan_timestamp}",
        title="CHAOS AGENTS",
        border_style="blue",
    ))

    # Risk summary
    console.print(f"\n  Overall Risk: [{risk_style}]{report.overall_risk}[/{risk_style}]")
    vc = report.vulnerability_count
    console.print(
        f"  Vulnerabilities: "
        f"[red bold]{vc.critical} Critical[/red bold] | "
        f"[red]{vc.high} High[/red] | "
        f"[yellow]{vc.medium} Medium[/yellow] | "
        f"[green]{vc.low} Low[/green]"
    )
    console.print(f"  Payloads Tried: {report.total_payloads_tried}")
    console.print(f"  OTel Coverage: {report.otel_coverage_pct:.0f}%")
    console.print(f"  Execution Time: {report.execution_time_seconds:.1f}s")
    console.print(f"  Tokens Used: {report.total_tokens_used}")

    # Attack results table
    if report.attack_results:
        console.print()
        table = Table(title="Attack Results", border_style="blue")
        table.add_column("Attack Type", style="cyan")
        table.add_column("Payloads", justify="right")
        table.add_column("Vulns Found", justify="right")
        table.add_column("Success Rate", justify="right")
        table.add_column("Severity", justify="center")

        for result in report.attack_results:
            sev = result.overall_severity
            sev_style = severity_colors.get(sev, "white")
            table.add_row(
                result.attack_type,
                str(len(result.payloads_tried)),
                str(len(result.vulnerabilities_found)),
                f"{result.success_rate:.0%}",
                f"[{sev_style}]{sev}[/{sev_style}]",
            )

        console.print(table)

    # Vulnerabilities detail
    all_vulns = []
    for result in report.attack_results:
        all_vulns.extend(result.vulnerabilities_found)

    if all_vulns:
        console.print()
        console.print("[bold]Vulnerabilities Detail:[/bold]")
        for i, vuln in enumerate(all_vulns, 1):
            sev_style = severity_colors.get(vuln.severity, "white")
            console.print(f"\n  [{sev_style}][{vuln.severity}][/{sev_style}] {vuln.title}")
            console.print(f"    Component: {vuln.component}")
            console.print(f"    {vuln.description}")
            console.print(f"    Evidence: {vuln.evidence[:200]}")
            console.print(f"    Fix: {vuln.remediation}")

    # Recommendations
    if report.recommendations:
        console.print()
        console.print("[bold]Recommendations:[/bold]")
        for rec in report.recommendations:
            console.print(f"  [{rec.priority}] {rec.title}: {rec.description}")

    # Blind spots
    if report.blind_spots:
        console.print()
        console.print("[bold yellow]Observability Blind Spots:[/bold yellow]")
        for spot in report.blind_spots:
            console.print(f"  - {spot}")

    console.print()


def generate_json_report(report: ChaosReport, output_path: str) -> None:
    """Save report as JSON."""
    with open(output_path, "w") as f:
        json.dump(report.model_dump(), f, indent=2, default=str)


def generate_markdown_report(report: ChaosReport, output_path: str) -> None:
    """Save report as Markdown."""
    vc = report.vulnerability_count
    lines = [
        "# Chaos Agents Security Report",
        "",
        f"**Target:** {report.target}",
        f"**Domain:** {report.domain}",
        f"**Scan Time:** {report.scan_timestamp}",
        f"**Overall Risk:** {report.overall_risk}",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Critical | {vc.critical} |",
        f"| High | {vc.high} |",
        f"| Medium | {vc.medium} |",
        f"| Low | {vc.low} |",
        f"| Payloads Tried | {report.total_payloads_tried} |",
        f"| OTel Coverage | {report.otel_coverage_pct:.0f}% |",
        f"| Execution Time | {report.execution_time_seconds:.1f}s |",
        f"| Tokens Used | {report.total_tokens_used} |",
        "",
        "## Attack Results",
        "",
    ]

    for result in report.attack_results:
        lines.append(f"### {result.attack_type}")
        lines.append("")
        lines.append(f"- Payloads: {len(result.payloads_tried)}")
        lines.append(f"- Vulnerabilities: {len(result.vulnerabilities_found)}")
        lines.append(f"- Success Rate: {result.success_rate:.0%}")
        lines.append(f"- Severity: {result.overall_severity}")
        lines.append("")

        for vuln in result.vulnerabilities_found:
            lines.append(f"#### [{vuln.severity}] {vuln.title}")
            lines.append("")
            lines.append(f"- **Component:** {vuln.component}")
            lines.append(f"- **Description:** {vuln.description}")
            lines.append(f"- **Evidence:** {vuln.evidence[:300]}")
            lines.append(f"- **Remediation:** {vuln.remediation}")
            lines.append("")

    if report.blind_spots:
        lines.append("## Observability Blind Spots")
        lines.append("")
        for spot in report.blind_spots:
            lines.append(f"- {spot}")
        lines.append("")

    if report.recommendations:
        lines.append("## Recommendations")
        lines.append("")
        for rec in report.recommendations:
            lines.append(f"- **[{rec.priority}] {rec.title}:** {rec.description}")
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))
