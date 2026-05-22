-- Phase 10 DB Migration: Relational schema for Budget Command Center
-- All tables use prefix bcc_ and enforce RLS via user_id = auth.uid()

-- ─── ACCOUNTS ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_accounts (
    id                  TEXT PRIMARY KEY,
    user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    type                TEXT NOT NULL DEFAULT 'budget',
    color               TEXT NOT NULL DEFAULT '#3a7fc1',
    opening_balance     NUMERIC(12,2) NOT NULL DEFAULT 0,
    debt_apr            NUMERIC(8,3),
    debt_min_payment    NUMERIC(12,2),
    credit_limit        NUMERIC(12,2),
    archived            BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order          INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE bcc_accounts ENABLE ROW LEVEL SECURITY;

CREATE POLICY bcc_accounts_user_policy ON bcc_accounts
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ─── CATEGORIES ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_categories (
    id          TEXT PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    color       TEXT NOT NULL DEFAULT '',
    archived    BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE bcc_categories ENABLE ROW LEVEL SECURITY;

CREATE POLICY bcc_categories_user_policy ON bcc_categories
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ─── BUCKETS ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_buckets (
    id                  TEXT PRIMARY KEY,
    user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    cat_id              TEXT,
    name                TEXT NOT NULL,
    type                TEXT NOT NULL DEFAULT 'expense',
    rollover            BOOLEAN NOT NULL DEFAULT FALSE,
    recurring           BOOLEAN NOT NULL DEFAULT FALSE,
    due_day             TEXT,
    due_amount          NUMERIC(12,2),
    pay_freq            TEXT,
    debt_account_id     TEXT,
    target_amount       NUMERIC(12,2),
    target_date         TEXT,
    contrib_freq        TEXT,
    default_budget      NUMERIC(12,2) NOT NULL DEFAULT 0,
    notes               TEXT,
    archived            BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order          INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE bcc_buckets ENABLE ROW LEVEL SECURITY;

CREATE POLICY bcc_buckets_user_policy ON bcc_buckets
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ─── TRANSACTIONS ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_transactions (
    id                          TEXT PRIMARY KEY,
    user_id                     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date                        DATE NOT NULL,
    description                 TEXT,
    type                        TEXT NOT NULL DEFAULT 'out',
    amount                      NUMERIC(12,2) NOT NULL DEFAULT 0,
    month_id                    TEXT NOT NULL,
    bucket_id                   TEXT,
    account_id                  TEXT,
    to_account_id               TEXT,
    debt_payment_account_id     TEXT,
    income_type                 TEXT,
    reconciled                  BOOLEAN NOT NULL DEFAULT FALSE,
    recurring                   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE bcc_transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY bcc_transactions_user_policy ON bcc_transactions
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ─── MONTHS ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_months (
    id          TEXT NOT NULL,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    year        INTEGER NOT NULL,
    month       INTEGER NOT NULL,
    label       TEXT NOT NULL,
    PRIMARY KEY (id, user_id)
);

ALTER TABLE bcc_months ENABLE ROW LEVEL SECURITY;

CREATE POLICY bcc_months_user_policy ON bcc_months
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ─── MONTH ALLOCATIONS ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_month_allocations (
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    month_id    TEXT NOT NULL,
    bucket_id   TEXT NOT NULL,
    amount      NUMERIC(12,2) NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, month_id, bucket_id)
);

ALTER TABLE bcc_month_allocations ENABLE ROW LEVEL SECURITY;

CREATE POLICY bcc_month_allocations_user_policy ON bcc_month_allocations
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ─── MONTH BUDGETS ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_month_budgets (
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    month_id    TEXT NOT NULL,
    bucket_id   TEXT NOT NULL,
    amount      NUMERIC(12,2) NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, month_id, bucket_id)
);

ALTER TABLE bcc_month_budgets ENABLE ROW LEVEL SECURITY;

CREATE POLICY bcc_month_budgets_user_policy ON bcc_month_budgets
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ─── MONTH ROLLOVER RELEASED ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_month_rollover_released (
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    month_id    TEXT NOT NULL,
    bucket_id   TEXT NOT NULL,
    amount      NUMERIC(12,2) NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, month_id, bucket_id)
);

ALTER TABLE bcc_month_rollover_released ENABLE ROW LEVEL SECURITY;

CREATE POLICY bcc_month_rollover_released_user_policy ON bcc_month_rollover_released
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ─── MONTH SKIPPED ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_month_skipped (
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    month_id    TEXT NOT NULL,
    bucket_id   TEXT NOT NULL,
    PRIMARY KEY (user_id, month_id, bucket_id)
);

ALTER TABLE bcc_month_skipped ENABLE ROW LEVEL SECURITY;

CREATE POLICY bcc_month_skipped_user_policy ON bcc_month_skipped
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ─── MONTH VAULT WITHDRAWALS ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_month_vault_withdrawals (
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    month_id    TEXT NOT NULL,
    bucket_id   TEXT NOT NULL,
    amount      NUMERIC(12,2) NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, month_id, bucket_id)
);

ALTER TABLE bcc_month_vault_withdrawals ENABLE ROW LEVEL SECURITY;

CREATE POLICY bcc_month_vault_withdrawals_user_policy ON bcc_month_vault_withdrawals
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ─── PAYCHECKS ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_paychecks (
    id          TEXT PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    label       TEXT NOT NULL,
    amount      NUMERIC(12,2) NOT NULL DEFAULT 0,
    freq        INTEGER NOT NULL DEFAULT 14,
    anchor_date TEXT,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE bcc_paychecks ENABLE ROW LEVEL SECURITY;

CREATE POLICY bcc_paychecks_user_policy ON bcc_paychecks
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ─── ALLOCATION RULES ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_allocation_rules (
    id          TEXT PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    rule_type   TEXT NOT NULL DEFAULT 'internal',
    value_type  TEXT NOT NULL DEFAULT 'fixed',
    value       NUMERIC(12,4) NOT NULL DEFAULT 0,
    bucket_id   TEXT,
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE bcc_allocation_rules ENABLE ROW LEVEL SECURITY;

CREATE POLICY bcc_allocation_rules_user_policy ON bcc_allocation_rules
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ─── VAULT TRANSFERS ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_vault_transfers (
    id              TEXT PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    from_bucket_id  TEXT NOT NULL,
    to_bucket_id    TEXT NOT NULL,
    amount          NUMERIC(12,2) NOT NULL,
    month_id        TEXT NOT NULL,
    reason          TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE bcc_vault_transfers ENABLE ROW LEVEL SECURITY;

CREATE POLICY bcc_vault_transfers_user_policy ON bcc_vault_transfers
    FOR ALL
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- ─── INDEXES ─────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_bcc_transactions_user_month
    ON bcc_transactions(user_id, month_id);

CREATE INDEX IF NOT EXISTS idx_bcc_transactions_user_account
    ON bcc_transactions(user_id, account_id);

CREATE INDEX IF NOT EXISTS idx_bcc_month_allocations_user_month
    ON bcc_month_allocations(user_id, month_id);

CREATE INDEX IF NOT EXISTS idx_bcc_month_budgets_user_month
    ON bcc_month_budgets(user_id, month_id);

CREATE INDEX IF NOT EXISTS idx_bcc_buckets_user_cat
    ON bcc_buckets(user_id, cat_id);
