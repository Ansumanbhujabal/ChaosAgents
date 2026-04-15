"""Observability Auditor Agent — checks if attacks were visible in traces."""

from __future__ import annotations

import time

from chaos_agents.models import AttackResult, Payload, ThreatModel, Vulnerability


async def run_observability_audit(
    threat_model: ThreatModel,
    attack_results: list[AttackResult],
) -> AttackResult:
    """Audit whether attacks were detectable via observability.

    Analyzes the ThreatModel's OTel coverage and cross-references with
    attack results to find blind spots.

    Args:
        threat_model: ThreatModel from scanner.
        attack_results: Results from all attack agents.

    Returns:
        AttackResult describing observability gaps.
    """
    start_time = time.time()
    payloads_tried = []
    vulnerabilities = []
    otel = threat_model.otel_coverage

    # Check 1: Is tracing even enabled?
    payloads_tried.append(Payload(
        content="Check: Is OpenTelemetry tracing enabled?",
        attack_subtype="tracing_check",
        domain_adapted=False,
    ))

    if not otel.tracing_enabled:
        vulnerabilities.append(Vulnerability(
            title="No observability instrumentation",
            severity="High",
            description="Target has no OpenTelemetry tracing configured. "
                        "All attacks are invisible to monitoring.",
            evidence="No setup_tracing() or @trace decorators found",
            component="observability",
            remediation="Add agentscope.tracing.setup_tracing() and instrument agent calls with @trace decorators",
        ))

    # Check 2: Are all agents traced?
    traced = set(otel.traced_components)
    all_agents = {a.name for a in threat_model.agents_found}
    untraced_agents = all_agents - traced

    if untraced_agents:
        payloads_tried.append(Payload(
            content=f"Check: Untraced agents: {', '.join(untraced_agents)}",
            attack_subtype="coverage_gap",
            domain_adapted=False,
        ))
        vulnerabilities.append(Vulnerability(
            title=f"{len(untraced_agents)} agents have no tracing",
            severity="Medium",
            description=f"Agents without traces: {', '.join(untraced_agents)}",
            evidence=f"Coverage: {otel.coverage_pct:.0f}%",
            component="observability",
            remediation="Add @trace_reply decorator to all agent reply methods",
        ))

    # Check 3: Were successful attacks detectable?
    successful_attacks = [
        r for r in attack_results
        if r.vulnerabilities_found
    ]

    for result in successful_attacks:
        attack_components = {v.component for v in result.vulnerabilities_found}
        unmonitored = attack_components - traced

        if unmonitored:
            payloads_tried.append(Payload(
                content=f"Check: {result.attack_type} hit unmonitored components: {', '.join(unmonitored)}",
                attack_subtype="blind_spot",
                domain_adapted=False,
            ))
            vulnerabilities.append(Vulnerability(
                title=f"Blind spot: {result.attack_type} attacks invisible",
                severity="High",
                description=f"{result.attack_type} successfully attacked {', '.join(unmonitored)} "
                            f"but these components have no tracing",
                evidence=f"{len(result.vulnerabilities_found)} vulnerabilities found in unmonitored components",
                component="observability",
                remediation=f"Add tracing to: {', '.join(unmonitored)}",
            ))

    # Check 4: Are tool calls traced?
    tool_agents = [a for a in threat_model.agents_found if a.tools]
    if tool_agents and not any("tool" in c.lower() for c in otel.traced_components):
        payloads_tried.append(Payload(
            content="Check: Tool execution tracing",
            attack_subtype="tool_tracing_gap",
            domain_adapted=False,
        ))
        vulnerabilities.append(Vulnerability(
            title="Tool calls not traced",
            severity="Medium",
            description="Agents have registered tools but tool execution is not instrumented",
            evidence=f"Agents with tools: {', '.join(a.name for a in tool_agents)}",
            component="observability",
            remediation="Add @trace_toolkit decorator to tool execution paths",
        ))

    elapsed = time.time() - start_time
    total = len(payloads_tried)
    success_count = len(vulnerabilities)

    return AttackResult(
        attack_type="observability_audit",
        agent_name="ObservabilityAuditor",
        payloads_tried=payloads_tried,
        vulnerabilities_found=vulnerabilities,
        overall_severity=max((v.severity for v in vulnerabilities), default="None", key=lambda s: {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}.get(s, 99)),
        success_rate=success_count / total if total > 0 else 0.0,
        execution_time_seconds=elapsed,
        tokens_used=0,
    )
