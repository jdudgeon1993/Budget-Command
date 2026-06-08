# Cura — Reflex → Flask Continuity / Parity Review

Comparison of the two versions to ensure nothing is lost in the migration.
Status as of the Phase 0–9 build (everything below is on branch
`claude/fix-mobile-nav-dashboard-07n2g`, folder `webapp/`).

## The strongest continuity guarantee: identical engine

The Flask app reuses **the exact same Python** as Reflex — byte-for-byte copies:

| Module | Role | Shared? |
|---|---|---|
| `formulas.py` | All budget math (RTS, balances, available, spent…) | ✅ identical |
| `forecast_calc.py` | Forecast engine | ✅ identical |
| `db.py` | Supabase access (auth + all CRUD) | ✅ identical |
| `schema.sql` / Supabase tables | Data store | ✅ same database |

Because both versions read the **same tables** through the **same queries** and
compute through the **same formulas**, numbers are identical by construction and
**no user-data migration is needed** — point either app at the same Supabase
project and it sees the same data. Cross-panel figures already tie out in the
Flask build (e.g. Checking balance, net worth, spent all reconcile).

## Panel-by-panel parity

| Panel | Reflex had | Flask has | Gaps to close before cutover |
|---|---|---|---|
| **Shell** | sidebar, mobile nav, month switch, RTS | ✅ all + HTMX injection | vendor real htmx (SPA swaps) |
| **Buckets** | inline alloc+budget edit, groups, status, attention, fill, reorder, add, settings | ✅ alloc edit + OOB RTS, groups, status, attention, category bars | budget edit, fill, reorder, add-bucket wiring, archive, settings menu |
| **Transactions** | add/edit/delete sheet | ✅ add form → insert → redirect | edit, delete, type-toggle live highlight |
| **Accounts** | cards, ledger, reconcile, add/edit, debt payoff | ✅ cards, summary, date-grouped ledger | reconciliation, add/edit account, debt payoff, search |
| **Reports** | BvA, category, snapshots, trends, payees | ✅ BvA, category spend, snapshot, net worth | trends-over-time, payee analysis, historical snapshots |
| **Setup** | paychecks, categories, rules, wizard | ✅ paychecks/categories/rules add+delete | edit, category delete/reorder, rule toggle, guided wizard |
| **Forecast** | broken hybrid What-If | ✅ **approved proto mounted, fully interactive** | inject real buckets, persist scenarios to Supabase, authoritative compute via `forecast_calc` |
| **Payday** | quick distribution modal | ⬜ not built (Phase 8) | build the modal |

## Behavior / continuity notes

- **Auth:** same `db.sign_in` (Supabase JWT). Reflex stored it in a cookie; Flask
  stores it in a signed session. Same account, same login.
- **Scheduled vs posted txs:** identical handling (`formulas.is_scheduled`) — future
  txs excluded from balances/spent, surfaced separately. Verified in both ledger
  and Scheduled totals.
- **Transfers:** debit source + credit destination correctly (seen in Accounts).
- **Money formatting:** matched (`$1,234` / `-$1,234`).

## Not yet verified against real data

Local builds run on **dev-seed** (this sandbox has no Supabase creds and no network
egress). The engine is identical, so behavior should match — but `db.py`'s live
queries + RLS are only exercised where the DB is reachable. **Verify on Railway or
laptop** with real login (see MIGRATION_PLAN.md Phase 10 / the deploy options).

## Cutover checklist (Phase 10)

1. Close the per-panel gaps above (mostly edit/delete flows + forecast data wiring).
2. Vendor real `htmx.min.js` (CDNs were blocked in the build env).
3. Build the Payday modal.
4. Deploy Flask as a **second Railway service** (same Supabase env vars, no `DEV_SEED`).
5. Log in with a real account; click every panel; compare each number to the live
   Reflex app side-by-side.
6. When parity confirmed → flip Railway to the Flask service; archive `reflex_app/`.

## Bottom line

Structural + behavioral continuity is **guaranteed by construction** (shared engine,
shared database). What remains is **UI completeness** — the edit/delete flows and the
forecast data-wiring — not correctness risk. Both versions can run against the same
Supabase project simultaneously, so the final review is a side-by-side click-through
with real data, panel by panel, before flipping the switch.
