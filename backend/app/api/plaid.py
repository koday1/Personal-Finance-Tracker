from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.item_remove_request import ItemRemoveRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decrypt_token, encrypt_token, require_app_api_key
from app.db.session import get_db
from app.models.plaid_account import PlaidAccount
from app.models.plaid_item import PlaidItem
from app.models.transaction import Transaction
from app.services.plaid_client import get_plaid_client
from app.services.transaction_mapper import transaction_to_model_kwargs

router = APIRouter(dependencies=[Depends(require_app_api_key)])


class LinkTokenRequest(BaseModel):
    user_id: Optional[str] = None


class ExchangePublicTokenRequest(BaseModel):
    public_token: str
    user_id: Optional[str] = None
    institution_name: Optional[str] = None


class SyncTransactionsRequest(BaseModel):
    item_id: Optional[str] = None
    max_pages: int = 10


class SandboxItemRequest(BaseModel):
    user_id: Optional[str] = None
    institution_id: str = "ins_109508"
    institution_name: str = "First Platypus Bank"


class RemoveItemRequest(BaseModel):
    item_id: str


@router.get("/items")
def list_items(db: Session = Depends(get_db)) -> dict[str, object]:
    items = db.scalars(select(PlaidItem).order_by(PlaidItem.created_at.desc())).all()
    return {
        "count": len(items),
        "items": [
            {
                "item_id": item.item_id,
                "institution_name": item.institution_name or "Connected institution",
                "user_id": item.user_id,
                "accounts": [
                    {
                        "account_id": account.plaid_account_id,
                        "name": account.name,
                        "official_name": account.official_name,
                        "mask": account.mask,
                        "type": account.type,
                        "subtype": account.subtype,
                    }
                    for account in item.accounts
                ],
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "updated_at": item.updated_at.isoformat() if item.updated_at else None,
            }
            for item in items
        ],
    }


@router.post("/link-token")
def create_link_token(payload: LinkTokenRequest) -> dict[str, Any]:
    client = get_plaid_client()
    user_id = payload.user_id or settings.default_user_id
    request_kwargs: dict[str, Any] = {
        "user": LinkTokenCreateRequestUser(client_user_id=user_id),
        "client_name": settings.app_name,
        "products": [Products(product) for product in settings.plaid_product_list],
        "country_codes": [CountryCode(code) for code in settings.plaid_country_code_list],
        "language": "en",
    }
    if settings.plaid_redirect_uri:
        request_kwargs["redirect_uri"] = settings.plaid_redirect_uri

    response = client.link_token_create(LinkTokenCreateRequest(**request_kwargs))
    return response.to_dict()


@router.post("/exchange-public-token")
def exchange_public_token(
    payload: ExchangePublicTokenRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    client = get_plaid_client()
    response = client.item_public_token_exchange(
        ItemPublicTokenExchangeRequest(public_token=payload.public_token)
    )
    access_token = response["access_token"]
    item_id = response["item_id"]

    existing = db.scalar(select(PlaidItem).where(PlaidItem.item_id == item_id))
    if existing:
        existing.encrypted_access_token = encrypt_token(access_token)
        existing.institution_name = payload.institution_name
        existing.user_id = payload.user_id or settings.default_user_id
    else:
        db.add(
            PlaidItem(
                item_id=item_id,
                user_id=payload.user_id or settings.default_user_id,
                institution_name=payload.institution_name,
                encrypted_access_token=encrypt_token(access_token),
            )
        )

    db.commit()
    return {"item_id": item_id}


@router.post("/sandbox-item")
def create_sandbox_item(
    payload: SandboxItemRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    if settings.plaid_env.lower() != "sandbox":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sandbox item creation is only available when PLAID_ENV=sandbox.",
        )

    client = get_plaid_client()
    sandbox_response = client.sandbox_public_token_create(
        SandboxPublicTokenCreateRequest(
            institution_id=payload.institution_id,
            initial_products=[Products(product) for product in settings.plaid_product_list],
        )
    )

    return exchange_public_token(
        ExchangePublicTokenRequest(
            public_token=sandbox_response["public_token"],
            user_id=payload.user_id or settings.default_user_id,
            institution_name=payload.institution_name,
        ),
        db,
    )


@router.post("/remove-item")
def remove_item(
    payload: RemoveItemRequest,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    item = db.scalar(select(PlaidItem).where(PlaidItem.item_id == payload.item_id))
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plaid item not found.")

    client = get_plaid_client()
    access_token = decrypt_token(item.encrypted_access_token)
    client.item_remove(ItemRemoveRequest(access_token=access_token))

    db.query(Transaction).filter(Transaction.plaid_item_id == item.id).delete()
    db.delete(item)
    db.commit()
    return {"item_id": payload.item_id, "status": "removed"}


@router.post("/sync-transactions")
def sync_transactions(
    payload: SyncTransactionsRequest,
    db: Session = Depends(get_db),
) -> dict[str, int]:
    query = select(PlaidItem)
    if payload.item_id:
        query = query.where(PlaidItem.item_id == payload.item_id)

    items = list(db.scalars(query))
    if not items:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No Plaid items found.")

    total_added = 0
    total_modified = 0
    total_removed = 0

    client = get_plaid_client()

    for item in items:
        _sync_accounts(client, db, item)
        added, modified, removed, cursor = _sync_item(client, db, item, payload.max_pages)
        item.transactions_cursor = cursor
        total_added += added
        total_modified += modified
        total_removed += removed

    db.commit()
    return {
        "items_synced": len(items),
        "added": total_added,
        "modified": total_modified,
        "removed": total_removed,
    }


def _sync_accounts(client: Any, db: Session, item: PlaidItem) -> None:
    access_token = decrypt_token(item.encrypted_access_token)
    response = client.accounts_get(AccountsGetRequest(access_token=access_token))

    for account in response["accounts"]:
        account_id = account["account_id"]
        existing = db.scalar(
            select(PlaidAccount).where(PlaidAccount.plaid_account_id == account_id)
        )
        values = {
            "plaid_item_id": item.id,
            "plaid_account_id": account_id,
            "name": account.get("name") or "Account",
            "official_name": account.get("official_name"),
            "mask": account.get("mask"),
            "type": str(account.get("type")) if account.get("type") else None,
            "subtype": str(account.get("subtype")) if account.get("subtype") else None,
        }
        if existing:
            for key, value in values.items():
                setattr(existing, key, value)
        else:
            db.add(PlaidAccount(**values))


def _sync_item(client: Any, db: Session, item: PlaidItem, max_pages: int) -> tuple[int, int, int, Optional[str]]:
    access_token = decrypt_token(item.encrypted_access_token)
    cursor = item.transactions_cursor
    has_more = True
    page_count = 0
    added_count = 0
    modified_count = 0
    removed_count = 0

    while has_more and page_count < max_pages:
        request_kwargs = {"access_token": access_token}
        if cursor:
            request_kwargs["cursor"] = cursor

        response = client.transactions_sync(TransactionsSyncRequest(**request_kwargs))
        data = response.to_dict()

        for plaid_transaction in response["added"]:
            _upsert_transaction(db, item.id, plaid_transaction)
            added_count += 1

        for plaid_transaction in response["modified"]:
            _upsert_transaction(db, item.id, plaid_transaction)
            modified_count += 1

        for removed_transaction in response["removed"]:
            existing = db.scalar(
                select(Transaction).where(
                    Transaction.plaid_transaction_id == removed_transaction["transaction_id"]
                )
            )
            if existing:
                existing.removed = True
                removed_count += 1

        cursor = data.get("next_cursor")
        has_more = bool(data.get("has_more"))
        page_count += 1

    return added_count, modified_count, removed_count, cursor


def _upsert_transaction(db: Session, plaid_item_id: int, plaid_transaction: Any) -> None:
    values = transaction_to_model_kwargs(plaid_item_id, plaid_transaction)
    existing = db.scalar(
        select(Transaction).where(
            Transaction.plaid_transaction_id == values["plaid_transaction_id"]
        )
    )
    if existing:
        for key, value in values.items():
            setattr(existing, key, value)
    else:
        db.add(Transaction(**values))
