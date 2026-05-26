from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (UniqueConstraint("plaid_transaction_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plaid_item_id: Mapped[int] = mapped_column(ForeignKey("plaid_items.id"), index=True)
    plaid_transaction_id: Mapped[str] = mapped_column(String(128), index=True)
    plaid_account_id: Mapped[str] = mapped_column(String(128), index=True)
    transaction_date: Mapped[date] = mapped_column(Date, index=True)
    name: Mapped[str] = mapped_column(String(500))
    merchant_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2))
    iso_currency_code: Mapped[Optional[str]] = mapped_column(String(12), nullable=True)
    category_primary: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    category_detailed: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    pending: Mapped[bool] = mapped_column(Boolean, default=False)
    removed: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    plaid_item = relationship("PlaidItem", back_populates="transactions")
