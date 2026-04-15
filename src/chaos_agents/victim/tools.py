"""Banking tools for the Finance HelpDesk victim app."""

from __future__ import annotations

import json
import os
import random
from datetime import datetime, timedelta

from agentscope.tool import ToolResponse
from agentscope.message import TextBlock

# Default path to accounts data
_DEFAULT_ACCOUNTS_PATH = os.path.join(
    os.path.dirname(__file__),
    "data",
    "accounts.json",
)


def load_accounts(accounts_path: str | None = None) -> dict:
    """Load accounts from JSON file, keyed by account_number.

    Args:
        accounts_path: Path to accounts JSON file. Uses default if None.

    Returns:
        Dictionary of accounts keyed by account number.
    """
    path = accounts_path or _DEFAULT_ACCOUNTS_PATH
    with open(path, "r") as f:
        return json.load(f)


def _save_accounts(accounts: dict, accounts_path: str | None = None) -> None:
    """Save accounts back to JSON file."""
    path = accounts_path or _DEFAULT_ACCOUNTS_PATH
    with open(path, "w") as f:
        json.dump(accounts, f, indent=2)


async def get_balance(
    account_number: str,
    accounts_path: str | None = None,
) -> ToolResponse:
    """Get the balance for a given account number.

    Args:
        account_number: The account number to look up.
        accounts_path: Optional path to accounts JSON file.

    Returns:
        ToolResponse with balance information or error message.
    """
    accounts = load_accounts(accounts_path)

    if account_number not in accounts:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Account {account_number} not found.")],
        )

    account = accounts[account_number]
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=(
                    f"Account {account_number} ({account['name']}): "
                    f"Balance is ${account['balance']:.2f}. "
                    f"Tier: {account['tier']}."
                ),
            )
        ],
    )


async def get_transaction_history(
    account_number: str,
    accounts_path: str | None = None,
) -> ToolResponse:
    """Get simulated transaction history for an account.

    Args:
        account_number: The account number to look up.
        accounts_path: Optional path to accounts JSON file.

    Returns:
        ToolResponse with transaction history or error message.
    """
    accounts = load_accounts(accounts_path)

    if account_number not in accounts:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Account {account_number} not found.")],
        )

    # Generate simulated transaction history
    categories = [
        ("Grocery Store", -45.50, -150.00),
        ("Direct Deposit", 2500.00, 5000.00),
        ("Electric Company", -85.00, -200.00),
        ("Restaurant", -25.00, -80.00),
        ("ATM Withdrawal", -100.00, -500.00),
        ("Online Transfer", -200.00, -1000.00),
        ("Refund", 15.00, 100.00),
    ]

    rng = random.Random(hash(account_number))
    lines = [f"Recent transactions for {account_number}:"]
    today = datetime.now()

    for i in range(5):
        cat_name, low, high = rng.choice(categories)
        amount = round(rng.uniform(low, high), 2)
        date = (today - timedelta(days=i + 1)).strftime("%Y-%m-%d")
        sign = "+" if amount > 0 else ""
        lines.append(f"  {date} | {cat_name:<20s} | {sign}${amount:,.2f}")

    return ToolResponse(
        content=[TextBlock(type="text", text="\n".join(lines))],
    )


async def transfer_funds(
    from_account: str,
    to_account: str,
    amount: float,
    pin: str,
    accounts_path: str | None = None,
) -> ToolResponse:
    """Transfer funds between two accounts.

    Validates PIN, checks daily transfer limit, checks sufficient balance,
    and executes the transfer.

    Args:
        from_account: Source account number.
        to_account: Destination account number.
        amount: Amount to transfer (must be positive).
        pin: PIN for the source account.
        accounts_path: Optional path to accounts JSON file.

    Returns:
        ToolResponse with transfer result or error message.
    """
    accounts = load_accounts(accounts_path)

    # Validate source account exists
    if from_account not in accounts:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Account {from_account} not found.")],
        )

    # Validate destination account exists
    if to_account not in accounts:
        return ToolResponse(
            content=[TextBlock(type="text", text=f"Account {to_account} not found.")],
        )

    source = accounts[from_account]

    # Validate PIN
    if pin != source["pin"]:
        return ToolResponse(
            content=[TextBlock(type="text", text="Invalid PIN. Transaction denied.")],
        )

    # Validate amount
    if amount <= 0:
        return ToolResponse(
            content=[TextBlock(type="text", text="Transfer amount must be positive.")],
        )

    # Check daily transfer limit
    if amount > source["daily_transfer_limit"]:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=(
                        f"Transfer of ${amount:,.2f} exceeds your daily limit "
                        f"of ${source['daily_transfer_limit']:,.2f}."
                    ),
                )
            ],
        )

    # Check sufficient balance
    if amount > source["balance"]:
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=(
                        f"Insufficient funds. Current balance: "
                        f"${source['balance']:,.2f}."
                    ),
                )
            ],
        )

    # Execute transfer
    accounts[from_account]["balance"] -= amount
    accounts[to_account]["balance"] += amount
    _save_accounts(accounts, accounts_path)

    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=(
                    f"Transfer successful: ${amount:,.2f} from {from_account} "
                    f"to {to_account}. New balance for {from_account}: "
                    f"${accounts[from_account]['balance']:,.2f}."
                ),
            )
        ],
    )
