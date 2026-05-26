from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from typing import Any, Optional

from app.models.transaction import Transaction
from app.services.category_rules import budget_category_for, cashflow_type_for


def _personal_finance_category(transaction: Any) -> tuple[Optional[str], Optional[str]]:
    category = getattr(transaction, "personal_finance_category", None)
    if not category:
        return None, None
    return getattr(category, "primary", None), getattr(category, "detailed", None)


def transaction_to_model_kwargs(plaid_item_id: int, transaction: Any) -> dict[str, Any]:
    primary, detailed = _personal_finance_category(transaction)
    transaction_date = getattr(transaction, "date")
    if isinstance(transaction_date, str):
        transaction_date = date.fromisoformat(transaction_date)

    return {
        "plaid_item_id": plaid_item_id,
        "plaid_transaction_id": transaction.transaction_id,
        "plaid_account_id": transaction.account_id,
        "transaction_date": transaction_date,
        "name": transaction.name,
        "merchant_name": getattr(transaction, "merchant_name", None),
        "amount": Decimal(str(transaction.amount)),
        "iso_currency_code": getattr(transaction, "iso_currency_code", None),
        "category_primary": primary,
        "category_detailed": detailed,
        "pending": bool(getattr(transaction, "pending", False)),
        "removed": False,
        "raw_json": json.dumps(transaction.to_dict(), default=str),
    }


def transaction_to_sheet_row(transaction: Transaction) -> dict[str, Any]:
    amount = float(transaction.amount)
    budget_category = budget_category_for(transaction)
    return {
        "date": transaction.transaction_date.isoformat(),
        "name": transaction.name,
        "merchant": transaction.merchant_name or "",
        "amount": amount,
        "currency": transaction.iso_currency_code or "",
        "budget_category": budget_category,
        "cashflow_type": cashflow_type_for(budget_category, amount),
        "category_primary": transaction.category_primary or "",
        "category_detailed": transaction.category_detailed or "",
        "pending": transaction.pending,
        "transaction_id": transaction.plaid_transaction_id,
        "account_id": transaction.plaid_account_id,
        "item_id": transaction.plaid_item.item_id if transaction.plaid_item else "",
    }
