
from pathlib import Path
import duckdb


def investigate_account(transactions_path, bank_id, account_number):
    """Investigate transactions involving one bank/account pair."""

    transactions_path = Path(transactions_path)

    if not transactions_path.is_file():
        raise FileNotFoundError(
            f"Transaction file not found: {transactions_path}"
        )

    if isinstance(bank_id, bool) or not isinstance(bank_id, int):
        raise ValueError("bank_id must be an integer")

    if bank_id < 0:
        raise ValueError("bank_id cannot be negative")

    if not isinstance(account_number, str) or not account_number.strip():
        raise ValueError("account_number must be a nonempty string")

    account_number = account_number.strip()

    connection = duckdb.connect(":memory:")

    try:
        result = connection.execute(
            """
            WITH flagged AS (
                SELECT
                    COALESCE(
                        TRY_CAST("From Bank" AS BIGINT) = ?
                        AND "Account" = ?,
                        FALSE
                    ) AS is_sender,

                    COALESCE(
                        TRY_CAST("To Bank" AS BIGINT) = ?
                        AND "Account_1" = ?,
                        FALSE
                    ) AS is_receiver,

                    "Is Laundering" AS laundering_label

                FROM read_csv(?, sample_size=20000)
            )

            SELECT
                COUNT(*) AS total_transactions,

                COUNT(*) FILTER (
                    WHERE is_sender AND NOT is_receiver
                ) AS outgoing_transactions,

                COUNT(*) FILTER (
                    WHERE is_receiver AND NOT is_sender
                ) AS incoming_transactions,

                COUNT(*) FILTER (
                    WHERE is_sender AND is_receiver
                ) AS self_transfers,

                COUNT(*) FILTER (
                    WHERE laundering_label = 1
                ) AS labeled_transactions

            FROM flagged
            WHERE is_sender OR is_receiver
            """,
            [
                bank_id,
                account_number,
                bank_id,
                account_number,
                str(transactions_path),
            ],
        ).fetchone()

    finally:
        connection.close()

    return {
        "bank_id": bank_id,
        "account_number": account_number,
        "total_transactions": result[0],
        "outgoing_transactions": result[1],
        "incoming_transactions": result[2],
        "self_transfers": result[3],
        "labeled_transactions": result[4],
    }
