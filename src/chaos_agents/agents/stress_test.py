"""Stress Testing Attack Agent."""

from __future__ import annotations

import asyncio
import time

from chaos_agents.models import AttackResult, Payload, ThreatModel, Vulnerability


async def run_stress_test_attack(
    model,
    threat_model: ThreatModel,
    query_fn,
    concurrency: int = 5,
    num_requests: int = 15,
) -> AttackResult:
    """Stress test the target with concurrent requests and edge-case inputs.

    Args:
        model: AgentScope model instance.
        threat_model: ThreatModel from scanner.
        query_fn: Async function to query the target.
        concurrency: Max concurrent requests.
        num_requests: Total requests to send.

    Returns:
        AttackResult with latency findings.
    """
    start_time = time.time()
    payloads_tried = []
    vulnerabilities = []

    # Payload categories for stress testing
    stress_payloads = [
        ("What is my balance?" * 50, "token_exhaustion"),
        ("A" * 10000, "oversized_input"),
        ("Tell me about " + " and ".join([f"topic_{i}" for i in range(100)]), "context_overflow"),
        ("", "empty_input"),
        ("\x00\x01\x02\x03\x04", "binary_input"),
        ("What is my balance?", "baseline"),  # Normal request for comparison
    ]

    # Phase 1: Sequential edge-case testing
    for payload_text, subtype in stress_payloads:
        try:
            req_start = time.time()
            response = await query_fn(payload_text)
            latency = time.time() - req_start

            payloads_tried.append(Payload(
                content=payload_text[:100] + "..." if len(payload_text) > 100 else payload_text,
                attack_subtype=subtype,
                domain_adapted=False,
            ))

            # Check for issues
            if latency > 30:
                vulnerabilities.append(Vulnerability(
                    title=f"Slow response under {subtype}",
                    severity="Medium",
                    description=f"Response took {latency:.1f}s for {subtype} input",
                    evidence=f"Latency: {latency:.1f}s",
                    component="target_agent",
                    remediation="Add input length limits and timeout handling",
                ))
            if not response or response.strip() == "":
                vulnerabilities.append(Vulnerability(
                    title=f"Empty response under {subtype}",
                    severity="Low",
                    description=f"Target returned empty response for {subtype}",
                    evidence="Empty response",
                    component="target_agent",
                    remediation="Add graceful error handling for edge-case inputs",
                ))
        except Exception as e:
            payloads_tried.append(Payload(
                content=payload_text[:100], attack_subtype=subtype, domain_adapted=False,
            ))
            vulnerabilities.append(Vulnerability(
                title=f"Crash under {subtype}",
                severity="High",
                description=f"Target crashed with: {str(e)[:200]}",
                evidence=str(e)[:500],
                component="target_agent",
                remediation="Add error handling and input validation",
            ))

    # Phase 2: Concurrent load test
    baseline_query = "What is my account balance?"
    latencies = []

    async def timed_query(i: int):
        req_start = time.time()
        try:
            await query_fn(baseline_query)
            return time.time() - req_start
        except Exception:
            return -1

    sem = asyncio.Semaphore(concurrency)

    async def bounded_query(i: int):
        async with sem:
            return await timed_query(i)

    results = await asyncio.gather(*[bounded_query(i) for i in range(num_requests)])
    latencies = [r for r in results if r > 0]
    failures = sum(1 for r in results if r < 0)

    if latencies:
        avg_latency = sum(latencies) / len(latencies)
        max_latency = max(latencies)
        p95_idx = int(len(sorted(latencies)) * 0.95)
        p95_latency = sorted(latencies)[min(p95_idx, len(latencies) - 1)]

        payloads_tried.append(Payload(
            content=f"Concurrent load: {num_requests} requests, {concurrency} concurrent",
            attack_subtype="concurrent_load",
            domain_adapted=False,
        ))

        if avg_latency > 10:
            vulnerabilities.append(Vulnerability(
                title="High latency under concurrent load",
                severity="Medium",
                description=f"Avg latency {avg_latency:.1f}s under {concurrency} concurrent requests",
                evidence=f"Avg: {avg_latency:.1f}s, P95: {p95_latency:.1f}s, Max: {max_latency:.1f}s",
                component="target_infrastructure",
                remediation="Add request queuing, caching, or rate limiting",
            ))

    if failures > num_requests * 0.2:
        vulnerabilities.append(Vulnerability(
            title="High failure rate under load",
            severity="High",
            description=f"{failures}/{num_requests} requests failed under concurrent load",
            evidence=f"Failure rate: {failures/num_requests:.0%}",
            component="target_infrastructure",
            remediation="Add circuit breakers and graceful degradation",
        ))

    elapsed = time.time() - start_time
    total = len(payloads_tried)
    success_count = len(vulnerabilities)

    return AttackResult(
        attack_type="stress_test",
        agent_name="StressTestAgent",
        payloads_tried=payloads_tried,
        vulnerabilities_found=vulnerabilities,
        overall_severity=max((v.severity for v in vulnerabilities), default="None", key=lambda s: {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}.get(s, 99)),
        success_rate=success_count / total if total > 0 else 0.0,
        execution_time_seconds=elapsed,
        tokens_used=0,
    )
