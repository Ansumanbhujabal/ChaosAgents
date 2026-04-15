"""Pydantic schemas for Chaos Agents threat models, attack results, and reports."""
from __future__ import annotations

from pydantic import BaseModel, Field


# --- Domain & Recon Schemas ---


class DomainContext(BaseModel):
    """Domain-specific context discovered during scanning."""

    domain: str = Field(description="Target application domain (e.g. finance, healthcare)")
    sensitive_entities: list[str] = Field(default_factory=list, description="Sensitive data entities found")
    dangerous_tools: list[str] = Field(default_factory=list, description="Tools with high-risk capabilities")
    business_rules: list[str] = Field(default_factory=list, description="Business rules that could be exploited")


class AgentInfo(BaseModel):
    """Information about a discovered agent."""

    name: str = Field(description="Agent class or instance name")
    agent_type: str = Field(description="Agent type (e.g. ReActAgent, DialogAgent)")
    tools: list[str] = Field(default_factory=list, description="Tools available to this agent")
    system_prompt: str = Field(default="", description="Agent system prompt if discovered")
    file_path: str = Field(default="", description="Source file where agent is defined")


class RAGSurface(BaseModel):
    """RAG attack surface information."""

    vectorstore_type: str = Field(description="Type of vector store (e.g. Qdrant, Chroma)")
    embedding_model: str = Field(default="", description="Embedding model used")
    chunk_count: int = Field(default=0, description="Number of chunks in the store")
    file_path: str = Field(default="", description="Source file path")


class MemorySurface(BaseModel):
    """Memory system attack surface."""

    memory_type: str = Field(description="Type of memory (e.g. Redis, SQLite, Mem0)")
    persistence: bool = Field(default=False, description="Whether memory persists across sessions")
    shared: bool = Field(default=False, description="Whether memory is shared across agents")
    file_path: str = Field(default="", description="Source file path")


class ToolSurface(BaseModel):
    """Tool attack surface information."""

    tool_name: str = Field(description="Name of the tool")
    risk_level: str = Field(default="medium", description="Risk level: low, medium, high, critical")
    description: str = Field(default="", description="Tool description")
    file_path: str = Field(default="", description="Source file path")


class PipelineInfo(BaseModel):
    """Agent pipeline / flow information."""

    name: str = Field(description="Pipeline or flow name")
    agents: list[str] = Field(default_factory=list, description="Agents in this pipeline")
    flow_type: str = Field(default="sequential", description="Flow type: sequential, parallel, conditional")


class GuardrailInfo(BaseModel):
    """Guardrail / safety mechanism information."""

    name: str = Field(description="Guardrail name")
    guardrail_type: str = Field(default="input", description="Type: input, output, tool_call")
    description: str = Field(default="", description="What this guardrail does")
    file_path: str = Field(default="", description="Source file path")


class OTelCoverage(BaseModel):
    """OpenTelemetry observability coverage."""

    tracing_enabled: bool = Field(default=False, description="Whether OTel tracing is set up")
    traced_components: list[str] = Field(default_factory=list, description="Components with tracing")
    untraced_components: list[str] = Field(default_factory=list, description="Components without tracing")
    coverage_pct: float = Field(default=0.0, description="Percentage of components traced")


class AttackRecommendation(BaseModel):
    """Recommended attack based on scan results."""

    attack_type: str = Field(description="Type of attack to attempt")
    target_component: str = Field(description="Component to target")
    severity: str = Field(description="Expected severity if successful")
    rationale: str = Field(description="Why this attack is recommended")
    suggested_payloads: list[str] = Field(default_factory=list, description="Example payloads to try")


class ThreatModel(BaseModel):
    """Complete threat model from scanning phase."""

    target_name: str = Field(description="Name of the target application")
    target_path: str = Field(description="Path to target application code")
    domain_context: DomainContext = Field(description="Domain context information")
    agents_found: list[AgentInfo] = Field(default_factory=list, description="Discovered agents")
    rag_surfaces: list[RAGSurface] = Field(default_factory=list, description="RAG attack surfaces")
    memory_surfaces: list[MemorySurface] = Field(default_factory=list, description="Memory attack surfaces")
    tool_surfaces: list[ToolSurface] = Field(default_factory=list, description="Tool attack surfaces")
    pipeline_map: list[PipelineInfo] = Field(default_factory=list, description="Pipeline/flow map")
    guardrails: list[GuardrailInfo] = Field(default_factory=list, description="Discovered guardrails")
    otel_coverage: OTelCoverage = Field(description="Observability coverage assessment")
    recommended_attacks: list[AttackRecommendation] = Field(default_factory=list, description="Recommended attacks")
    scan_timestamp: str = Field(description="ISO timestamp of the scan")


# --- Attack Result Schemas ---


class Payload(BaseModel):
    """An attack payload that was tried."""

    content: str = Field(description="The payload content/prompt")
    attack_subtype: str = Field(default="", description="Specific attack subtype")
    domain_adapted: bool = Field(default=False, description="Whether payload was domain-adapted")


class Vulnerability(BaseModel):
    """A discovered vulnerability."""

    title: str = Field(description="Short vulnerability title")
    severity: str = Field(description="Severity: Critical, High, Medium, Low")
    description: str = Field(description="Detailed description of the vulnerability")
    evidence: str = Field(default="", description="Evidence/output demonstrating the vulnerability")
    component: str = Field(default="", description="Affected component")
    remediation: str = Field(default="", description="Suggested remediation")


class AttackResult(BaseModel):
    """Result from a single attack agent run."""

    attack_type: str = Field(description="Type of attack performed")
    agent_name: str = Field(description="Name of the attack agent")
    payloads_tried: list[Payload] = Field(default_factory=list, description="Payloads attempted")
    vulnerabilities_found: list[Vulnerability] = Field(default_factory=list, description="Vulnerabilities discovered")
    overall_severity: str = Field(default="None", description="Overall severity for this attack type")
    success_rate: float = Field(default=0.0, description="Fraction of payloads that succeeded")
    execution_time_seconds: float = Field(default=0.0, description="Time taken in seconds")
    tokens_used: int = Field(default=0, description="Total tokens consumed")


# --- Report Schemas ---


class VulnCount(BaseModel):
    """Vulnerability count by severity."""

    critical: int = Field(default=0)
    high: int = Field(default=0)
    medium: int = Field(default=0)
    low: int = Field(default=0)


class Recommendation(BaseModel):
    """A remediation recommendation."""

    title: str = Field(description="Recommendation title")
    priority: str = Field(default="Medium", description="Priority: Critical, High, Medium, Low")
    description: str = Field(default="", description="Detailed recommendation")
    affected_components: list[str] = Field(default_factory=list, description="Components affected")


class ChaosReport(BaseModel):
    """Final chaos testing report."""

    target: str = Field(description="Target application name")
    domain: str = Field(description="Target domain")
    scan_timestamp: str = Field(description="ISO timestamp of the scan")
    threat_model: ThreatModel = Field(description="Threat model from scanning")
    attack_results: list[AttackResult] = Field(default_factory=list, description="All attack results")
    overall_risk: str = Field(default="Unknown", description="Overall risk rating")
    vulnerability_count: VulnCount = Field(default_factory=VulnCount, description="Vulnerability counts")
    otel_coverage_pct: float = Field(default=0.0, description="OTel coverage percentage")
    blind_spots: list[str] = Field(default_factory=list, description="Identified blind spots")
    recommendations: list[Recommendation] = Field(default_factory=list, description="Remediation recommendations")
    total_payloads_tried: int = Field(default=0, description="Total payloads attempted")
    total_vulnerabilities: int = Field(default=0, description="Total vulnerabilities found")
    total_tokens_used: int = Field(default=0, description="Total tokens consumed")
    execution_time_seconds: float = Field(default=0.0, description="Total execution time")
