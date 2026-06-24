from __future__ import annotations

import argparse
import os
import sys
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import joinedload


BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from app.db.session import SessionLocal  # noqa: E402
from app.api.plaid import SyncTransactionsRequest, sync_transactions  # noqa: E402
from app.models.plaid_item import PlaidItem  # noqa: E402
from app.models.transaction import Transaction  # noqa: E402
from app.services.transaction_mapper import transaction_to_sheet_row  # noqa: E402


DEFAULT_SETTLEMENT_LAG_DAYS = 8


def default_end_date() -> date:
    return date.today() - timedelta(days=DEFAULT_SETTLEMENT_LAG_DAYS)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Print a weekly spending summary.")
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to include.",
    )
    parser.add_argument(
        "--end-date",
        type=date.fromisoformat,
        default=default_end_date(),
        help=(
            "Last transaction date to include, in YYYY-MM-DD format. "
            "Defaults to 8 days ago, so a Monday run reports the prior Monday-Sunday week."
        ),
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Number of largest purchases to list.",
    )
    parser.add_argument(
        "--skip-sync",
        action="store_true",
        help="Use the local database without syncing Plaid first.",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=10,
        help="Maximum Plaid sync pages per connected institution.",
    )
    return parser.parse_args()


def dollars(amount: float) -> str:
    return f"${amount:,.2f}"


def sync_latest_transactions(max_pages: int) -> str:
    with SessionLocal() as db:
        result = sync_transactions(SyncTransactionsRequest(max_pages=max_pages), db)

    return (
        "Plaid sync complete: "
        f"{result['items_synced']} item(s), "
        f"{result['added']} added, "
        f"{result['modified']} modified, "
        f"{result['removed']} removed."
    )


def format_summary(start_date: date, end_date: date, top_limit: int) -> str:
    with SessionLocal() as db:
        transactions = db.scalars(
            select(Transaction)
            .options(
                joinedload(Transaction.plaid_item).joinedload(PlaidItem.accounts),
            )
            .where(Transaction.transaction_date >= start_date)
            .where(Transaction.transaction_date <= end_date)
            .where(Transaction.removed.is_(False))
            .where(Transaction.pending.is_(False))
            .order_by(Transaction.transaction_date.desc(), Transaction.amount.desc())
        ).unique().all()

    rows = [transaction_to_sheet_row(transaction) for transaction in transactions]
    expense_rows = [row for row in rows if row["cashflow_type"] == "expense"]

    lines = [
        f"Weekly spending summary: {start_date.isoformat()} to {end_date.isoformat()}",
        "",
    ]

    if not expense_rows:
        lines.append("No settled spending transactions found for this period.")
        return "\n".join(lines)

    total = sum(row["amount"] for row in expense_rows)
    lines.append(f"Total spending: {dollars(total)}")
    lines.append(f"Transactions counted: {len(expense_rows)}")

    category_totals: dict[str, float] = defaultdict(float)
    account_totals: dict[str, float] = defaultdict(float)
    for row in expense_rows:
        category_totals[row["budget_category"]] += row["amount"]
        account_totals[row["account_name"]] += row["amount"]

    lines.extend(["", "Category breakdown:"])
    for category, amount in sorted(category_totals.items(), key=lambda item: item[1], reverse=True):
        lines.append(f"- {category}: {dollars(amount)}")

    lines.extend(["", "Spending by account:"])
    for account, amount in sorted(account_totals.items(), key=lambda item: item[1], reverse=True):
        lines.append(f"- {account}: {dollars(amount)}")

    biggest_purchases = sorted(expense_rows, key=lambda row: row["amount"], reverse=True)[:top_limit]
    lines.extend(["", "Biggest purchases:"])
    for row in biggest_purchases:
        merchant = row["merchant"] or row["name"]
        lines.append(
            f"- {row['date']} | {merchant} | {row['budget_category']} | {dollars(row['amount'])}"
        )

    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    start_date = args.end_date - timedelta(days=args.days - 1)
    if not args.skip_sync:
        print(sync_latest_transactions(args.max_pages))
        print()
    print(format_summary(start_date, args.end_date, args.top))


if __name__ == "__main__":
    main()
