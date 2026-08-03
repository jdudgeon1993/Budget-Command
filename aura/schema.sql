-- ─────────────────────────────────────────────────────────────────────────────
-- Aura — clean zero-based envelope budgeting schema
-- ─────────────────────────────────────────────────────────────────────────────
-- Prefix: aura_*  (coexists with the legacy bcc_* Cura tables in the SAME
-- Supabase project — Cura keeps running untouched while Aura is built alongside).
--
-- Design rules carried from the Aura brief:
--   • Three envelope TYPES in one table, but NO debt/credit fields, NO shadow
--     "retired_*" archive tables (an `archived` flag is enough), and NO four-way
--     month-close table sprawl (one snapshot pair: aura_cycles + _cycle_envelopes).
--   • REAL foreign keys on every relationship that matters. The DB must never be
--     able to hold a transaction that points at a non-existent envelope.
--   • Proper types: date is DATE, money is NUMERIC(12,2), day-of-month is SMALLINT,
--     enums are CHECK-constrained TEXT. No dates-as-text, no freq-as-text-vs-int.
--   • uuid PKs (gen_random_uuid()), user_id UUID → auth.users, RLS via auth.uid()
--     — identical to the surrounding Supabase project conventions.
--
-- Money model (everything ties to ONE real cash account; nothing cached):
--   There is a single main cash account (your checking). Envelopes do NOT hold
--   separate money — they are labels partitioning that one balance. Every dollar
--   is either Unallocated or funded into some envelope.
--
--   Available Balance (must match the bank) — transaction-driven:
--     = opening_balance + Σ(income + refund) − Σ(expense)
--     ≡ Unallocated + Σ over ALL envelopes of (funded − spent)      [invariant]
--
--   Ready to Spend (RTS) — the same balance minus locked + spoken-for money:
--     = Unallocated + Σ over NON-VAULT envelopes of (funded − spent)
--     = Available Balance − Σ over vault envelopes of (funded − spent)
--
--   `funded` is authoritative placed money (fund/defund mutate it silently and
--   are NOT decremented by spending). `spent` is DERIVED = Σ cleared expense
--   transactions in the envelope's active window, so editing a transaction
--   recomputes everything live (never stored/cached). Both Available Balance and
--   RTS are computed, never stored — they cannot drift.
--
-- Idempotent: every statement is CREATE ... IF NOT EXISTS; safe to re-run.
-- ─────────────────────────────────────────────────────────────────────────────


-- ─── BUDGET (per-user singleton: the main cash account + Unallocated + cycle) ──
--   Folds the single main cash account into the per-user budget row: one real
--   checking balance the whole envelope system reconciles to (Available Balance
--   = opening_balance + Σ income/refund − Σ expense ≡ Unallocated + Σ funded−spent).
--   Multiple distinct reconcilable accounts (e.g. checking + savings) are a
--   deliberate v1 deferral — envelopes partition this one balance.
CREATE TABLE IF NOT EXISTS aura_budget (
    user_id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    account_name     TEXT NOT NULL DEFAULT 'Checking',
    opening_balance  NUMERIC(12,2) NOT NULL DEFAULT 0,   -- cash-account starting point
    unallocated      NUMERIC(12,2) NOT NULL DEFAULT 0,   -- the hero number the user watches
    cycle_start      DATE NOT NULL,                       -- first day of the current open cycle
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE aura_budget ENABLE ROW LEVEL SECURITY;
CREATE POLICY aura_budget_user ON aura_budget
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());


-- ─── CATEGORIES (flat display grouping only — no nesting, fully optional) ──────
CREATE TABLE IF NOT EXISTS aura_categories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    color       TEXT NOT NULL DEFAULT '',
    sort_order  INTEGER NOT NULL DEFAULT 0,
    archived    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE aura_categories ENABLE ROW LEVEL SECURITY;
CREATE POLICY aura_categories_user ON aura_categories
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());


-- ─── ENVELOPES (the only authoritative budget state; three types) ─────────────
--   spend    — normal monthly category. `target` monthly; optional `due_day`.
--              Resets at rollover: leftover (funded−spent) returns to Unallocated.
--   sinking  — goal with a `target` amount + `target_date` beyond this cycle.
--              `funded` persists across cycles untouched (does NOT reset).
--   vault    — internal savings NO expense transaction may ever touch. Money moves
--              in/out ONLY via aura_vault_transfers. Enforced in the API layer.
CREATE TABLE IF NOT EXISTS aura_envelopes (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    category_id  UUID REFERENCES aura_categories(id) ON DELETE SET NULL,
    name         TEXT NOT NULL,
    type         TEXT NOT NULL CHECK (type IN ('spend','sinking','vault')),
    target       NUMERIC(12,2),                       -- spend: monthly target; sinking: goal
    due_day      SMALLINT CHECK (due_day BETWEEN 1 AND 31),   -- spend: day-of-month due
    target_date  DATE,                                -- sinking: goal deadline
    funded       NUMERIC(12,2) NOT NULL DEFAULT 0,    -- authoritative placed money
    sort_order   INTEGER NOT NULL DEFAULT 0,
    archived     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE aura_envelopes ENABLE ROW LEVEL SECURITY;
CREATE POLICY aura_envelopes_user ON aura_envelopes
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE INDEX IF NOT EXISTS aura_envelopes_user_idx ON aura_envelopes(user_id);
CREATE INDEX IF NOT EXISTS aura_envelopes_cat_idx  ON aura_envelopes(category_id);


-- ─── TRANSACTIONS (the ledger — descriptive record of CLEARED money only) ─────
--   expense — money leaves an envelope. envelope_id REQUIRED (real FK) and the
--             API rejects any expense whose envelope is a vault.
--   income  — money enters Unallocated. envelope_id NULL.
--   refund  — treated as income to Unallocated (never returned to an envelope).
--   NOTE: fund/defund (Unallocated ↔ envelope) are SILENT placements — they do
--   NOT get a ledger row here; the envelope's `funded` is their record.
CREATE TABLE IF NOT EXISTS aura_transactions (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    envelope_id  UUID REFERENCES aura_envelopes(id) ON DELETE RESTRICT,  -- required for expense
    kind         TEXT NOT NULL CHECK (kind IN ('expense','income','refund')),
    amount       NUMERIC(12,2) NOT NULL CHECK (amount >= 0),   -- sign implied by kind
    tx_date      DATE NOT NULL,
    cycle_start  DATE NOT NULL,                       -- the cycle this tx belongs to
    note         TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- an expense must name an envelope; income/refund must not
    CONSTRAINT aura_tx_envelope_shape CHECK (
        (kind = 'expense' AND envelope_id IS NOT NULL) OR
        (kind IN ('income','refund') AND envelope_id IS NULL)
    )
);
ALTER TABLE aura_transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY aura_transactions_user ON aura_transactions
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE INDEX IF NOT EXISTS aura_tx_user_cycle_idx ON aura_transactions(user_id, cycle_start);
CREATE INDEX IF NOT EXISTS aura_tx_envelope_idx   ON aura_transactions(envelope_id);


-- ─── BILLS (lightweight "known future deduction" — Forecast ONLY) ─────────────
--   Bills are explicitly NOT envelopes and are never funded/tracked as state.
--   They exist solely so Forecast can apply scheduled lump-sum deductions.
CREATE TABLE IF NOT EXISTS aura_bills (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name         TEXT NOT NULL,
    amount       NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    cadence      TEXT NOT NULL CHECK (cadence IN ('weekly','biweekly','monthly','yearly','once')),
    due_day      SMALLINT CHECK (due_day BETWEEN 1 AND 31),  -- monthly/yearly anchor
    anchor_date  DATE,                                        -- weekly/biweekly/once anchor
    active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE aura_bills ENABLE ROW LEVEL SECURITY;
CREATE POLICY aura_bills_user ON aura_bills
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());


-- ─── PAYCHECKS (multiple named incomes; Forecast projects pay dates forward) ──
CREATE TABLE IF NOT EXISTS aura_paychecks (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    name         TEXT NOT NULL,
    amount       NUMERIC(12,2) NOT NULL CHECK (amount >= 0),
    cadence      TEXT NOT NULL CHECK (cadence IN ('weekly','biweekly','semimonthly','monthly')),
    anchor_date  DATE NOT NULL,
    active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE aura_paychecks ENABLE ROW LEVEL SECURITY;
CREATE POLICY aura_paychecks_user ON aura_paychecks
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());


-- ─── ALLOCATION RULES (evaluated ONLY inside the payday allocation modal) ─────
--   internal — route a % or fixed amount of a paycheck to a specific envelope
--              (envelope_id required; may target vaults/sinking funds).
--   external — a genuine cross-account transfer; informational/manual-confirm
--              only (Aura never moves real bank money). envelope_id NULL.
CREATE TABLE IF NOT EXISTS aura_allocation_rules (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    kind         TEXT NOT NULL CHECK (kind IN ('internal','external')),
    value_type   TEXT NOT NULL CHECK (value_type IN ('percent','fixed')),
    value        NUMERIC(12,2) NOT NULL CHECK (value >= 0),
    envelope_id  UUID REFERENCES aura_envelopes(id) ON DELETE CASCADE,  -- required for internal
    label        TEXT,                                -- external: destination name
    active       BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order   INTEGER NOT NULL DEFAULT 0,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT aura_rule_internal_needs_envelope CHECK (
        kind = 'external' OR envelope_id IS NOT NULL
    )
);
ALTER TABLE aura_allocation_rules ENABLE ROW LEVEL SECURITY;
CREATE POLICY aura_allocation_rules_user ON aura_allocation_rules
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());


-- ─── VAULT TRANSFERS (the ONLY way money moves in/out of a vault) ─────────────
--   NULL from/to = Unallocated. Regular fund/defund is silent, but vault moves
--   are recorded here because a transfer is the only lever a vault has, and the
--   `reason` gives an audit trail the silent envelope state can't.
CREATE TABLE IF NOT EXISTS aura_vault_transfers (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    from_envelope_id  UUID REFERENCES aura_envelopes(id) ON DELETE SET NULL,  -- NULL = Unallocated
    to_envelope_id    UUID REFERENCES aura_envelopes(id) ON DELETE SET NULL,  -- NULL = Unallocated
    amount            NUMERIC(12,2) NOT NULL CHECK (amount > 0),
    reason            TEXT,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT aura_vault_transfer_distinct CHECK (
        from_envelope_id IS DISTINCT FROM to_envelope_id
    )
);
ALTER TABLE aura_vault_transfers ENABLE ROW LEVEL SECURITY;
CREATE POLICY aura_vault_transfers_user ON aura_vault_transfers
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());


-- ─── CYCLE SNAPSHOTS (rollover history — replaces the four bcc_month_* tables) ─
--   At each rollover a closed cycle is snapshotted so the user can still review
--   the just-closed cycle. Snapshots are immutable; live envelopes reset forward.
CREATE TABLE IF NOT EXISTS aura_cycles (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id            UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    cycle_start        DATE NOT NULL,
    cycle_end          DATE NOT NULL,
    unallocated_close  NUMERIC(12,2) NOT NULL DEFAULT 0,
    closed_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, cycle_start)
);
ALTER TABLE aura_cycles ENABLE ROW LEVEL SECURITY;
CREATE POLICY aura_cycles_user ON aura_cycles
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

CREATE TABLE IF NOT EXISTS aura_cycle_envelopes (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    cycle_id     UUID NOT NULL REFERENCES aura_cycles(id) ON DELETE CASCADE,
    envelope_id  UUID REFERENCES aura_envelopes(id) ON DELETE SET NULL,  -- may be deleted later
    name         TEXT NOT NULL,                       -- denormalized at snapshot time
    type         TEXT NOT NULL,
    target       NUMERIC(12,2),
    funded       NUMERIC(12,2) NOT NULL DEFAULT 0,
    spent        NUMERIC(12,2) NOT NULL DEFAULT 0,
    rolled       NUMERIC(12,2) NOT NULL DEFAULT 0,    -- leftover returned to Unallocated (neg if overspent)
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE aura_cycle_envelopes ENABLE ROW LEVEL SECURITY;
CREATE POLICY aura_cycle_envelopes_user ON aura_cycle_envelopes
    FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
CREATE INDEX IF NOT EXISTS aura_cycle_env_cycle_idx ON aura_cycle_envelopes(cycle_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- 10 tables total. Compare to Cura's 18 bcc_* tables:
--   dropped entirely — bcc_accounts (+debt/credit/APR), bcc_retired_buckets,
--   bcc_retired_categories, bcc_month_allocations, bcc_month_budgets,
--   bcc_month_handled, bcc_month_skipped, bcc_month_rollover_released,
--   bcc_month_vault_withdrawals, bcc_vault_release_log, bcc_scenarios.
--   Every debt field, every shadow-archive table, and the four-way month-close
--   split are gone; four month-close tables collapse to one snapshot pair.
-- ─────────────────────────────────────────────────────────────────────────────
