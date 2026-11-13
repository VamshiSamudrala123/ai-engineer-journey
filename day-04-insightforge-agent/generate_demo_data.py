"""Generate deterministic, clearly fictional sample transactions for a small demo.

Opt in with INSIGHTFORGE_DEMO_DATA=true. This is NOT the IBM/Kaggle dataset.
The generated values must never be presented as measured real-world statistics.
Existing dataset files are not overwritten.
"""
import csv
from datetime import datetime, timedelta
import os
from pathlib import Path
import random

PROJECT_DIR = Path(__file__).resolve().parent


def main():
    override = os.getenv("INSIGHTFORGE_DATA_DIR", "").strip()
    output_dir = Path(override) if override else PROJECT_DIR / "data" / "raw"
    if not output_dir.is_absolute():
        raise ValueError("INSIGHTFORGE_DATA_DIR must be an absolute path")

    transactions = output_dir / "HI-Small_Trans.csv"
    accounts = output_dir / "HI-Small_accounts.csv"
    if transactions.exists() and accounts.exists():
        print("Existing dataset found; preserving it.")
        return
    if transactions.exists() or accounts.exists():
        raise FileExistsError("Only one dataset file exists; refusing to overwrite it")

    output_dir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(20261113)
    known_accounts = [(3208, "8000F4580")]
    known_accounts += [(3200 + i // 20, f"DEMO{i:05d}") for i in range(1, 121)]

    with accounts.open("x", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Bank ID", "Account Number"])
        writer.writerows(known_accounts)

    with transactions.open("x", newline="", encoding="utf-8") as file:
        fields = [
            "Timestamp", "From Bank", "Account", "To Bank", "Account_1",
            "Amount Received", "Receiving Currency", "Amount Paid",
            "Payment Currency", "Payment Format", "Is Laundering",
        ]
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for i in range(1500):
            sender = known_accounts[0] if i % 11 == 0 else rng.choice(known_accounts)
            receiver = known_accounts[0] if i % 17 == 0 else rng.choice(known_accounts)
            currency = rng.choice(["USD", "EUR", "GBP", "CAD"])
            writer.writerow({
                "Timestamp": (datetime(2022, 9, 1) + timedelta(minutes=i * 17)).strftime("%Y-%m-%d %H:%M:%S"),
                "From Bank": sender[0],
                "Account": sender[1],
                "To Bank": receiver[0],
                "Account_1": receiver[1],
                "Amount Received": f"{rng.uniform(10, 8000):.2f}",
                "Receiving Currency": currency,
                "Amount Paid": f"{rng.uniform(10, 8000):.2f}",
                "Payment Currency": currency,
                "Payment Format": rng.choice(["ACH", "Cheque", "Credit card", "Cash", "Reinvestment"]),
                "Is Laundering": int(i % 73 == 0),
            })
    print(f"Generated 1,500 fictional demo transactions and {len(known_accounts)} demo accounts")


if __name__ == "__main__":
    main()
