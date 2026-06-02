# Budget Command — Roadmap to 100

> Current honest score: **78/100**. This document is the path to 100.
> It is ordered by **reliability-per-unit-effort**: the earliest phases buy
> the most real-world stability for the least churn. Nothing here is a
> rewrite — it is a hardening campaign followed by a polish campaign.

Legend:
- **Impact** = how much it moves the score / protects user data
- **Effort** = rough size (S < half day, M ~1 day, L ~2–3 days)
- File references use `path:line` against the current `claude/fix-mobile-nav-dashboard-07n2g` branch.

---

## PHASE 1 — Concurrency & State Safety  *(Impact: HIGH · Effort: M)*

**Goal:** No user edit is ever silently lost. The 30-second background poll
must never clobber in-flight work.

### 1.1 Make the background poll edit-aware
- **Where:** `state.py:1209` `poll_data()`
- **Problem:** Every 30s it reassigns `self._raw` from the DB inside
  `async with self`. If the user has an optimistic edit in `_raw` that
  hasn't persisted, it's overwritten. Worse: a poll can reload a deletion
  made in another tab while a pending save re-writes the stale value
  (classic lost update).
- **Fix:**
  1. Add a `_dirty: bool = False` (or `_pending_writes: int`) backend var.
  2. Set it `True` at the top of every mutating handler, clear it after the
     DB write + reload completes.
  3. In `poll_data`, **skip the reload** when `_dirty` is set (try again next
     tick). Optionally also skip when a modal/edit field is open
     (`editing_bid`, `editing_budget_bid`, `bsettings_open`, `sheet_open`).
- **Acceptance:** Start editing an allocation, wait 30s without submitting —
  your in-progress value is still there. Delete a bucket in tab A; tab B's
  next poll reflects the deletion and does not resurrect it.

### 1.2 Serialize mutations against the poll
- **Where:** all async mutating handlers + `poll_data`
- **Problem:** Reflex's `async with self` lock is per-handler; there's no
  global guard preventing a save and a poll from interleaving on
  `self._raw["months"][mid]["allocations"]`.
- **Fix:** The `_dirty` flag from 1.1 covers most of this. For belt-and-
  suspenders, gate the poll behind "no mutation in the last N seconds."
- **Acceptance:** Rapidly fund several buckets while the poll interval
  elapses — final DB state matches the UI exactly.

### 1.3 Make the poll back off when the tab is hidden
- **Where:** `state.py:1209`
- **Enhancement:** Skip polling when the browser tab isn't visible (reduces
  needless DB load and the race surface). Reflex exposes page visibility via
  an `on_load`/JS bridge, or simply widen the interval to 60s.
- **Acceptance:** Idle background tabs stop hammering the DB.

---

## PHASE 2 — Error Handling & Resilience  *(Impact: HIGH · Effort: M)*

**Goal:** Every failure is either recovered or shown. No silent data loss,
no dead session.

### 2.1 Fix the one inconsistent handler
- **Where:** `state.py:1389` `save_budget_edit()`
- **Problem:** It's the only **sync** mutating handler, with **no try/except**
  and **no auth-error redirect**, while every sibling is async + guarded. On
  token expiry it throws uncaught instead of bouncing to login; it blocks the
  event loop on the DB round-trip.
- **Fix:** Convert to `async`, wrap DB calls in the standard
  `try / except DB.is_auth_error → redirect / except → reload + toast`
  pattern used by `save_alloc_edit()` (`state.py:1428`).
- **Acceptance:** Let the session expire, press Enter on a budget edit →
  redirected to login, not a crash.

### 2.2 Central auth-error guard
- **Where:** new helper in `state.py`; applied to every handler
- **Problem:** Token expiry is handled per-handler and inconsistently. Some
  paths redirect, others (`load_payees` `state.py:3011`, `poll_data`,
  `save_budget_edit`) just fail.
- **Fix:** Add a small decorator/util, e.g. `_guard(self, fn)` or a
  `_handle_db_error(e, mid)` method that all `except` blocks call. It
  detects `DB.is_auth_error`, clears `access_token`, and yields
  `rx.redirect("/login")`. Replace the ad-hoc blocks.
- **Acceptance:** Grep shows a single auth-error code path; expiry on *any*
  action lands on login.

### 2.3 No more silent `except: pass`
- **Where:** `state.py:1222` (poll), `state.py:3011` (`load_payees`),
  `state.py:804` (`apply_fc_scenario`), `_run_whatif`, `_load_wi_scenarios`
- **Fix:** Keep them non-fatal, but log server-side and — where user-facing —
  surface a subtle toast. Auth errors must route through 2.2, not be
  swallowed.
- **Acceptance:** A failing payee fetch logs a warning; an auth failure
  inside it still redirects.

### 2.4 Token refresh
- **Where:** `db.py` + `state.py` login/session
- **Problem:** No refresh-token mechanism. Sessions die after the Supabase
  access-token TTL (~1h) with no graceful renewal.
- **Fix:** Capture the refresh token at login, store it server-side
  (`_refresh_token`), and call Supabase's refresh endpoint when a 401 is
  detected — retry the original call once before redirecting.
- **Acceptance:** Idle 70 minutes, then act — the session renews silently
  instead of forcing re-login.

---

## PHASE 3 — Financial Correctness Hardening  *(Impact: MED-HIGH · Effort: M)*

**Goal:** The math is already sound; close the edge cases so bad data can't
crash or mislead.

### 3.1 Guard all date parsing
- **Where:** `formulas.py:67` (`is_scheduled`), `forecast_calc.py` date
  parsing, `state.py` month parsing (`_months_left` ~`state.py:95`)
- **Problem:** `date.fromisoformat()` throws on any non-ISO string; one bad
  date crashes the whole forecast with no recovery.
- **Fix:** A single `_safe_date(s) -> date | None` helper; callers treat
  `None` as "not scheduled / skip." Validate `1 <= month <= 12` in
  `_months_left`.
- **Acceptance:** Inject a malformed date in a tx → forecast still renders,
  that row is simply skipped.

### 3.2 Make vault spent/available semantically correct
- **Where:** `state.py:2261-2264`
- **Problem:** For vaults, `spent = avail = vault_total`. The displayed
  dollar (`vault_fmt`) is correct, but the status pill and any "spent %"
  derived from these is misleading.
- **Fix:**
  ```python
  withdrawn = float((active_month.get("vaultWithdrawals") or {}).get(bid) or 0)
  spent = withdrawn
  avail = vault_total            # accumulated balance still available
  ```
  Revisit `_bucket_status` for the vault case so a still-funding vault doesn't
  read "PAID."
- **Acceptance:** A vault with $600 saved, $0 withdrawn shows 0 spent and
  $600 available, not "PAID / 600 spent."

### 3.3 Validate debt-payment exclusivity
- **Where:** `formulas.py:108`; ideally at write time in `db.py`
- **Problem:** A row with `accountId == debtPaymentAccountId` would
  double-reduce the debt balance. The normal flow never produces this, so
  this is a guard, not a live bug.
- **Fix:** In `acct_balance`, make the debt-payment branch an `elif` of the
  `accountId` branch, or assert the two IDs differ at insert time.
- **Acceptance:** Constructed malformed row no longer double-counts.

### 3.4 Clarify Ready-to-Spend across months
- **Where:** `state.py:2188`
- **Problem:** RTS is always computed for `current_month_id()` even when the
  user is viewing a past/closed month — confusing next to historical data.
- **Fix (decide intent):** Either (a) label it "Ready to Spend (this month)"
  and visually de-emphasize it when not viewing the current month, or
  (b) compute RTS for the displayed month. Recommend (a) — RTS is a
  "right now" number.
- **Acceptance:** Viewing March while it's April makes clear the RTS figure
  is the live current-month value.

### 3.5 Money-type hygiene pass
- **Where:** `formulas.py` `float(... or 0)` sites
- **Problem:** `float("")` and `float("$100")` raise; only some call sites
  are wrapped.
- **Fix:** A `_money(v) -> float` coercer that strips `$`/`,` and treats
  blank/garbage as 0. Use it everywhere amounts are read.
- **Acceptance:** Bad amount strings degrade to 0 instead of crashing.

---

## PHASE 4 — Optimistic-Update Discipline  *(Impact: MED · Effort: M-L)*

**Goal:** UI and DB never diverge, even on partial failure.

### 4.1 Stop mutating `_raw` in place
- **Where:** `vault_transfer` (`state.py:1683`), `distribute_rts`
  (`state.py:1840`), `vault_release_pool` (`state.py:1722`),
  `_set_raw_alloc` (`state.py:1462`)
- **Problem:** They mutate nested dicts via `setdefault(...)` references, then
  `_process` *before* the DB write. A partial write (first upsert ok, second
  fails) leaves UI ahead of DB.
- **Fix:** Adopt one consistent optimistic pattern:
  1. Compute new values, reassign (don't mutate) the relevant slice of
     `_raw`, `_process`, render.
  2. Write to DB.
  3. On **any** failure: reload from DB, `_process`, toast, **and clear the
     edit/modal fields** so the user sees true state.
  Consider a tiny `_optimistic(apply_fn, persist_fn, mid)` wrapper so all
  handlers share the rollback path.
- **Acceptance:** Force the second DB call to fail mid-transfer → UI snaps
  back to real balances, modal closes, error toast shown.

### 4.2 Clear stale modal/edit state on error
- **Where:** every error branch that reloads (e.g. `state.py:1697`)
- **Fix:** After an error reload, reset `bsf_transfer_amt`, `edit_alloc_val`,
  `editing_bid`, etc. Folded into the 4.1 wrapper.
- **Acceptance:** No "ghost" input left in a form after a failed save.

---

## PHASE 5 — Performance & Scale  *(Impact: MED · Effort: M)*

**Goal:** Stay snappy at thousands of transactions and years of history.

### 5.1 Index transactions once per `_process`
- **Where:** `state.py:_process` (~`state.py:2145`), `forecast_calc.py`
- **Problem:** `_process` is O(transactions × buckets); some inner sums are
  O(n) inside O(n) loops (e.g. forecast `paid_bids`). Two full `_process`
  runs per action (optimistic + reload).
- **Fix:** Build lookup maps once: `tx_by_bucket_month`, `tx_by_account`,
  `spent_by_bucket_month`. Pass them to the formula calls or precompute the
  aggregates. Eliminates the nested scans.
- **Acceptance:** With 5k synthetic transactions, a fund action stays under a
  noticeable lag threshold; profile shows the nested scans gone.

### 5.2 Skip the redundant double-process
- **Where:** handlers that `_process` optimistically then reload + `_process`
- **Fix:** Where the optimistic compute already matches what the reload will
  produce, skip the first `_process` (or skip the reload and trust the
  optimistic state for non-derived writes). Be surgical — correctness first.
- **Acceptance:** One `_process` per simple action in the common path.

### 5.3 Paginate / window the ledger
- **Where:** ledger rendering + `DB.load_all` (`db.py:37`)
- **Problem:** `load_all` pulls every transaction every time; the ledger
  renders them all.
- **Fix:** Virtualize or page the ledger view; optionally lazy-load older
  months on demand.
- **Acceptance:** A 3-year ledger scrolls smoothly; initial load is bounded.

---

## PHASE 6 — Security & Privacy Hygiene  *(Impact: MED · Effort: S)*

**Goal:** Least-exposure defaults. (RLS is already correctly enforced —
`schema.sql` `user_id = auth.uid()` on every table — so this is hardening,
not a hole.)

### 6.1 Keep secrets server-side
- **Where:** `state.py:263` `access_token`, `state.py:264` `user_id`
- **Problem:** Public state vars are serialized to the browser over the
  WebSocket. The token is the user's own and RLS limits blast radius, but
  there's no reason to ship it client-side.
- **Fix:** Rename to `_access_token` / `_user_id` (backend-only). Update all
  references.
- **Acceptance:** Token no longer appears in client state deltas.

### 6.2 Input validation at the boundary
- **Where:** `db.py` insert/update helpers
- **Fix:** Reject non-positive amounts where nonsensical, clamp string
  lengths, validate enum-ish fields (account type, bucket type, freq) before
  they hit the DB.
- **Acceptance:** Garbage payloads are rejected with a clear message.

### 6.3 Rate-limit auth endpoints
- **Where:** `sign_up` / login in `db.py`
- **Fix:** Lean on Supabase auth settings (lockout, captcha) and surface
  friendly errors.
- **Acceptance:** Repeated bad logins are throttled.

---

## PHASE 7 — Test & Verification Harness  *(Impact: HIGH for longevity · Effort: L)*

**Goal:** Lock in the formulas so future changes can't silently break money.

### 7.1 Golden-master formula tests
- **Where:** new `reflex_app/tests/test_formulas.py`
- **Fix:** Pure-Python unit tests for `formulas.py` and `forecast_calc.py`
  using fixed fixtures: account balance (incl. debt, opening, xfr,
  adjustment, scheduled), rollover, vault accumulation, RTS, BvA, forecast
  periods, timeline occurrence logic (the bug we just fixed — pin it).
- **Acceptance:** `pytest` green; each known formula has a regression test.

### 7.2 Component smoke compile in CI
- **Where:** GitHub Actions
- **Fix:** Run `reflex export --frontend-only --no-zip` in CI so a
  Reflex-incompatible expression (the `Var + str` / `.contains` class of bug
  we hit) fails the build *before* Railway.
- **Acceptance:** A bad component change red-Xes the PR, not the deploy.

### 7.3 Seed + scenario fixtures
- **Where:** `reflex_app/tests/fixtures/`
- **Fix:** A realistic multi-month seed dataset for manual and automated
  verification.
- **Acceptance:** One command spins up a believable demo account.

---

## PHASE 8 — UX Polish & "Then Some"  *(Impact: MED · Effort: L, incremental)*

**Goal:** The difference between "works" and "delightful."

### 8.1 Undo / safety net
- Soft-delete with an "Undo" toast for destructive actions (delete tx,
  archive bucket, close month). Recoverable for ~10s.

### 8.2 Empty & first-run states
- Every panel needs a real empty state: what it's for, the one action to
  take next. A guided first-run (create account → bucket → paycheck → first
  transaction).

### 8.3 Keyboard & accessibility
- Audit focus order, `aria-*`, and contrast (the mono-on-dark palette is
  tight). Keyboard shortcuts for add-transaction, month nav, panel switch.

### 8.4 Recurring transactions / automation
- Promote "scheduled" txs into true recurrence rules that auto-materialize on
  their date (closing the loop with the forecast/timeline we just hardened).

### 8.5 Data export / import
- CSV/JSON export of transactions and a yearly summary; import with mapping.
  Critical for trust ("my data isn't trapped").

### 8.6 Notifications & nudges
- Optional: upcoming-bill and low-RTS nudges (email or in-app), driven by the
  same forecast engine.

### 8.7 Reports depth
- Year-over-year, category drilldown from the BvA cells, exportable report
  views, and a savings-rate trend line.

### 8.8 Mobile pass
- Re-screenshot every panel at 390px after these changes; tighten the
  bottom-nav reachability and sheet ergonomics.

### 8.9 Onboarding & docs
- In-app glossary for the domain terms (RTS, vault, sinking, rollover,
  ZBB funding) — power features are only powerful if understood.

---

## Suggested execution order

1. **Phase 1 + 2** together — they share the `_dirty` flag and the central
   auth guard, and they buy the most reliability. *This is the 78 → ~88 jump.*
2. **Phase 3** — correctness guards; cheap insurance.
3. **Phase 7.1 + 7.2** — pin the formulas and add the CI compile gate before
   refactoring further.
4. **Phase 4** — optimistic-update discipline, now safely test-backed.
5. **Phase 5, 6** — scale and hygiene.
6. **Phase 8** — ongoing polish toward 100.

**Score trajectory (estimate):**
`78 → 88 (P1–2) → 91 (P3) → 93 (P7) → 96 (P4–5) → 98 (P6) → 100 (P8)`
