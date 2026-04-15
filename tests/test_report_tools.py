"""Tests for report generation tools."""

import json
import pytest
from chaos_agents.models import ChaosReport, ThreatModel, DomainContext, OTelCoverage, VulnCount
from chaos_agents.tools.report_tools import generate_json_report, generate_markdown_report


@pytest.fixture
def sample_report():
    return ChaosReport(
        target="HelpDesk Bot",
        domain="finance",
        scan_timestamp="2026-04-15T10:00:00Z",
        threat_model=ThreatModel(
            target_name="HelpDesk Bot",
            target_path="/path",
            domain_context=DomainContext(
                domain="finance", sensitive_entities=[], dangerous_tools=[], business_rules=[],
            ),
            agents_found=[], rag_surfaces=[], memory_surfaces=[],
            tool_surfaces=[], pipeline_map=[], guardrails=[],
            otel_coverage=OTelCoverage(
                tracing_enabled=False, traced_components=[], untraced_components=[], coverage_pct=0.0,
            ),
            recommended_attacks=[], scan_timestamp="2026-04-15T10:00:00Z",
        ),
        attack_results=[],
        overall_risk="Low",
        vulnerability_count=VulnCount(critical=0, high=0, medium=0, low=0),
        otel_coverage_pct=0.0,
        blind_spots=[],
        recommendations=[],
        total_payloads_tried=0,
        total_vulnerabilities=0,
        total_tokens_used=0,
        execution_time_seconds=5.2,
    )


def test_generate_json_report(sample_report, tmp_path):
    output_path = tmp_path / "report.json"
    generate_json_report(sample_report, str(output_path))

    with open(output_path) as f:
        data = json.load(f)
    assert data["target"] == "HelpDesk Bot"
    assert data["overall_risk"] == "Low"


def test_generate_markdown_report(sample_report, tmp_path):
    output_path = tmp_path / "report.md"
    generate_markdown_report(sample_report, str(output_path))

    with open(output_path) as f:
        content = f.read()
    assert "HelpDesk Bot" in content
    assert "finance" in content
