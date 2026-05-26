const CONFIG_SHEET = 'Config';
const TRANSACTIONS_SHEET = 'Transactions';

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Budget Sync')
    .addItem('Sync Plaid Transactions', 'syncPlaidTransactions')
    .addItem('Connect Plaid Account', 'openPlaidLink')
    .addToUi();
}

function openPlaidLink() {
  const template = HtmlService.createTemplateFromFile('LinkDialog');
  template.linkToken = getPlaidLinkToken_();
  SpreadsheetApp.getUi().showModalDialog(
    template.evaluate().setWidth(420).setHeight(260),
    'Connect Plaid Account'
  );
}

function getPlaidLinkToken_() {
  const config = getConfig_();
  const response = callBackend_('/api/plaid/link-token', {
    method: 'post',
    payload: JSON.stringify({ user_id: config.userId || 'personal' }),
  });
  return response.link_token;
}

function exchangePublicToken(publicToken, metadata) {
  const institution = metadata && metadata.institution ? metadata.institution.name : '';
  const config = getConfig_();
  return callBackend_('/api/plaid/exchange-public-token', {
    method: 'post',
    payload: JSON.stringify({
      public_token: publicToken,
      user_id: config.userId || 'personal',
      institution_name: institution,
    }),
  });
}

function syncPlaidTransactions() {
  callBackend_('/api/plaid/sync-transactions', {
    method: 'post',
    payload: JSON.stringify({ max_pages: 10 }),
  });

  const response = callBackend_('/api/sheets/transactions?include_pending=true', {
    method: 'get',
  });

  writeTransactions_(response.transactions || []);
}

function writeTransactions_(transactions) {
  const sheet = getOrCreateSheet_(TRANSACTIONS_SHEET);
  const headers = [
    'Date',
    'Name',
    'Merchant',
    'Amount',
    'Currency',
    'Primary Category',
    'Detailed Category',
    'Pending',
    'Transaction ID',
    'Account ID',
  ];

  sheet.clearContents();
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]).setFontWeight('bold');

  if (!transactions.length) {
    return;
  }

  const rows = transactions.map((transaction) => [
    transaction.date,
    transaction.name,
    transaction.merchant,
    transaction.amount,
    transaction.currency,
    transaction.category_primary,
    transaction.category_detailed,
    transaction.pending,
    transaction.transaction_id,
    transaction.account_id,
  ]);

  sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
  sheet.autoResizeColumns(1, headers.length);
}

function callBackend_(path, options) {
  const config = getConfig_();
  const response = UrlFetchApp.fetch(config.backendUrl + path, {
    method: options.method || 'get',
    contentType: 'application/json',
    payload: options.payload,
    headers: {
      'X-API-Key': config.apiKey,
    },
    muteHttpExceptions: true,
  });

  const status = response.getResponseCode();
  const body = response.getContentText();
  if (status < 200 || status >= 300) {
    throw new Error('Backend request failed: ' + status + ' ' + body);
  }
  return JSON.parse(body);
}

function getConfig_() {
  const sheet = getOrCreateSheet_(CONFIG_SHEET);
  const values = sheet.getDataRange().getValues();
  const config = {};
  values.forEach((row) => {
    if (row[0]) {
      config[String(row[0]).trim()] = String(row[1] || '').trim();
    }
  });

  if (!config.backendUrl || !config.apiKey) {
    throw new Error('Config sheet must include backendUrl and apiKey rows.');
  }
  return config;
}

function getOrCreateSheet_(name) {
  const spreadsheet = SpreadsheetApp.getActive();
  return spreadsheet.getSheetByName(name) || spreadsheet.insertSheet(name);
}
