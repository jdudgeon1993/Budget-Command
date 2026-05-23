# Budget Command — Phase Roadmap

## ✅ Phase 1–8: Foundation
Core Flask app, Supabase auth, bucket/category/account CRUD, transaction ledger,
payday modal, vault/rollover logic, debt payment flows.

## ✅ Phase 9: Stability
- Fragment completeness (bucket/account server-rendered fragments)
- Lazy-refresh ledger on open
- `switchBucketType` live updates
- Paycheck allocations update Allocated column live
- Rollover made silent (behind-the-scenes); Release UI removed; checkbox kept

## ✅ Phase 10: DB Migration — JSON blob → Relational Tables
- `schema.sql`: 13 relational Supabase tables (`bcc_*`) with RLS
- `_load(uid, token)`: assembles canonical camelCase dict from SQL for formula compatibility
- Targeted save helpers replace single-blob writes
- Browser-accessible `/api/run-migration` endpoint for Railway deployment (removed after use)
- `formulas.py` and `_live_state()` untouched

## ✅ Phase 11: UX Polish — Math Inputs, Calculator, Sticky Headers
- `evalMathExpr()`: arithmetic in any number field (e.g. `100+25` → `$125`)
- Calculator popover: numpad + operator buttons, seeds from current value, APPLY commits
- Sticky table headers: `position:sticky` on all `.data-table thead th`
- `wireMathInputs()` wires calc triggers on page load + dynamic fragment injection

## ✅ Phase 12: Due Date Status Badges
- `_due_info(due_day, active_mid, status)`: computes label (`DUE 5D`, `DUE TODAY`, `OVERDUE 2D`)
  and urgency (`overdue`, `today`, `soon` ≤7d, `upcoming` ≤14d, `far`)
- Shown inline in the status column below the status badge (only when not PAID/FUNDED/OVER)
- Color-coded: red=overdue/today, amber=soon, yellow=upcoming, muted=far
- `refreshValues()` patches `[data-due-id]` spans live after every mutation
- Supports numeric day, "eom" (end of month), clamped to actual month length

## ✅ Phase 13: Reports (More → Reports tab)
- 7-tab YNAB-style suite: Summary, Budget, Cash Flow, YTD, Income, Trends, Net Worth
- Pure SVG charts (no libraries): donut, horizontal bars, grouped bars, line chart
- `/api/reports`: category breakdown, 12-month trends, YTD, income sources, net worth history
- `/api/export-csv`: CSV download of active month's transactions
- RTS in reports fixed to use `_rts_now(data)` (same formula as banner)
- Moved into More tab (alongside Accounts, Settings) — removed standalone nav tab

## ✅ Phase 14A: Paycheck Forecast (More → Plan)
Week-by-week cash flow projection anchored to real paycheck schedules.

### Engine
- `/api/forecast?months=N`: projects N months forward; range selector 2/3/6/12/eoy
- Paycheck schedule: `anchorDate` + `freq` (7=weekly, 14=biweekly, 15=semi-monthly, 30=monthly)
  - `freq=15` = always 1st and 15th, NOT every 15 days
  - Ceiling-division fast-forward so ancient anchors don't triple-generate dates
- Pre-paycheck gap period: today → day before first upcoming paycheck
- Bill engine: two pools pulled automatically — no `recurring` flag required
  - **Dated bills**: any bucket with `dueDay` + amount → calendar-anchored deductions
  - **Freq-only bills**: bucket with `payFreq` + amount, no `dueDay` → spending-rate
    deductions (gas, groceries); anchored to period start, weekly/biweekly/monthly
- Overdue detection: gap period scans back to month start for unpaid bills
- Funded check: current month uses real `bBudget`/`bAlloc` data; future months fall
  back to `defaultBudget > 0` as the funded signal (no more all-red projections)
- Internal alloc rules: only vault-type buckets deduct from balance; expense rules
  are informational (earmarked, no cash movement)
- Age of Money: 14-day average balance ÷ 90-day average daily spend

### Period math
- `period_net` = income − routes-out − **unfunded** obligations only
  Pre-funded clearings are real outflows but already handled — excluded from pressure signal
- `period_cleared` = total of pre-funded bill clearings (shown separately)
- Per-period forward minimum Safe to Spend: `min(end_balance[i:])`
  with 🟢🟡🔴 dot indicator at bottom of each expanded card
- ✓ Pre-Funded badge on period header when all obligations are covered

### UI
- Summary bar: Start | Income | Routes Out | Pre-Funded | Needs Funding | Safe to Spend
- Account balance chip selector (multi-select or custom amount)
- "Awaiting paycheck" toggle — hides income on first period if not yet received
- Planned expenses overlay (client-side, per-period injection)
- Expandable period cards; shortfall and first period auto-open

### Removals / fixes
- Removed `recurring` checkbox from bucket editor — intent is expressed by the fields themselves
- Removed `@media (max-width: 640px)` column-hiding rules — consistent layout at all sizes,
  `clamp()` font scaling throughout

## 🔲 Phase 14B: What-If Sandbox
Scratch copy of the current month's bucket table — no server saves.
- Editable allocations update a "Simulated RTS" banner live (client-side math)
- Uses existing `bucket_rollover` + `bucket_spent` from liveState for accuracy
- Delta display vs. real RTS ("Freed $200 vs. actual")
- Reset button | "Apply to Month" button (optional push to real allocations)

## 🔲 Phase 15: Coach AI
- Contextual spending analysis against budget
- Proactive alerts (over budget, large unallocated balance, upcoming due dates)
- Conversational Q&A about financial state

## 🔲 Phase 16: Final Polish
- PWA / home screen install
- Push notifications for due dates
- Multi-user / shared budget support
- Onboarding flow for new users
