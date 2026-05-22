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

## 🔲 Phase 14: Plan tab — Forecast + What-If (More → Plan)

### 14A: Paycheck Forecast (highest priority)
Week-by-week cash flow projection based on real paycheck schedules and recurring bills.
- `/api/forecast?months=N`: projects N months forward from today (2/3/6/12/eoy)
- Paycheck schedule engine: `anchorDate` + `freq` (7/14/15/30) → exact future pay dates
  - `freq=15` = semi-monthly (always 1st and 15th, NOT every 15 days)
  - `freq=7/14` = walk from anchor in N-day steps
  - `freq=30` = same day each month as anchor
- Recurring bill engine: buckets with `recurring=true`, `dueDay`, `dueAmount`, `payFreq`
- External transfer rules (`ruleType="external"`) shown as outflows on pay dates
- Each week shows: paychecks in (green), bills out (red/amber), net, running balance
- SHORTFALL weeks flagged in red when running balance < 0
- "Add hypothetical" — test new expense or income without saving (e.g. new mortgage)
- Time range selector: 2 mo / 3 mo / 6 mo / 12 mo / End of Year

### 14B: What-If Sandbox
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
