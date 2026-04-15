"""Tests for config loading."""

import pytest

from chaos_agents.config import load_config


def test_load_config_from_env(monkeypatch):
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    config = load_config()
    assert config.api_key == "test-key"
    assert config.endpoint == "https://test.openai.azure.com/"
    assert config.deployment == "gpt-4o"
    assert config.api_version == "2024-12-01-preview"


def test_load_config_missing_key_raises(monkeypatch):
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    with pytest.raises(ValueError, match="AZURE_OPENAI_API_KEY"):
        load_config()
