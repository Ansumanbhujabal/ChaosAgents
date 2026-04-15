"""Configuration loading for Chaos Agents."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class ChaosConfig:
    """Azure OpenAI configuration."""

    api_key: str
    endpoint: str
    deployment: str
    api_version: str
    model_name: str
    embedding_deployment: str | None = None
    embedding_model: str | None = None


def load_config() -> ChaosConfig:
    """Load configuration from environment variables."""
    load_dotenv()

    api_key = os.environ.get("AZURE_OPENAI_API_KEY")
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")

    if not api_key:
        raise ValueError("AZURE_OPENAI_API_KEY environment variable is required")
    if not endpoint:
        raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is required")

    return ChaosConfig(
        api_key=api_key,
        endpoint=endpoint,
        deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-12-01-preview"),
        model_name=os.environ.get("AZURE_OPENAI_MODEL", "gpt-4o"),
        embedding_deployment=os.environ.get("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        embedding_model=os.environ.get("AZURE_OPENAI_EMBEDDING_MODEL"),
    )


def make_model(config: ChaosConfig, stream: bool = False):
    """Create an AgentScope OpenAIChatModel configured for Azure."""
    from agentscope.model import OpenAIChatModel

    return OpenAIChatModel(
        model_name=config.model_name,
        api_key=config.api_key,
        client_type="azure",
        client_kwargs={
            "azure_endpoint": config.endpoint,
            "api_version": config.api_version,
            "azure_deployment": config.deployment,
        },
        stream=stream,
        generate_kwargs={"temperature": 0.7, "max_tokens": 4096},
    )
