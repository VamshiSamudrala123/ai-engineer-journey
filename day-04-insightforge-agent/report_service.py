"""Connect approved DuckDB account investigations to deterministic PDF reports.

This module does not call Gemini or allow user-controlled dataset paths.
"""

from collections.abc import Mapping

from report_generator import build_account_report_pdf
from tool_registry import execute_tool


def generate_account_report(bank_id: int, account_number: str) -> bytes:
    """Run an approved account investigation and render its verified results.

    The caller supplies only a bank ID and account number. The tool registry
    decides which local synthetic banking dataset to query.
    """
    if isinstance(bank_id, bool) or not isinstance(bank_id, int) or bank_id < 0:
        raise ValueError("bank_id must be a nonnegative integer")

    if not isinstance(account_number, str):
        raise ValueError("account_number must be text")

    account_number = account_number.strip()
    if not account_number or len(account_number) > 64:
        raise ValueError("account_number must be 1 to 64 characters")

    # Source of truth: the same approved DuckDB tool used by the API and Gemini.
    investigation = execute_tool(
        "investigate_account",
        {"bank_id": bank_id, "account_number": account_number},
    )

    # Don't generate a report mislabeled with an unrelated account identity.
    if not isinstance(investigation, Mapping):
        raise ValueError("Investigation tool returned invalid data")

    if (
        investigation.get("bank_id") != bank_id
        or investigation.get("account_number") != account_number
    ):
        raise ValueError("Investigation result does not match requested account")

    # This validates/reconciles all counts and returns the PDF as bytes.
    return build_account_report_pdf(investigation)
