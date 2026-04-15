"""Integration smoke tests — verify the full pipeline wires together."""
import pytest

from chaos_agents.agents.observability_audit import run_observability_audit
from chaos_agents.agents.prompt_injection import run_prompt_injection_attack
from chaos_agents.agents.reporter import build_chaos_report
from chaos_agents.agents.tool_abuse import run_tool_abuse_attack
from chaos_agents.models import (
    AgentInfo,
    AttackRecommendation,
    DomainContext,
    OTelCoverage,
    ThreatModel,
    ToolSurface,
)


@pytest.fixture
def sample_threat_model():
    return ThreatModel(
        target_name="TestApp",
        target_path="/tmp/test",
        domain_context=DomainContext(
            domain="finance",
            sensitive_entities=["account_number", "SSN"],
            dangerous_tools=["transfer_funds"],
            business_rules=["PIN required for transfers"],
        ),
        agents_found=[
            AgentInfo(
                name="BotAgent",
                agent_type="ReActAgent",
                tools=["transfer_funds"],
                system_prompt="You are a bot",
                file_path="bot.py",
            )
        ],
        rag_surfaces=[],
        memory_surfaces=[],
        tool_surfaces=[
            ToolSurface(
                tool_name="transfer_funds",
                risk_level="critical",
                description="Move money",
                file_path="tools.py",
            )
        ],
        pipeline_map=[],
        guardrails=[],
        otel_coverage=OTelCoverage(
            tracing_enabled=False,
            traced_components=[],
            untraced_components=["BotAgent"],
            coverage_pct=0.0,
        ),
        recommended_attacks=[
            AttackRecommendation(
                attack_type="prompt_injection",
                target_component="BotAgent",
                severity="High",
                rationale="No input validation",
                suggested_payloads=["test"],
            )
        ],
        scan_timestamp="2026-04-15T10:00:00Z",
    )


async def test_prompt_injection_against_mock_target(
    sample_threat_model,
):
    async def mock_query(query):
        return (
            "I cannot comply with that request. "
            "Please contact support."
        )

    result = await run_prompt_injection_attack(
        None, sample_threat_model, mock_query
    )
    assert result.attack_type == "prompt_injection"
    assert len(result.payloads_tried) > 0
    assert result.success_rate == 0.0


async def test_tool_abuse_against_mock_target(
    sample_threat_model,
):
    async def mock_query(query):
        return (
            "I need proper authorization before "
            "I can process that request."
        )

    result = await run_tool_abuse_attack(
        None, sample_threat_model, mock_query
    )
    assert result.attack_type == "tool_abuse"
    assert len(result.payloads_tried) > 0


async def test_observability_audit(sample_threat_model):
    result = await run_observability_audit(
        sample_threat_model, []
    )
    assert result.attack_type == "observability_audit"
    assert len(result.vulnerabilities_found) > 0
    assert any(
        "observability" in v.title.lower()
        or "No observability" in v.title
        for v in result.vulnerabilities_found
    )


async def test_full_report_generation(sample_threat_model):
    async def mock_query(query):
        return "Request denied."

    pi_result = await run_prompt_injection_attack(
        None, sample_threat_model, mock_query
    )
    audit_result = await run_observability_audit(
        sample_threat_model, [pi_result]
    )
    report = build_chaos_report(
        sample_threat_model, [pi_result, audit_result], 5.0
    )
    assert report.target == "TestApp"
    assert report.domain == "finance"
    assert report.total_payloads_tried > 0
