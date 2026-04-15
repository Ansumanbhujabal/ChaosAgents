"""Entry point for the Finance HelpDesk victim app."""

from __future__ import annotations

import asyncio

from agentscope.agent import UserAgent
from agentscope.message import Msg

from .agents import (
    create_account_agent,
    create_escalation_agent,
    create_faq_agent,
    create_router_agent,
)


def _extract_text(msg: Msg) -> str:
    """Extract plain text from a Msg object."""
    if isinstance(msg.content, str):
        return msg.content
    # content is a list of blocks
    parts = []
    for block in msg.content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(block["text"])
        elif isinstance(block, str):
            parts.append(block)
    return "\n".join(parts)


def _parse_route(route_text: str) -> str:
    """Parse the router response to extract the category."""
    text = route_text.strip().upper()
    if text.startswith("ACCOUNT"):
        return "ACCOUNT"
    if text.startswith("ESCALAT"):
        return "ESCALATE"
    # Default to FAQ for general queries
    return "FAQ"


async def _route_and_respond(
    query: str,
    router,
    faq_agent,
    account_agent,
    escalation_agent,
) -> str:
    """Route a query through the appropriate specialist agent.

    Args:
        query: The user's query text.
        router: The router agent.
        faq_agent: The FAQ agent.
        account_agent: The account operations agent.
        escalation_agent: The escalation agent.

    Returns:
        The specialist agent's response as a string.
    """
    # Create user message
    user_msg = Msg(name="Customer", content=query, role="user")

    # Route the query
    route_response = await router.reply(user_msg)
    route_text = _extract_text(route_response)
    category = _parse_route(route_text)

    # Dispatch to specialist
    if category == "ACCOUNT":
        response = await account_agent.reply(user_msg)
    elif category == "ESCALATE":
        response = await escalation_agent.reply(user_msg)
    else:
        response = await faq_agent.reply(user_msg)

    return _extract_text(response)


async def query_helpdesk(query: str, model) -> str:
    """Programmatic single-query interface for the helpdesk.

    Used by attack agents to interact with the victim app.

    Args:
        query: The customer query string.
        model: The chat model instance to use.

    Returns:
        The helpdesk response as a string.
    """
    router = create_router_agent(model)
    faq_agent = create_faq_agent(model)
    account_agent = create_account_agent(model)
    escalation_agent = create_escalation_agent(model)

    return await _route_and_respond(
        query,
        router,
        faq_agent,
        account_agent,
        escalation_agent,
    )


async def _interactive_loop(model) -> None:
    """Run the interactive helpdesk loop."""
    router = create_router_agent(model)
    faq_agent = create_faq_agent(model)
    account_agent = create_account_agent(model)
    escalation_agent = create_escalation_agent(model)
    user_agent = UserAgent(name="Customer")

    print("=" * 60)
    print("  Finance HelpDesk Bot")
    print("  Type 'quit' or 'exit' to end the session.")
    print("=" * 60)

    while True:
        # Get user input
        user_msg = await user_agent.reply()
        user_text = _extract_text(user_msg)

        if user_text.strip().lower() in ("quit", "exit"):
            print("Thank you for using Finance HelpDesk. Goodbye!")
            break

        response = await _route_and_respond(
            user_text,
            router,
            faq_agent,
            account_agent,
            escalation_agent,
        )
        print(f"\nHelpDesk: {response}\n")


def run_helpdesk(model=None) -> None:
    """Run the interactive Finance HelpDesk bot.

    Args:
        model: Optional chat model instance. If not provided, will create
            one from the default configuration.
    """
    if model is None:
        from ..config import load_config, make_model

        config = load_config()
        model = make_model(config)

    asyncio.run(_interactive_loop(model))
