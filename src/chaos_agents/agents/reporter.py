"""Reporter Agent — aggregates attack results into ChaosReport."""

from __future__ import annotations

from chaos_agents.models import (
    ThreatModel,
    AttackResult,
    ChaosReport,
    VulnCount,
    Recommendation,
)


def build_chaos_report(
    threat_model: ThreatModel,
    attack_results: list[AttackResult],
    execution_time: float,
) -> ChaosReport:
    """Aggregate attack results into a final ChaosReport.

    Args:
        threat_model: The scanner's threat model.
        attack_results: Results from all attack agents.
        execution_time: Total execution time in seconds.

    Returns:
        Complete ChaosReport.
    """
    # Count vulnerabilities by severity
    vuln_count = VulnCount()
    all_vulns = []
    total_payloads = 0
    total_tokens = 0

    for result in attack_results:
        total_payloads += len(result.payloads_tried)
        total_tokens += result.tokens_used
        for vuln in result.vulnerabilities_found:
            all_vulns.append(vuln)
            if vuln.severity == "Critical":
                vuln_count.critical += 1
            elif vuln.severity == "High":
                vuln_count.high += 1
            elif vuln.severity == "Medium":
                vuln_count.medium += 1
            else:
                vuln_count.low += 1

    # Determine overall risk
    if vuln_count.critical > 0:
        overall_risk = "Critical"
    elif vuln_count.high > 0:
        overall_risk = "High"
    elif vuln_count.medium > 0:
        overall_risk = "Medium"
    elif vuln_count.low > 0:
        overall_risk = "Low"
    else:
        overall_risk = "None"

    # Find observability blind spots
    blind_spots = []
    otel_result = next((r for r in attack_results if r.attack_type == "observability_audit"), None)
    if otel_result:
        blind_spots = [v.description for v in otel_result.vulnerabilities_found]

    # Generate recommendations
    recommendations = _generate_recommendations(attack_results)

    return ChaosReport(
        target=threat_model.target_name,
        domain=threat_model.domain_context.domain,
        scan_timestamp=threat_model.scan_timestamp,
        threat_model=threat_model,
        attack_results=attack_results,
        overall_risk=overall_risk,
        vulnerability_count=vuln_count,
        otel_coverage_pct=threat_model.otel_coverage.coverage_pct,
        blind_spots=blind_spots,
        recommendations=recommendations,
        total_payloads_tried=total_payloads,
        total_vulnerabilities=len(all_vulns),
        total_tokens_used=total_tokens,
        execution_time_seconds=execution_time,
    )


def _generate_recommendations(attack_results: list[AttackResult]) -> list[Recommendation]:
    """Generate prioritized recommendations from attack results."""
    recommendations = []
    severity_priority = {"Critical": "P0", "High": "P1", "Medium": "P2", "Low": "P3"}

    # Group vulnerabilities by remediation
    seen_remediations = set()
    for result in attack_results:
        for vuln in result.vulnerabilities_found:
            if vuln.remediation not in seen_remediations:
                seen_remediations.add(vuln.remediation)
                recommendations.append(Recommendation(
                    title=vuln.title,
                    priority=severity_priority.get(vuln.severity, "P3"),
                    description=vuln.remediation,
                    affected_components=[vuln.component],
                ))

    # Sort by priority
    recommendations.sort(key=lambda r: r.priority)
    return recommendations
