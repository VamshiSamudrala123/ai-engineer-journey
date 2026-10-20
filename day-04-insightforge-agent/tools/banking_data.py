
from pathlib import Path

import duckdb


def inspect_banking_data(transactions_path, accounts_path):
    """Inspect the banking datasets and return summary statistics."""

    transactions_path = Path(transactions_path)
    accounts_path = Path(accounts_path)

    # Make sure both files exist before querying them.
    if not transactions_path.is_file():
        raise FileNotFoundError(
            f"Transactions file not found: {transactions_path}"
        )

    if not accounts_path.is_file():
        raise FileNotFoundError(
            f"Accounts file not found: {accounts_path}"
        )

    # Use an in-memory DuckDB database.
    connection = duckdb.connect(":memory:")

    try:
        # Calculate statistics directly from the transaction CSV.
        transaction_result = connection.execute(
            """
            SELECT
                COUNT(*) AS transaction_count,
                MIN("Timestamp") AS first_transaction,
                MAX("Timestamp") AS last_transaction,
                COUNT(DISTINCT "From Bank")
                    AS distinct_sending_bank_values,
                COUNT(DISTINCT "Payment Currency")
                    AS payment_currency_count,
                COALESCE(
                    SUM(
                        CASE
                            WHEN "Is Laundering" = 1 THEN 1
                            ELSE 0
                        END
                    ),
                    0
                ) AS laundering_label_count
            FROM read_csv(?, sample_size=20000)
            """,
            [str(transactions_path)],
        ).fetchone()

        # Count the account records separately.
        account_result = connection.execute(
            """
            SELECT COUNT(*)
            FROM read_csv(?, sample_size=20000)
            """,
            [str(accounts_path)],
        ).fetchone()

    finally:
        # Close the connection even if a query fails.
        connection.close()

    (
        transaction_count,
        first_transaction,
        last_transaction,
        distinct_sending_bank_values,
        payment_currency_count,
        laundering_label_count,
    ) = transaction_result

    # Convert timestamps to strings so the result is JSON-friendly.
    return {
        "transaction_count": transaction_count,
        "account_count": account_result[0],
        "first_transaction": (
            first_transaction.isoformat()
            if first_transaction is not None else None
        ),
        "last_transaction": (
            last_transaction.isoformat()
            if last_transaction is not None else None
        ),
        "distinct_sending_bank_values": distinct_sending_bank_values,
        "payment_currency_count": payment_currency_count,
        "laundering_label_count": int(laundering_label_count),
    }
