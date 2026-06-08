-- Cura — Incremental migrations for existing Supabase projects
-- Run these statements in your Supabase SQL editor.
-- All statements are safe to re-run.

-- ─── bcc_months: columns added post-initial-schema ───────────────────────────
ALTER TABLE bcc_months ADD COLUMN IF NOT EXISTS closed           BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE bcc_months ADD COLUMN IF NOT EXISTS notes            TEXT;
ALTER TABLE bcc_months ADD COLUMN IF NOT EXISTS ai_report        TEXT;
ALTER TABLE bcc_months ADD COLUMN IF NOT EXISTS closing_snapshot JSONB;
ALTER TABLE bcc_months ADD COLUMN IF NOT EXISTS closing_date     TEXT;

-- ─── bcc_accounts: promo period fields ───────────────────────────────────────
ALTER TABLE bcc_accounts ADD COLUMN IF NOT EXISTS is_promo       BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE bcc_accounts ADD COLUMN IF NOT EXISTS promo_end_date TEXT;

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

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_policies
    WHERE tablename = 'bcc_scenarios' AND policyname = 'bcc_scenarios_user_policy'
  ) THEN
    CREATE POLICY bcc_scenarios_user_policy ON bcc_scenarios
      FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_bcc_scenarios_user
    ON bcc_scenarios(user_id, sort_order);

-- ─── bcc_buckets: goal/sinking fund fields ───────────────────────────────────
-- These columns are required for goal/sinking bucket editing to work.
-- Without them, ALL bucket saves fail (Supabase rejects unknown columns).
ALTER TABLE bcc_buckets ADD COLUMN IF NOT EXISTS target_amount NUMERIC(12,2);
ALTER TABLE bcc_buckets ADD COLUMN IF NOT EXISTS target_date   TEXT;
ALTER TABLE bcc_buckets ADD COLUMN IF NOT EXISTS contrib_freq  TEXT;

-- Vault release log (reason tracking for reporting)
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
