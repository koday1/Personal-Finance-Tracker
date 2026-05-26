# Google Sheets Setup

Create a `Config` tab with these key/value rows:

| Key | Value |
| --- | --- |
| backendUrl | `https://your-backend.example.com` |
| apiKey | Same value as backend `APP_API_KEY` |
| userId | `personal` |

Then paste `google-apps-script/Code.gs` and `google-apps-script/LinkDialog.html` into Apps Script for the spreadsheet.

## First Sync

Reload the spreadsheet, then use:

1. `Budget Sync > Connect Plaid Account`
2. Complete Plaid Link
3. `Budget Sync > Sync Plaid Transactions`
