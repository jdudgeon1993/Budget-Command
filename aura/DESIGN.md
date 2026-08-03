# Aura — design decisions & rebuild plan

A ground-up rewrite of Cura around three pillars: **Envelopes** (authoritative
state), **Ledger** (descriptive record), **Forecast** (always computed). This
doc records the decisions baked into `aura/schema.sql` and flags everything the
brief asked to raise before the schema is finalized.

## Stack (confirmed with owner)

- **Flask + Supabase**, same as Cura today (deploys on Railway; runs locally
  under `DEV_SEED`). Not a FastAPI/self-host rewrite — that stays a future infra
  option, not this rebuild.
- **Reuse the existing Supabase database.** New `aura_*` tables live *alongside*
  the `bcc_*` tables. Cura keeps running untouched; **no data loss**. We build to
  parity, then cut over. (The brief's "isolated DB" mandate is knowingly deferred
  by the owner — the shared-project risk it flags is still real and worth a
  separate Supabase project or homelab Postgres eventually.)
- **Phased alongside**, not rip-and-replace. Nothing breaks mid-flight.

## The money model (one cash account; nothing can drift)

There is **one real cash account** (your checking). Envelopes don't hold separate
money — they're labels partitioning that one balance. Every dollar is either
Unallocated or funded into an envelope.

```
Available Balance  =  opening_balance + Σ(income + refund) − Σ(expense)   ← matches the bank
                   ≡  Unallocated + Σ over ALL envelopes (funded − spent)  ← invariant
Ready to Spend     =  Unallocated + Σ over NON-VAULT envelopes (funded − spent)
                   =  Available Balance − Σ over vault envelopes (funded − spent)
```

- **Available Balance** — the real cash number, transaction-driven so it can be
  reconciled against the actual bank. Equals Unallocated + Σ envelope available
  by construction. (This is Cura's "Available Balance"; RTS is its "Ready to Spend".)
- **Unallocated** — one authoritative scalar (`aura_budget.unallocated`), the hero
  number. Mutated transactionally by income, refund, fund/defund, and rollover.
  Stored because fund/defund are *silent* (no ledger line to recompute from).
- **funded** — authoritative per envelope; the amount placed in it. Fund/defund
  move money between Unallocated and `funded` with no ledger row. NOT decremented
  by spending.
- **spent** — NOT stored. Derived = Σ cleared expense transactions against the
  envelope in its active window (current cycle for spend envelopes; lifetime for
  non-resetting sinking/vault). Editing/deleting a transaction recomputes live.
- **Available Balance and RTS** — always computed, never stored.

## Decisions baked into the schema

| Area | Decision |
|---|---|
| Envelope types | One `aura_envelopes` table, `type ∈ {spend, sinking, vault}`. No debt/credit type, no wide god-table gated by many dead columns. |
| Vault protection | Enforced in the **API** (an expense transaction targeting a vault envelope is rejected). Vault money moves only via `aura_vault_transfers`. |
| Archive | A single `archived` flag. **No** shadow `retired_*` tables. |
| Month-close | One immutable snapshot pair (`aura_cycles` + `aura_cycle_envelopes`) replaces Cura's four fragmented `bcc_month_*` tables. |
| Bills | Separate lightweight `aura_bills`, Forecast-only, never funded, never envelopes. |
| Paychecks | **Multiple named paychecks** adopted now (`aura_paychecks`) — resolves open-Q3 toward the more flexible legacy shape. |
| Allocation rules | `aura_allocation_rules` (internal/external × percent/fixed); evaluated **only** inside the payday modal. |
| Ledger | One envelope per transaction (no splits). Refunds = income to Unallocated. Fund/defund silent. |
| Types & keys | uuid PKs, real FKs on every relationship, `DATE`/`NUMERIC(12,2)`/`SMALLINT`, CHECK-enum text. No date-as-text, no id-as-text. |
| Cash account | **One main cash account** (folded into `aura_budget`: `account_name` + `opening_balance`). Available Balance reconciles to the bank and equals Unallocated + Σ envelope available. Multiple distinct accounts (checking + savings) deferred to a later `aura_accounts` table if wanted. |

## Decisions locked with owner

1. **Forecast is purely computed** — REJECTED the legacy "planned transaction
   rows" unification (it contradicted pillar 3). Forecast is a pure computation
   over envelopes + `aura_bills` + `aura_paychecks`; the ledger holds only cleared
   money. ✔ confirmed.
2. **One main cash account** — the whole budget reconciles to it (see money
   model above). ✔ confirmed.
3. **Sinking-fund due date = passive milestone** — no automation/notifications in
   v1; the user decides what happens when a fund reaches its date. ✔ confirmed.
4. **Cross-cycle edits ripple into today** — editing a transaction in a
   already-closed cycle must keep *today* accurate. Mechanic: Available Balance is
   transaction-driven across all time, so it self-corrects the instant a past tx
   changes; the resulting delta lands in **today's Unallocated** (money reappears
   or vanishes from today's spendable), preserving the invariant. The closed
   cycle's snapshot stays as the immutable record of what was decided then, marked
   *amended* — the books are never reopened, but today reflects the truth.
   ✔ confirmed (resolves open-Q1). Implemented in Phase 3.

## Still open (non-blocking, decide later)

- **What-If / scenarios** (`bcc_scenarios`, 0 rows in Cura) — dropped from v1; say
  if you want it revived.

## Rebuild phases

- **Phase 1 — schema + this doc** ← you are here (review gate).
- **Phase 2** — `aura/` Flask package: Supabase data layer (`aura/db.py`) with
  real FK-backed reads/writes + `DEV_SEED` in-memory mode, and the core money
  operations (fund/defund, income, expense with vault guard, refund) with RTS
  computed.
- **Phase 3** — Envelopes UI, Ledger UI (day-grouped, running balance), Forecast
  (burn-paced from targets/due dates + bills/paychecks), payday allocation modal
  + funding plan, rollover/cycle snapshot job.
- **Phase 4** — parity check vs Cura, optional `bcc_* → aura_*` data migration,
  cut `/` over to Aura, retire Cura routes.
