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

## 🔲 Phase 13: Reports
- Monthly spending breakdown by category/bucket
- Income vs. spending chart
- Net worth over time (all accounts)
- Export to CSV

## 🔲 Phase 14: What-If Simulator
- Adjust allocations on a scratch copy of the month without saving
- "What if I skip this bucket?" projections
- Debt payoff calculator / snowball vs. avalanche comparison

## 🔲 Phase 15: Coach AI
- Contextual spending analysis against budget
- Proactive alerts (over budget, large unallocated balance, upcoming due dates)
- Conversational Q&A about financial state

## 🔲 Phase 16: Final Polish
- PWA / home screen install
- Push notifications for due dates
- Multi-user / shared budget support
- Onboarding flow for new users
