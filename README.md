# Personal Finance Tracker

A lightweight personal budgeting app that syncs Plaid transactions into a local FastAPI backend and displays them in a simple dashboard.

The current app is built for a low-cost, self-owned workflow:

- FastAPI backend
- Plaid Sandbox and Plaid Link support
- Encrypted Plaid access token storage
- Transaction syncing through Plaid `/transactions/sync`
- Local dashboard with transaction table, filters, monthly summary, and category breakdown
- Friendly budget categories and starter category rules
- Disconnect button that removes a Plaid Item through `/item/remove`
- Optional Google Sheets export path for later

## Repository Layout

```text
backend/
  app/
    api/                 FastAPI route modules
    core/                settings and security helpers
    db/                  database session/bootstrap
    models/              SQLAlchemy models
    services/            Plaid client, category rules, and transaction mapping
    web/                 Built-in dashboard UI
google-apps-script/
  Code.gs                Optional Apps Script client for Google Sheets
docs/
  sheets-setup.md        Optional spreadsheet setup notes
```

## Quick Start

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste the generated key into `TOKEN_ENCRYPTION_KEY` in `backend/.env`.

Then fill in:

```env
PLAID_CLIENT_ID=
PLAID_SECRET=
PLAID_ENV=sandbox
APP_API_KEY=choose-a-local-password
```

Run locally:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Paste your `APP_API_KEY` into the dashboard.

## Simplest Sandbox Test

Use this before connecting real accounts.

1. Start the backend.
2. Open `http://127.0.0.1:8000`.
3. Paste your `APP_API_KEY`.
4. Click `Create test data`.
5. The app creates a fake Plaid Sandbox institution, syncs transactions, and loads the dashboard.

`Connect sandbox bank` is available if you want to test Plaid Link itself, but `Create test data` is the fastest path for local testing.

## Current Dashboard Features

- Transaction table
- Search by merchant, name, or category
- Month filter
- Account filter for checking, savings, and credit card accounts
- Budget category filter
- Type filter for expenses, income, and transfers
- Sort by date, amount, account, category, name, merchant, or type
- Monthly summary cards for income, spending, net cashflow, and top category
- Category breakdown sidebar
- Connected institutions panel
- Disconnect button for removing Plaid Items

## Budget Categories

Plaid categories are mapped into friendlier budget categories in:

```text
backend/app/services/category_rules.py
```

Examples:

- `FOOD_AND_DRINK_COFFEE` -> `Coffee`
- `FOOD_AND_DRINK_FAST_FOOD` -> `Restaurants`
- `RENT_AND_UTILITIES` -> `Bills`
- `TRANSPORTATION_TAXIS_AND_RIDE_SHARES` -> `Rideshare`
- Unknown categories -> `Other`

Merchant and name rules can also override Plaid categories.

## Main Flow

1. The dashboard calls `POST /api/plaid/link-token` or `POST /api/plaid/sandbox-item`.
2. The backend stores an encrypted Plaid access token.
3. `Sync transactions` calls `POST /api/plaid/sync-transactions`.
4. The backend updates local SQLite transaction data.
5. The dashboard calls `GET /api/sheets/transactions` to render the table and summaries.

The `/api/sheets/transactions` name is historical; it now powers both the local dashboard and the optional Sheets workflow.

## Sync vs Refresh

`Sync transactions` talks to Plaid and updates the local database.

`Refresh table` only reloads transactions that are already saved locally.

## Disconnecting Institutions

Use the dashboard's `Disconnect` button under `Connected Institutions` to remove an institution.

That calls Plaid `/item/remove`, deletes that institution's local transactions, and removes the stored access token. This matters because Plaid billing can continue while an Item exists.

## Secrets And Local Data

Do not commit:

- `backend/.env`
- `backend/finance.db`
- `backend/.venv/`

These are ignored by Git.

## Optional Google Sheets

The original Sheets integration still exists, but the recommended first workflow is the built-in dashboard.

See:

```text
docs/sheets-setup.md
```

## Deployment Notes

This can run on Replit, Render, Fly.io, Railway, or a small VPS. For anything beyond personal local use, prefer Postgres over SQLite and put secrets in your hosting platform's secrets manager.
