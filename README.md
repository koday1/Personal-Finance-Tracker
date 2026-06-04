# Personal Finance Tracker

A simple personal budgeting dashboard for syncing Plaid transactions and viewing everything in one place.

The app currently runs locally, connects to Plaid, stores transactions in a local database, and shows a dashboard with filters, account labels, categories, monthly totals, and connected institutions.

## Run The App

From the project folder:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Generate an encryption key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste that value into `TOKEN_ENCRYPTION_KEY` in `backend/.env`.

Fill in the rest of `backend/.env`:

```env
PLAID_CLIENT_ID=
PLAID_SECRET=
PLAID_ENV=sandbox
APP_API_KEY=choose-a-local-password
```

Start the app:

```bash
uvicorn app.main:app --reload
```

Open:

```text
http://127.0.0.1:8000
```

Paste your `APP_API_KEY` into the dashboard.

## Test With Fake Data

Use Sandbox before connecting real accounts.

1. Set `PLAID_ENV=sandbox`.
2. Start the app.
3. Open `http://127.0.0.1:8000`.
4. Paste your `APP_API_KEY`.
5. Click `Create test data`.
6. Click `Sync transactions` if the table does not load automatically.

## Use Real Accounts

For real accounts:

```env
PLAID_ENV=production
DATABASE_URL=sqlite:///./finance-prod.db
```

Then start the app and click `Connect account`.

Only enter bank credentials inside the Plaid popup. Do not put bank usernames or passwords in this app, `.env`, GitHub, or chat.

## Main Buttons

`Connect account` connects a bank through Plaid.

`Sync transactions` asks Plaid for new, changed, or removed transactions and updates the local database.

`Refresh table` reloads what is already saved locally.

`Disconnect` removes a connected institution from Plaid and deletes its local transactions.

## What The Dashboard Shows

- Transactions from connected accounts
- Account labels for checking, savings, and credit cards
- Search and filters by month, account, category, and type
- Income, spending, net cashflow, and top category
- Category breakdown
- Connected institutions

Credit card payments are treated as transfers so they do not double-count as spending.

## Local Files To Protect

Do not commit these:

```text
backend/.env
backend/finance.db
backend/finance-prod.db
backend/.venv/
```

They are ignored by Git.

## Optional Google Sheets

There is an older Google Sheets integration in `google-apps-script/`, but the recommended workflow is the built-in dashboard.

See `docs/sheets-setup.md` if you want to experiment with Sheets later.
