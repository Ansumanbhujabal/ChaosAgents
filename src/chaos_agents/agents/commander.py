"""Commander Agent — orchestrates the full scan-attack-report pipeline."""

from __future__ import annotations

import asyncio
import time
from typing import Callable

from rich.console import Console

from chaos_agents.config import ChaosConfig, make_model
from chaos_agents.models import ThreatModel, AttackResult
from chaos_agents.agents.scanner import run_scan
from chaos_agents.agents.prompt_injection import run_prompt_injection_attack
from chaos_agents.agents.memory_poison import run_memory_poison_attack
from chaos_agents.agents.tool_abuse import run_tool_abuse_attack
from chaos_agents.agents.rag_poison import run_rag_poison_attack
from chaos_agents.agents.stress_test import run_stress_test_attack
from chaos_agents.agents.multi_agent_manip import run_multi_agent_manipulation_attack
from chaos_agents.agents.observability_audit import run_observability_audit
from chaos_agents.agents.reporter import build_chaos_report
from chaos_agents.tools.report_tools import print_terminal_report, generate_json_report, generate_markdown_report
from chaos_agents.victim.app import query_helpdesk


ATTACK_REGISTRY = {
    "prompt_injection": {
        "fn": run_prompt_injection_attack,
        "requires": None,  # Always applicable
    },
    "memory_poison": {
        "fn": run_memory_poison_attack,
        "requires": "memory_surfaces",
    },
    "tool_abuse": {
        "fn": run_tool_abuse_attack,
        "requires": "tool_surfaces",
    },
    "rag_poison": {
        "fn": run_rag_poison_attack,
        "requires": "rag_surfaces",
    },
    "stress_test": {
        "fn": run_stress_test_attack,
        "requires": None,  # Always applicable
    },
    "multi_agent_manipulation": {
        "fn": run_multi_agent_manipulation_attack,
        "requires": "pipeline_map",
    },
}


async def run_full_pipeline(
    config: ChaosConfig,
    target_path: str,
    category: str | None = None,
    output_dir: str = "reports",
    use_victim: bool = False,
) -> None:
    """Run the full scan -> attack -> audit -> report pipeline.

    Args:
        config: Azure OpenAI configuration.
        target_path: Path to target codebase.
        category: Specific attack category to run (None = all applicable).
        output_dir: Directory for report output.
        use_victim: If True, attack the built-in victim app.
    """
    console = Console()
    start_time = time.time()
    model = make_model(config)

    # Step 1: Scan
    console.print("[bold blue]Phase 1: Scanning target...[/bold blue]")
    threat_model = await run_scan(model, target_path)
    console.print(f"  Found {len(threat_model.agents_found)} agents, "
                  f"{len(threat_model.tool_surfaces)} tools, "
                  f"{len(threat_model.rag_surfaces)} RAG surfaces")
    console.print(f"  Domain: {threat_model.domain_context.domain}")
    console.print(f"  Recommended attacks: {len(threat_model.recommended_attacks)}")

    # Step 2: Build query function
    if use_victim:
        async def query_fn(query: str) -> str:
            return await query_helpdesk(query, make_model(config))
    else:
        async def query_fn(query: str) -> str:
            return f"[No live target configured. Query: {query[:100]}]"

    # Step 3: Determine which attacks to run
    attacks_to_run = _select_attacks(threat_model, category)
    console.print(f"\n[bold blue]Phase 2: Running {len(attacks_to_run)} attack agents...[/bold blue]")

    # Step 4: Execute attacks in parallel
    attack_tasks = []
    for attack_name, attack_info in attacks_to_run.items():
        console.print(f"  Dispatching: {attack_name}")
        attack_tasks.append(
            attack_info["fn"](model, threat_model, query_fn)
        )

    attack_results = await asyncio.gather(*attack_tasks)
    attack_results = list(attack_results)

    # Step 5: Run observability audit
    console.print("\n[bold blue]Phase 3: Observability audit...[/bold blue]")
    audit_result = await run_observability_audit(threat_model, attack_results)
    attack_results.append(audit_result)

    # Step 6: Generate report
    console.print("\n[bold blue]Phase 4: Generating report...[/bold blue]")
    elapsed = time.time() - start_time
    report = build_chaos_report(threat_model, attack_results, elapsed)

    # Output
    print_terminal_report(report)

    import os
    os.makedirs(output_dir, exist_ok=True)
    timestamp = threat_model.scan_timestamp.replace(":", "-").replace("T", "_")[:19]
    json_path = os.path.join(output_dir, f"{threat_model.target_name}-{timestamp}.json")
    md_path = os.path.join(output_dir, f"{threat_model.target_name}-{timestamp}.md")

    generate_json_report(report, json_path)
    generate_markdown_report(report, md_path)
    console.print(f"  JSON report: {json_path}")
    console.print(f"  Markdown report: {md_path}")


async def run_scan_only(config: ChaosConfig, target_path: str) -> ThreatModel:
    """Run only the scanner, return ThreatModel."""
    model = make_model(config)
    return await run_scan(model, target_path)


def _select_attacks(
    threat_model: ThreatModel,
    category: str | None,
) -> dict:
    """Select which attacks to run based on threat model and user filter."""
    selected = {}

    for name, info in ATTACK_REGISTRY.items():
        # Filter by category if specified
        if category and name != category:
            continue

        # Skip if required surface doesn't exist
        requires = info["requires"]
        if requires:
            surface = getattr(threat_model, requires, [])
            if not surface:
                continue

        selected[name] = info

    return selected
