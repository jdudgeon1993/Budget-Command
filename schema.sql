-- Cura — Budget Command Center
-- Full relational schema. All tables prefixed bcc_, RLS enforced via user_id = auth.uid()
-- Single source of truth — run the whole file on a fresh Supabase project.
-- For an existing project, every statement is idempotent (CREATE/ADD ... IF NOT EXISTS),
-- so re-running this file brings it up to date.


-- ─── ACCOUNTS ────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_accounts (
    id                  TEXT PRIMARY KEY,
    user_id             UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    type                TEXT NOT NULL DEFAULT 'budget',   -- budget | debt | credit
    color               TEXT NOT NULL DEFAULT '#3a7fc1',
    opening_balance     NUMERIC(12,2) NOT NULL DEFAULT 0,
    debt_apr            NUMERIC(8,3),
    debt_min_payment    NUMERIC(12,2),
    credit_limit        NUMERIC(12,2),
    is_promo            BOOLEAN NOT NULL DEFAULT FALSE,
    promo_end_date      TEXT,
    archived            BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order          INTEGER NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE bcc_accounts ENABLE ROW LEVEL SECURITY;
CREATE POLICY bcc_accounts_user_policy ON bcc_accounts
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

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
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- ─── BUCKETS ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_buckets (
    id              TEXT PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    cat_id          TEXT,
    name            TEXT NOT NULL,
    type            TEXT NOT NULL DEFAULT 'expense',   -- expense | vault | debt
    rollover        BOOLEAN NOT NULL DEFAULT FALSE,
    recurring       BOOLEAN NOT NULL DEFAULT FALSE,
    due_day         TEXT,                              -- 1-31 | 'eom' | NULL
    due_amount      NUMERIC(12,2),
    pay_freq        TEXT,                              -- monthly | biweekly | etc.
    debt_account_id TEXT,
    default_budget  NUMERIC(12,2) NOT NULL DEFAULT 0,
    target_amount   NUMERIC(12,2),                     -- goal/sinking: savings target
    target_date     TEXT,                              -- goal/sinking: YYYY-MM deadline
    contrib_freq    TEXT,                              -- goal/sinking: contribution frequency
    notes           TEXT,
    flex            BOOLEAN NOT NULL DEFAULT FALSE,
    archived        BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE bcc_buckets ENABLE ROW LEVEL SECURITY;
CREATE POLICY bcc_buckets_user_policy ON bcc_buckets
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- ─── TRANSACTIONS ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_transactions (
    id                      TEXT PRIMARY KEY,
    user_id                 UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    date                    DATE NOT NULL,
    description             TEXT,
    type                    TEXT NOT NULL DEFAULT 'out',   -- in | out | xfr | opening | adjustment
    amount                  NUMERIC(12,2) NOT NULL DEFAULT 0,
    month_id                TEXT NOT NULL,
    bucket_id               TEXT,
    account_id              TEXT,
    to_account_id           TEXT,
    debt_payment_account_id TEXT,
    reconciled              BOOLEAN NOT NULL DEFAULT FALSE,
    recurring               BOOLEAN NOT NULL DEFAULT FALSE,
    planned                 BOOLEAN NOT NULL DEFAULT TRUE,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Migration: add `planned` to existing installs (no-op if column exists)
ALTER TABLE bcc_transactions ADD COLUMN IF NOT EXISTS planned BOOLEAN NOT NULL DEFAULT TRUE;

ALTER TABLE bcc_transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY bcc_transactions_user_policy ON bcc_transactions
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- ─── MONTHS ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_months (
    id               TEXT NOT NULL,
    user_id          UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    year             INTEGER NOT NULL,
    month            INTEGER NOT NULL,                  -- 0-indexed (JS convention)
    label            TEXT NOT NULL,
    closed           BOOLEAN NOT NULL DEFAULT FALSE,
    notes            TEXT,
    ai_report        TEXT,
    closing_snapshot JSONB,
    closing_date     TEXT,
    PRIMARY KEY (id, user_id)
);

ALTER TABLE bcc_months ENABLE ROW LEVEL SECURITY;
CREATE POLICY bcc_months_user_policy ON bcc_months
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

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
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

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
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- ─── MONTH ROLLOVER RELEASED ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_month_rollover_released (
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    month_id    TEXT NOT NULL,
    bucket_id   TEXT NOT NULL,
    amount      NUMERIC(12,2) NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, month_id, bucket_id)
);

ALTER TABLE bcc_month_rollover_released ENABLE ROW LEVEL SECURITY;
CREATE POLICY bcc_month_rollover_released_user_policy ON bcc_month_rollover_released
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- ─── MONTH SKIPPED ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_month_skipped (
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    month_id    TEXT NOT NULL,
    bucket_id   TEXT NOT NULL,
    PRIMARY KEY (user_id, month_id, bucket_id)
);

ALTER TABLE bcc_month_skipped ENABLE ROW LEVEL SECURITY;
CREATE POLICY bcc_month_skipped_user_policy ON bcc_month_skipped
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

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
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- ─── PAYCHECKS ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_paychecks (
    id          TEXT PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    label       TEXT NOT NULL,
    amount      NUMERIC(12,2) NOT NULL DEFAULT 0,
    freq        INTEGER NOT NULL DEFAULT 14,            -- days between paychecks
    anchor_date TEXT,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE bcc_paychecks ENABLE ROW LEVEL SECURITY;
CREATE POLICY bcc_paychecks_user_policy ON bcc_paychecks
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- ─── ALLOCATION RULES ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_allocation_rules (
    id          TEXT PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    rule_type   TEXT NOT NULL DEFAULT 'internal',       -- internal | external
    value_type  TEXT NOT NULL DEFAULT 'fixed',          -- fixed | percent
    value       NUMERIC(12,4) NOT NULL DEFAULT 0,
    bucket_id   TEXT,
    active      BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE bcc_allocation_rules ENABLE ROW LEVEL SECURITY;
CREATE POLICY bcc_allocation_rules_user_policy ON bcc_allocation_rules
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

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
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- ─── VAULT RELEASE LOG ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS bcc_vault_release_log (
    id          TEXT PRIMARY KEY,
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    month_id    TEXT NOT NULL,
    bucket_id   TEXT NOT NULL,
    amount      NUMERIC(12,2) NOT NULL,
    reason      TEXT,
    is_planned  BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE bcc_vault_release_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY bcc_vault_release_log_user_policy ON bcc_vault_release_log
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- ─── SCENARIOS (What If) ─────────────────────────────────────────────────────
-- Stores saved What If scenarios per user. Previously localStorage-only.
CREATE TABLE IF NOT EXISTS bcc_scenarios (
    id              TEXT PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    allocations     JSONB NOT NULL DEFAULT '{}',        -- {bucket_id: amount}
    income_override NUMERIC(12,2),                      -- NULL = not overridden
    schedule        JSONB NOT NULL DEFAULT '{}',        -- {bucket_id: {month_id: false}}
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE bcc_scenarios ENABLE ROW LEVEL SECURITY;
CREATE POLICY bcc_scenarios_user_policy ON bcc_scenarios
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

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

CREATE INDEX IF NOT EXISTS idx_bcc_scenarios_user
    ON bcc_scenarios(user_id, sort_order);
