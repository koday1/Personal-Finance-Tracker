from __future__ import annotations

from app.models.transaction import Transaction


CATEGORY_BY_PRIMARY = {
    "BANK_FEES": "Fees",
    "ENTERTAINMENT": "Entertainment",
    "FOOD_AND_DRINK": "Restaurants",
    "GENERAL_MERCHANDISE": "Shopping",
    "GENERAL_SERVICES": "Services",
    "GOVERNMENT_AND_NON_PROFIT": "Giving",
    "HOME_IMPROVEMENT": "Home",
    "INCOME": "Income",
    "LOAN_PAYMENTS": "Debt",
    "MEDICAL": "Health",
    "PERSONAL_CARE": "Health",
    "RENT_AND_UTILITIES": "Bills",
    "TRANSFER_IN": "Transfers",
    "TRANSFER_OUT": "Transfers",
    "TRANSPORTATION": "Transportation",
    "TRAVEL": "Travel",
}

CATEGORY_BY_DETAIL = {
    "FOOD_AND_DRINK_COFFEE": "Coffee",
    "FOOD_AND_DRINK_FAST_FOOD": "Restaurants",
    "FOOD_AND_DRINK_GROCERIES": "Groceries",
    "FOOD_AND_DRINK_RESTAURANT": "Restaurants",
    "LOAN_PAYMENTS_CREDIT_CARD_PAYMENT": "Credit Card Payment",
    "RENT_AND_UTILITIES_INTERNET_AND_CABLE": "Bills",
    "TRANSPORTATION_GAS": "Gas",
    "TRANSPORTATION_PARKING": "Transportation",
    "TRANSPORTATION_TAXIS_AND_RIDE_SHARES": "Rideshare",
    "TRAVEL_FLIGHTS": "Travel",
}

MERCHANT_RULES = [
    ("starbucks", "Coffee"),
    ("mcdonald", "Restaurants"),
    ("kfc", "Restaurants"),
    ("uber", "Rideshare"),
    ("united airlines", "Travel"),
    ("sparkfun", "Shopping"),
    ("gusto", "Income"),
]

NAME_RULES = [
    ("gusto", "Income"),
    ("credit card", "Credit Card Payment"),
    ("student loan", "Debt"),
    ("mortgage", "Debt"),
    ("auto loan", "Debt"),
    ("loan payment", "Debt"),
    ("intrst pymnt", "Interest"),
    ("venmo", "Transfers"),
    ("zelle", "Transfers"),
]

DEFAULT_BUDGET_CATEGORY = "Other"
INCOME_CATEGORIES = {"Income", "Interest"}
TRANSFER_CATEGORIES = {"Transfers", "Credit Card Payment"}


def budget_category_for(transaction: Transaction) -> str:
    merchant = (transaction.merchant_name or "").lower()
    name = transaction.name.lower()

    if _is_credit_card_payment(transaction, name):
        return "Credit Card Payment"

    for needle, category in MERCHANT_RULES:
        if needle in merchant:
            return category

    for needle, category in NAME_RULES:
        if needle in name:
            return category

    detailed = transaction.category_detailed or ""
    if detailed in CATEGORY_BY_DETAIL:
        return CATEGORY_BY_DETAIL[detailed]

    primary = transaction.category_primary or ""
    return CATEGORY_BY_PRIMARY.get(primary, DEFAULT_BUDGET_CATEGORY)


def _is_credit_card_payment(transaction: Transaction, normalized_name: str) -> bool:
    if "payment" not in normalized_name:
        return False
    if not transaction.plaid_item:
        return False

    for account in transaction.plaid_item.accounts:
        if account.plaid_account_id != transaction.plaid_account_id:
            continue
        return account.subtype == "credit card" or account.type == "credit"

    return False


def cashflow_type_for(category: str, amount: float) -> str:
    if category in INCOME_CATEGORIES or amount < 0:
        return "income"
    if category in TRANSFER_CATEGORIES:
        return "transfer"
    return "expense"
