# Phase 2 Roadmap — Cura to 100 (Flask Purge Target)

All issues sourced from the feature-by-feature code review (June 2026).
Goal: close every gap so the Reflex app fully replaces the Flask app.

---

## Phase 1 — Financial Correctness  (numbers must be right)

### 1.1 Category budget header uses wrong fallback
**File:** `state.py` `_process` ~2284
Header row `cat_budget_sum` uses `b_budget()` only; per-bucket rows and the
scoreboard rollup also fold in `b.get("defaultBudget")`. Same category can
show two different "/ budget" totals.
**Fix:** apply `or float(b.get("defaultBudget") or 0)` in the header sum too.

### 1.2 PAID fires before FUNDED — status conflict
**File:** `state.py` `_bucket_status` ~41
`spent >= alloc → PAID` before FUNDED/OVERFUNDED checks, so a $10-allocated
$200-budgeted bucket shows PAID (green-ish) instead of FUNDING (amber).
**Fix:** reorder checks — OVER → OVERFUNDED → FUNDED → PAID → FUNDING.

### 1.3 Distribute RTS ignores `defaultBudget` fallback
**File:** `state.py` `distribute_rts` ~1873
Uses `b_budget()` only; buckets with no per-month budget row (rely on
`defaultBudget`) appear fully funded and are skipped.
**Fix:** use `b_budget(m, bid) or float(b.get("defaultBudget") or 0)`.

### 1.4 Forecast funding ignores rollover balance
**File:** `forecast_calc.py` `compute_forecast`
A bucket fully funded via rollover (not this-month alloc) appears "Needs
Funding" in the Forecast — contradicts what the Buckets panel shows.
**Fix:** use `bucket_available()` for funded check, not raw alloc.

### 1.5 Income-override scaling inconsistency
**File:** `forecast_calc.py`
`compute_forecast` and `compute_6month` scale the override on different bases
→ the KPI bar and the 6-month chart disagree for the same override value.
**Fix:** extract shared `_scale_income()` helper used by both.

---

## Phase 2 — Data Validation  (prevent silent bad data)

### 2.1 Self-transfer not blocked
**File:** `state.py` `submit_transaction`, `save_edit_tx`
A transfer where `sheet_account == sheet_to_account` can be saved; with one
account the default quietly points to itself.
**Fix:** validate `to_account != account` before saving XFR transactions.

### 2.2 Debt payment source not validated
**File:** `state.py` `save_debt_payment`
Source account can equal the debt account; overpayment beyond balance allowed.
**Fix:** block `from_account == debt_account`; warn but allow overpayment (don't cap).

### 2.3 Percent allocation rules can exceed 100%
**File:** `state.py` `add_alloc_rule_submit`
No validation that internal percent rules sum ≤ 100%.
**Fix:** on submit, sum active internal pct rules; warn (toast) if > 100%.

---

## Phase 3 — Setup Handler Hardening

### 3.1 Setup/cat/delete handlers skip auth-error + _busy
**File:** `state.py` — `add_paycheck_submit`, `delete_paycheck_item`,
`add_alloc_rule_submit`, `toggle_alloc_rule_item`, `delete_alloc_rule_item`,
`save_cat_edit`, `archive_category`, `move_cat_up`, `move_cat_down`
These use bare `except → toast`, never call `_on_db_error` or set `_busy`,
so expired tokens show wrong errors and the poll can race them.
**Fix:** convert to `async def`, add `_busy` guard, use `_on_db_error`.

### 3.2 Copy-pasted `load_all → _raw → _process` in ~15 handlers
**File:** `state.py` multiple handlers
The `_reload()` helper exists (state.py:1211) but is rarely used.
**Fix:** replace all `data = DB.load_all(...)` + `self._raw = data` + `_process`
blocks with `self._reload()`.

### 3.3 Destructive actions have no confirmation
**Affects:** delete rule, delete paycheck, archive category, archive account (one-click)
**Fix:** Add a small `rx.dialog` confirmation for irreversible actions.

---

## Phase 4 — Session Persistence  (biggest real-world UX defect)

### 4.1 Token lost on browser refresh
**File:** `state.py` — auth vars
`_access_token`/`_user_id` are backend-only; refresh = forced re-login.
**Fix:** change to `access_token = rx.Cookie(name="cura_at", secure=True,
max_age=86400*7, same_site="strict")` and same for `user_id`. The cookie
survives refresh and is scoped to the domain.

### 4.2 Token expires silently after ~1hr
**File:** `state.py` `on_dashboard_load`, `_on_db_error`
Supabase tokens expire; the app just shows a confusing error.
**Fix:** on auth failure, call `supabase.auth.refresh_session()` before
redirecting to login. Store refresh_token in a second cookie.

### 4.3 Login error generic for all failures
**File:** `state.py` `login`
Network/Supabase-down errors mislabeled "Invalid email or password."
**Fix:** detect non-auth exceptions and show "Could not connect — try again."

---

## Phase 5 — Dead Code + Label Fixes  (quick wins)

### 5.1 Timeline shows 30 days but text says 60
**File:** `state.py:701`, `forecast.py:690`
`compute_simple_timeline(n_days=30)` but empty-state says "next 60 days."
**Fix:** change call to `n_days=60` to match the promise.

### 5.2 Ledger "No transactions" empty state is dead code
**File:** `state.py` `filtered_ledger`, `ledger.py` ~950
`month_totals` header row keeps `length ≥ 1` so the `length()==0` guard never fires.
**Fix:** check `length() <= 1` (header only) or filter tx rows separately.

### 5.3 Dead handlers + helpers
- `delete_tx` in `state.py:1398` — unwired, never called
- `_btn` helper in `accounts.py:47` — never used
- `_accounts_stub`/`_stub_panel` imports in `dashboard.py` — dead stubs

### 5.4 Promo fields half-wired
**File:** `state.py` 2789, `accounts.py`
`is_promo`/`promo_end_date` state but no UI render. Either wire or remove.
**Fix:** add promo fields to the debt settings section in accounts.py.

### 5.5 "Insights" vs "Forecast" label mismatch
**File:** `dashboard.py` mobile tab bar ~128
Desktop sidebar: "Insights". Mobile tab: "Forecast". Same panel.
**Fix:** align to "Insights" everywhere.

---

## Phase 6 — Reports Improvements

### 6.1 "Paid (period)" label is wrong
**File:** `reports.py` ~547
The value is lifetime total, only the by-month breakdown is period-scoped.
**Fix:** rename to "Lifetime Paid" on the Debt Tracker card.

### 6.2 Payee grouping is case-sensitive
**File:** `state.py` `_build_reports` ~3344
"Costco" vs "COSTCO" split into separate entries.
**Fix:** group by `desc.strip().lower()` but display the most common casing.

### 6.3 `_build_reports` is a 280-line god-method
**File:** `state.py` 3103–3450
Five distinct report builders in one function; variance/status logic 3× duplicated.
**Fix:** extract `_build_bva()`, `_build_summary()`, `_build_trends()`,
`_build_payees()`, `_build_debt()` private methods + a `_fmt_variance()` helper.

### 6.4 SVG chart is fixed-width and non-responsive
**File:** `reports.py` ~386, `state.py` SVG builder
`width=520` hard-coded; on mobile the chart just scrolls.
**Fix:** use `viewBox` + `preserveAspectRatio` so it scales with container.

---

## Phase 7 — Flask Parity (missing features)

### 7.1 CSV export not in Reflex
**Flask:** `/api/export-csv` (4370-line app.py ~2693)
**Fix:** add `export_transactions_csv` event + `rx.download` trigger for the
current month's transactions as a CSV file.

### 7.2 Edit existing paycheck not in Reflex
**Flask:** `/api/update-paycheck`
Reflex only has add/delete; no way to rename a paycheck or change its amount.
**Fix:** add `open_edit_paycheck(pc_id)` + `save_edit_paycheck()` handlers and
an edit form to setup.py.

### 7.3 Unarchive category not in Reflex
**Flask:** `/api/unarchive-category`
Reflex only archives; once archived a category disappears forever from the UI.
**Fix:** add an "Archived" toggle in Setup to show/hide archived categories
with an Unarchive button → `unarchive_category(cid)` handler.

### 7.4 AI coach not ported (optional)
**Flask:** `/api/coach` (Google Gemini)
Requires `GOOGLE_API_KEY`. Nice to have but not blocking purge.
**Fix (later):** add a Coach tab to Insights, wire to Gemini API.

---

## Phase 8 — Paycheck Scheduling Engine

### 8.1 Frequency + anchor are decorative
**File:** `state.py` `_compute_payday_rows`
The freq/anchor stored in DB are never read during payday calculation.
**Fix:** build `_next_paycheck_dates(freq, anchor, n=3)` helper that returns
next N dates; show "Next: Jun 15" chip on paycheck cards in Setup.

### 8.2 Wire to Forecast
**File:** `forecast_calc.py`
Forecast currently uses all paychecks with all their income — scheduling would
let it know which paycheck lands in which period.
**Fix:** feed computed next-date list into forecast income placement.

---

## Phase 9 — Flask Purge

### 9.1 Feature parity checklist
All Phase 7 items complete:
- [x] Auth (login/signup/logout)
- [x] Budgets (full ZBB panel)
- [x] Ledger (add/edit/delete/search)
- [x] Accounts (add/edit/archive/debt payment)
- [x] Forecast + Timeline + What-If + scenarios
- [x] Setup (paychecks/rules/categories)
- [x] Reports (BvA/Summary/Trends/Payees/Debt)
- [ ] CSV export (Phase 7.1)
- [ ] Edit paycheck (Phase 7.2)
- [ ] Unarchive category (Phase 7.3)
- [ ] AI coach (Phase 7.4 — optional)

### 9.2 Remove Flask app
Delete `app/` directory and its dependencies from the repo.

### 9.3 Update Railway
Remove Flask service / update build command to Reflex only.

### 9.4 Cleanup
Remove `google-genai` from Flask requirements (it's unused in Reflex);
remove `flask`, `gunicorn` from root requirements if present.

---

## Scoring target

| Area | Current | Target |
|---|---|---|
| Buckets | 8.0 | 9.5 |
| Ledger | 8.0 | 9.5 |
| Navigation | 8.0 | 9.0 |
| Forecast | 7.5 | 9.0 |
| Accounts | 7.5 | 9.0 |
| Setup | 7.0 | 9.0 |
| Reports | 6.5 | 8.5 |
| Auth/Arch | 6.5 | 9.0 |
| **Overall** | **~7.5** | **9.0+** |
