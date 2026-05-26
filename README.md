# Personal Finance Sheets Sync

A lightweight personal budgeting backend that syncs Plaid transactions into a Google Sheets workflow.

The app is intentionally small:

- FastAPI backend
- Plaid Link token generation and public token exchange
- Encrypted Plaid access token storage
- Transaction syncing through Plaid `/transactions/sync`
- Google Apps Script client that imports categorized transactions into Sheets

## Repository Layout

```text
backend/
  app/
    api/                 FastAPI route modules
    core/                settings and security helpers
    db/                  database session/bootstrap
    models/              SQLAlchemy models
    services/            Plaid and mapping logic
google-apps-script/
  Code.gs                Apps Script client for Google Sheets
docs/
  sheets-setup.md        Spreadsheet setup notes
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

Paste the generated key into `TOKEN_ENCRYPTION_KEY` in `.env`, then fill in your Plaid and Sheets API settings.

Run locally:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

Open that URL in your browser for the built-in transaction table.

## Simplest Sandbox Test

1. Set `PLAID_ENV=sandbox` in `backend/.env`.
2. Start the backend with `uvicorn app.main:app --reload`.
3. Open `http://127.0.0.1:8000`.
4. Paste your `APP_API_KEY` value into the API key field.
5. Click `Create test data`.
6. The app will create a fake Sandbox bank connection, sync, and show transactions in the table.

`Connect sandbox bank` is still available if you specifically want to test the Plaid Link popup. For the quickest local test, use `Create test data`.

## Core Flow

1. The built-in frontend or Google Sheets calls `POST /api/plaid/link-token` with `X-API-Key`.
2. The user completes Plaid Link.
3. The frontend sends the `public_token` to `POST /api/plaid/exchange-public-token`.
4. The backend stores the encrypted Plaid `access_token`.
5. A scheduled job or Apps Script call runs `POST /api/plaid/sync-transactions` with `X-API-Key`.
6. Google Sheets pulls rows from `GET /api/sheets/transactions` with `X-API-Key`.

## Deployment Notes

This can run on Replit, Render, Fly.io, Railway, or a small VPS. For anything beyond personal use, prefer Postgres over SQLite and put the encryption key in your hosting platform's secrets manager.

Never commit `.env`, Plaid secrets, access tokens, or downloaded bank data.
