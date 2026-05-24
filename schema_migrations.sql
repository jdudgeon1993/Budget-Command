-- Cura — Incremental migrations for existing Supabase projects
-- Run these statements in order against your existing database.
-- Each statement is idempotent (IF NOT EXISTS / IF NOT EXISTS).

-- ─── bcc_months: columns added post-initial-schema ───────────────────────────
ALTER TABLE bcc_months ADD COLUMN IF NOT EXISTS closed           BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE bcc_months ADD COLUMN IF NOT EXISTS notes            TEXT;
ALTER TABLE bcc_months ADD COLUMN IF NOT EXISTS ai_report        TEXT;
ALTER TABLE bcc_months ADD COLUMN IF NOT EXISTS closing_snapshot JSONB;
ALTER TABLE bcc_months ADD COLUMN IF NOT EXISTS closing_date     TEXT;

-- ─── bcc_accounts: promo period fields ───────────────────────────────────────
ALTER TABLE bcc_accounts ADD COLUMN IF NOT EXISTS is_promo       BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE bcc_accounts ADD COLUMN IF NOT EXISTS promo_end_date TEXT;

-- ─── bcc_buckets: remove unused sinking-fund fields ──────────────────────────
-- These columns exist in some deployments but are not used by the app.
-- Only run these if you want to clean up the schema; safe to skip.
-- ALTER TABLE bcc_buckets DROP COLUMN IF EXISTS target_amount;
-- ALTER TABLE bcc_buckets DROP COLUMN IF EXISTS target_date;
-- ALTER TABLE bcc_buckets DROP COLUMN IF EXISTS contrib_freq;

-- ─── bcc_transactions: remove unused income_type field ───────────────────────
-- ALTER TABLE bcc_transactions DROP COLUMN IF EXISTS income_type;

-- ─── bcc_scenarios: new table for What If scenarios ──────────────────────────
CREATE TABLE IF NOT EXISTS bcc_scenarios (
    id              TEXT PRIMARY KEY,
    user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name            TEXT NOT NULL,
    allocations     JSONB NOT NULL DEFAULT '{}',
    income_override NUMERIC(12,2),
    schedule        JSONB NOT NULL DEFAULT '{}',
    sort_order      INTEGER NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE bcc_scenarios ENABLE ROW LEVEL SECURITY;

CREATE POLICY bcc_scenarios_user_policy ON bcc_scenarios
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE INDEX IF NOT EXISTS idx_bcc_scenarios_user
    ON bcc_scenarios(user_id, sort_order);
