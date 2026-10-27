
import os
from pathlib import Path

from tools.banking_data import inspect_banking_data
from tools.transaction_analysis import analyze_payment_formats
from tools.account_investigation import investigate_account


# Resolve dataset locations from this project folder.
# The AI model will not supply arbitrary local file paths.
PROJECT_DIR = Path(__file__).resolve().parent


def get_dataset_dir():
    """Use a configured cloud directory or the local development data."""
    override = os.getenv("INSIGHTFORGE_DATA_DIR", "").strip()

    if override:
        directory = Path(override).expanduser()
        if not directory.is_absolute():
            raise ValueError(
                "INSIGHTFORGE_DATA_DIR must be an absolute path"
            )
        return directory

    return PROJECT_DIR / "data/raw"


DATA_DIR = get_dataset_dir()
TRANSACTIONS = DATA_DIR / "HI-Small_Trans.csv"
ACCOUNTS = DATA_DIR / "HI-Small_accounts.csv"


# Only these tools can be requested by the agent.
AVAILABLE_TOOLS = (
    "inspect_banking_data",
    "analyze_payment_formats",
    "investigate_account",
)


def execute_tool(tool_name, arguments=None):
    """Validate and execute one approved banking tool."""

    if tool_name not in AVAILABLE_TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")

    if arguments is None:
        arguments = {}

    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a dictionary")

    if tool_name == "inspect_banking_data":
        if arguments:
            raise ValueError(
                "inspect_banking_data accepts no arguments"
            )

        return inspect_banking_data(
            TRANSACTIONS,
            ACCOUNTS,
        )

    if tool_name == "analyze_payment_formats":
        if set(arguments) - {"top_n"}:
            raise ValueError("Unexpected tool arguments")

        return analyze_payment_formats(
            TRANSACTIONS,
            top_n=arguments.get("top_n", 10),
        )

    if tool_name == "investigate_account":
        required = {"bank_id", "account_number"}

        if set(arguments) != required:
            raise ValueError(
                "Required arguments: bank_id, account_number"
            )

        return investigate_account(
            TRANSACTIONS,
            bank_id=arguments["bank_id"],
            account_number=arguments["account_number"],
        )
