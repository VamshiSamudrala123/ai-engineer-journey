
from pathlib import Path
import duckdb


def analyze_payment_formats(transactions_path, top_n=10):
    """Summarize payment formats and synthetic laundering labels."""

    transactions_path = Path(transactions_path)

    if not transactions_path.is_file():
        raise FileNotFoundError(
            f"Transaction file not found: {transactions_path}"
        )

    if not isinstance(top_n, int) or isinstance(top_n, bool):
        raise ValueError("top_n must be an integer")

    if not 1 <= top_n <= 100:
        raise ValueError("top_n must be between 1 and 100")

    connection = duckdb.connect(":memory:")

    try:
        rows = connection.execute(
            """
            SELECT
                "Payment Format" AS payment_format,
                "Payment Currency" AS currency,
                COUNT(*) AS transaction_count,
                COUNT(*) FILTER (
                    WHERE "Is Laundering" = 1
                ) AS labeled_count,
                ROUND(
                    100.0 * COUNT(*) FILTER (
                        WHERE "Is Laundering" = 1
                    ) / COUNT(*),
                    3
                ) AS labeled_percentage
            FROM read_csv(?, sample_size=20000)
            GROUP BY
                "Payment Format",
                "Payment Currency"
            ORDER BY transaction_count DESC,
                     payment_format, currency
            LIMIT ?
            """,
            [str(transactions_path), top_n],
        ).fetchall()

        return [
            {
                "payment_format": row[0],
                "currency": row[1],
                "transaction_count": row[2],
                "labeled_count": row[3],
                "labeled_percentage": float(row[4]),
            }
            for row in rows
        ]

    finally:
        connection.close()