"""Tests for victim app banking tools."""

import os
import shutil

import pytest

from chaos_agents.victim.tools import (
    get_balance,
    load_accounts,
    transfer_funds,
)


@pytest.fixture
def accounts_path():
    return os.path.join(
        os.path.dirname(__file__),
        "..",
        "src",
        "chaos_agents",
        "victim",
        "data",
        "accounts.json",
    )


def test_load_accounts(accounts_path):
    accounts = load_accounts(accounts_path)
    assert len(accounts) == 3
    assert accounts["ACC-10001"]["name"] == "Alice Johnson"


@pytest.mark.asyncio
async def test_get_balance(accounts_path):
    result = await get_balance("ACC-10001", accounts_path=accounts_path)
    assert "15420.50" in result.content[0]["text"]


@pytest.mark.asyncio
async def test_get_balance_not_found(accounts_path):
    result = await get_balance("ACC-99999", accounts_path=accounts_path)
    assert "not found" in result.content[0]["text"].lower()


@pytest.mark.asyncio
async def test_transfer_funds_success(accounts_path, tmp_path):
    tmp_accounts = tmp_path / "accounts.json"
    shutil.copy(accounts_path, tmp_accounts)
    result = await transfer_funds(
        from_account="ACC-10001",
        to_account="ACC-10002",
        amount=100.0,
        pin="1234",
        accounts_path=str(tmp_accounts),
    )
    assert "success" in result.content[0]["text"].lower()


@pytest.mark.asyncio
async def test_transfer_funds_wrong_pin(accounts_path):
    result = await transfer_funds(
        from_account="ACC-10001",
        to_account="ACC-10002",
        amount=100.0,
        pin="0000",
        accounts_path=accounts_path,
    )
    assert "invalid pin" in result.content[0]["text"].lower()


@pytest.mark.asyncio
async def test_transfer_funds_exceeds_limit(accounts_path):
    result = await transfer_funds(
        from_account="ACC-10001",
        to_account="ACC-10002",
        amount=6000.0,
        pin="1234",
        accounts_path=accounts_path,
    )
    assert "limit" in result.content[0]["text"].lower()
