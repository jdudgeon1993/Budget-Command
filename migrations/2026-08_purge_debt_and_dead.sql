-- ═══════════════════════════════════════════════════════════════════════════
-- Cura DB cleanup — remove debt/credit data + dead schema objects
-- ═══════════════════════════════════════════════════════════════════════════
-- Run in the Supabase SQL editor (Dashboard → SQL). The app no longer reads or
-- writes any of the columns/tables/rows below, so removing them only declutters.
--
-- ⚠ BACK UP FIRST. Every DELETE / DROP here is irreversible.
--   Supabase → Database → Backups (or `pg_dump`) before running Steps 1–3.
-- ⚠ Run in the SQL editor as owner → this bypasses RLS and touches ALL rows.
--   That's intended for a single-user database; know that going in.
--
-- Do STEP 0 first and read the numbers. Only then run STEP 1–3.
-- Checking/Savings balances are unaffected: payments made FROM a cash account
-- keep their cash-account row and stay; only rows that live ON a debt/credit
-- account (interest charges, that account's opening balance) are removed.
-- ═══════════════════════════════════════════════════════════════════════════


-- ── STEP 0 — PREVIEW (read-only; changes nothing) ───────────────────────────
SELECT id, name, type FROM bcc_accounts WHERE type IN ('debt','credit');
SELECT count(*) AS debt_account_txs_to_delete
  FROM bcc_transactions
 WHERE account_id IN (SELECT id FROM bcc_accounts WHERE type IN ('debt','credit'));
SELECT count(*) AS transfers_pointing_at_debt
  FROM bcc_transactions
 WHERE to_account_id IN (SELECT id FROM bcc_accounts WHERE type IN ('debt','credit'));
SELECT count(*) AS dead_rollover_rows FROM bcc_month_rollover_released;


-- ── STEP 1 — DELETE debt/credit data ────────────────────────────────────────
BEGIN;

-- 1a. Transactions that live ON a debt/credit account (interest, its opening).
DELETE FROM bcc_transactions
 WHERE account_id IN (SELECT id FROM bcc_accounts WHERE type IN ('debt','credit'));

-- 1b. Neutralize transfers whose destination was a debt account (keeps the
--     cash-side outflow, just drops the now-meaningless destination pointer).
UPDATE bcc_transactions SET to_account_id = NULL
 WHERE to_account_id IN (SELECT id FROM bcc_accounts WHERE type IN ('debt','credit'));

-- 1c. Delete the debt/credit accounts themselves.
DELETE FROM bcc_accounts WHERE type IN ('debt','credit');

COMMIT;


-- ── STEP 2 — DROP dead columns (unreferenced by the app after the debt purge) ─
ALTER TABLE bcc_accounts        DROP COLUMN IF EXISTS debt_apr;
ALTER TABLE bcc_accounts        DROP COLUMN IF EXISTS debt_min_payment;
ALTER TABLE bcc_accounts        DROP COLUMN IF EXISTS credit_limit;
ALTER TABLE bcc_accounts        DROP COLUMN IF EXISTS is_promo;
ALTER TABLE bcc_accounts        DROP COLUMN IF EXISTS promo_end_date;
ALTER TABLE bcc_buckets         DROP COLUMN IF EXISTS debt_account_id;
ALTER TABLE bcc_retired_buckets DROP COLUMN IF EXISTS debt_account_id;
ALTER TABLE bcc_transactions    DROP COLUMN IF EXISTS debt_payment_account_id;


-- ── STEP 3 — DROP the dead table (defined in schema, queried by no code) ─────
DROP TABLE IF EXISTS bcc_month_rollover_released;


-- ── STEP 4 — VERIFY (optional; all should return 0 rows / 0 count) ──────────
SELECT count(*) AS remaining_debt_accounts FROM bcc_accounts WHERE type IN ('debt','credit');
-- Column list should no longer show any debt_/credit_/promo_ columns:
SELECT column_name FROM information_schema.columns
 WHERE table_name = 'bcc_accounts' ORDER BY ordinal_position;
