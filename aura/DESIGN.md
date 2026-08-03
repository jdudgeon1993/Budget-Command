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

## The money model (why RTS can't drift)

```
Ready to Spend (RTS)  =  Unallocated  +  Σ over non-vault envelopes (funded − spent)
```

- **Unallocated** — one authoritative scalar per user (`aura_budget.unallocated`),
  the hero number. Mutated transactionally by income, refund, fund/defund, and
  rollover. Stored because fund/defund are *silent* (no ledger line to recompute
  from).
- **funded** — authoritative per envelope. Fund/defund move money between
  Unallocated and `funded` and leave no ledger row (the envelope state is the
  record).
- **spent** — NOT stored. Derived = Σ cleared expense transactions for that
  envelope in the current cycle. So editing/deleting a transaction recomputes
  RTS live; there is nothing cached to drift.
- **RTS** — always computed from the above, never stored.

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
| Accounts | **Cut for v1.** Total money = Unallocated + Σ funded; no separate bank/account entity. (Deliberate simplification — flag if you want reconciliation against a real bank balance.) |

## Flags to confirm before finalizing (the brief's open questions)

1. **Forecast/Ledger unification via `planned` rows — REJECTED (needs your OK).**
   The legacy schema hinted at making scheduled bills/paychecks be `planned`
   transaction rows. That **contradicts pillar 3** ("Forecast is never a source
   of truth, always computed") and the ledger rule ("descriptive/informational
   only"). So Aura keeps Forecast a pure computation over envelopes + `aura_bills`
   + `aura_paychecks`; the ledger holds only cleared money. Confirm you agree.
2. **Cross-cycle transaction edits (open-Q1).** Schema supports it via
   `tx.cycle_start` + immutable snapshots. Default mechanic: closed-cycle
   snapshots are immutable; current-cycle edits recompute live. The exact "edit a
   past tx → ripple a delta into *today*" behavior is left for Phase 3 — flag if
   you want that delta auto-applied vs. just shown.
3. **Sinking-fund due date (open-Q2).** Default: **passive milestone**, no
   automation — the fund just reaches its date; you decide next. No notification
   engine in v1.
4. **`bcc_scenarios` / What-If (open-Q7).** 0 rows in Cura, dropped from Aura v1.
   Say if you want it revived later.

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
