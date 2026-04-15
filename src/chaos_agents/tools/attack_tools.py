"""Tools for attack agents — target interaction, payload delivery, result formatting."""

from __future__ import annotations


def format_attack_result(
    response_text: str,
    payload: str,
    attack_subtype: str,
    is_successful: bool,
    severity: str = "High",
    component: str = "unknown",
    remediation: str = "Add input validation",
) -> dict:
    """Format an attack attempt result into a structured dict.

    Args:
        response_text: The target's response to the payload.
        payload: The attack payload that was sent.
        attack_subtype: Category of the attack (e.g., direct_injection).
        is_successful: Whether the attack succeeded.
        severity: Severity if successful.
        component: Which component was targeted.
        remediation: Suggested fix.

    Returns:
        Dict with payload and optional vulnerability info.
    """
    result = {
        "payload": {
            "content": payload,
            "attack_subtype": attack_subtype,
            "domain_adapted": False,
        },
        "vulnerability": None,
    }

    if is_successful:
        result["vulnerability"] = {
            "title": f"Successful {attack_subtype}",
            "severity": severity,
            "description": f"Target responded to {attack_subtype} attack",
            "evidence": response_text[:500],
            "component": component,
            "remediation": remediation,
        }

    return result
