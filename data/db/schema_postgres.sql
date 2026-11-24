CREATE TABLE customers (
  customer_id TEXT PRIMARY KEY,
  first_name TEXT,
  last_name TEXT,
  birth_year INTEGER,
  city TEXT,
  state TEXT,
  customer_since DATE,
  digital_banking_enrolled BOOLEAN,
  digital_enrolled_date DATE
);

CREATE TABLE accounts (
  account_id TEXT PRIMARY KEY,
  customer_id TEXT,
  product TEXT,
  account_type TEXT,
  opened_date DATE,
  first_deposit_date DATE,
  status TEXT,
  statement_cycle_day INTEGER
);

CREATE TABLE cards (
  card_id TEXT PRIMARY KEY,
  account_id TEXT,
  card_type TEXT,
  network TEXT,
  last4 TEXT,
  issued_date DATE,
  verification_status TEXT
);

CREATE TABLE statements (
  statement_id TEXT PRIMARY KEY,
  account_id TEXT,
  period_end DATE,
  sent_date DATE
);

CREATE TABLE transactions (
  txn_id TEXT PRIMARY KEY,
  account_id TEXT,
  card_id TEXT,
  txn_date DATE,
  posted_date DATE,
  amount NUMERIC(12,2),
  channel TEXT,
  merchant_name TEXT,
  mcc TEXT,
  country TEXT,
  disputed BOOLEAN
);

CREATE TABLE dispute_cases (
  case_id TEXT PRIMARY KEY,
  customer_id TEXT,
  account_id TEXT,
  txn_id TEXT,
  received_channel TEXT,
  notice_type TEXT,
  notice_date DATE,
  statement_sent_date DATE,
  written_confirmation_requested BOOLEAN,
  written_confirmation_received_date DATE,
  claim_type TEXT,
  regulation TEXT,
  coverage_note TEXT,
  amount NUMERIC(12,2),
  new_account BOOLEAN,
  point_of_sale BOOLEAN,
  foreign_initiated BOOLEAN,
  timely_notice BOOLEAN,
  initial_period_business_days INTEGER,
  extended_period_calendar_days INTEGER,
  provisional_credit_date DATE,
  provisional_credit_amount NUMERIC(12,2),
  determination TEXT,
  determination_date DATE,
  reversal_date DATE,
  assigned_team TEXT,
  assigned_analyst TEXT,
  approved_by TEXT,
  procedure_version TEXT,
  system_version TEXT,
  status TEXT
);

CREATE TABLE case_events (
  event_id TEXT PRIMARY KEY,
  case_id TEXT,
  event_date DATE,
  event_type TEXT,
  actor TEXT,
  detail TEXT
);

CREATE TABLE letters (
  letter_id TEXT PRIMARY KEY,
  case_id TEXT,
  template_id TEXT,
  template_version INTEGER,
  sent_date DATE,
  channel TEXT
);

CREATE TABLE chargebacks (
  chargeback_id TEXT PRIMARY KEY,
  case_id TEXT,
  filed_date DATE,
  amount NUMERIC(12,2),
  reason_category TEXT,
  outcome TEXT,
  outcome_date DATE
);

CREATE TABLE analysts (
  analyst_id TEXT PRIMARY KEY,
  name TEXT,
  team TEXT,
  hired_date DATE,
  left_date DATE
);

CREATE TABLE holidays (
  date DATE,
  name TEXT
);

CREATE INDEX ix_cases_notice ON dispute_cases(notice_date);

CREATE INDEX ix_events_case ON case_events(case_id);

CREATE INDEX ix_txn_acct ON transactions(account_id);

CREATE INDEX ix_letters_case ON letters(case_id);
