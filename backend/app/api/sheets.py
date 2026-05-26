from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_app_api_key
from app.db.session import get_db
from app.models.transaction import Transaction
from app.services.transaction_mapper import transaction_to_sheet_row

router = APIRouter(dependencies=[Depends(require_app_api_key)])


@router.get("/transactions")
def list_transactions(
    since: Optional[date] = Query(default=None),
    include_pending: bool = Query(default=True),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    query = select(Transaction).where(Transaction.removed.is_(False))
    if since:
        query = query.where(Transaction.transaction_date >= since)
    if not include_pending:
        query = query.where(Transaction.pending.is_(False))

    query = query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
    transactions = db.scalars(query).all()
    return {
        "count": len(transactions),
        "transactions": [transaction_to_sheet_row(transaction) for transaction in transactions],
    }
