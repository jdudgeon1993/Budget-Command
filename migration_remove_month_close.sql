-- Migration: remove month-close + opt-in rollover remnants
--
-- Context: month-close was already orphaned in the UI (no active route linked
-- to it), and rollover is now always-on — every bucket's unspent allocation
-- carries forward automatically, like a real envelope. This migration drops
-- the now-unused tables/columns that supported the old explicit-close /
-- opt-in-rollover model.
--
-- Review before running. Not applied automatically — run manually against
-- Supabase when ready (e.g. via the SQL editor).

-- Drop tables that backed "release rollover to pool" and "skipped bucket" features
DROP TABLE IF EXISTS bcc_month_rollover_released;
DROP TABLE IF EXISTS bcc_month_skipped;

-- Drop month-close columns from bcc_months
ALTER TABLE bcc_months
    DROP COLUMN IF EXISTS closed,
    DROP COLUMN IF EXISTS closing_snapshot,
    DROP COLUMN IF EXISTS closing_date;

-- Drop the opt-in rollover toggle from bcc_buckets (rollover is now always-on)
ALTER TABLE bcc_buckets
    DROP COLUMN IF EXISTS rollover;
