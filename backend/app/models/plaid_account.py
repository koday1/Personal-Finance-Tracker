from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class PlaidAccount(Base):
    __tablename__ = "plaid_accounts"
    __table_args__ = (UniqueConstraint("plaid_account_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    plaid_item_id: Mapped[int] = mapped_column(ForeignKey("plaid_items.id"), index=True)
    plaid_account_id: Mapped[str] = mapped_column(String(128), index=True)
    name: Mapped[str] = mapped_column(String(255))
    official_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    mask: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    subtype: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    plaid_item = relationship("PlaidItem", back_populates="accounts")
