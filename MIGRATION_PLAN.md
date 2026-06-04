# Cura — Migration Plan: Reflex → Flask + Jinja2 + HTMX

## North star

- **The proto is the template (the look).** `proto.html` and `forecast-proto.html` are the
  visual source of truth. Lift their HTML/CSS into Jinja templates.
- **Reflex is the heart (the behavior).** `state.py` event handlers + the agnostic Python
  (`formulas.py`, `forecast_calc.py`, `db.py`) define *what each action does*. Re-express the
  handlers as Flask routes; carry the agnostic Python over unchanged.
- **One section at a time.** Every phase is a shippable vertical slice: template + routes +
  data wiring + HTMX + verification. Nothing half-wired left between phases.

## Stack

| Layer | Choice | Notes |
|---|---|---|
| Web framework | **Flask** | App factory + blueprints. Least ceremony. |
| Templates | **Jinja2** | Base shell + injected panel partials. |
| Interactivity | **HTMX** | Fragment swaps, inline edits, OOB updates. No websockets. |
| Local UI state | **Alpine.js** | Dropdowns, popovers, toggles. |
| Data | **Supabase** (unchanged) | via existing `db.py`. |
| Auth | **Supabase JWT** in Flask signed-cookie session. |
| Serve | **gunicorn** on Railway. |

## Reuse inventory (ports unchanged)

- `forecast_calc.py` (890) — forecast engine. **Keep.**
- `formulas.py` (293) — budget math. **Keep.**
- `db.py` (501) — Supabase access. **Keep** (swap only how results are stored: session, not state).
- `FORMULAS.md`, `schema.sql` — spec + schema. **Reference.**

## Cross-cutting conventions

- **Template tiers:** `base.html` (full shell) · `_partial.html` (`{% block panel %}` only) ·
  one template per panel that does `{% extends "_partial.html" if request.htmx else "base.html" %}`.
- **HTMX nav:** `hx-get="/<panel>" hx-target="#panel" hx-push-url="true"`.
- **Three interactivity tiers:** (1) whole-panel swap, (2) in-panel row fragments,
  (3) `hx-swap-oob` for global bits (Ready-to-Assign, month totals).
- **Behavior parity rule:** before writing a route, read the matching `state.py` handler and
  mirror its validation, db calls, and recompute order.
- **Per-phase verification:** `flask run`, open the page (desktop 1280 / mobile 390), screenshot,
  diff against the proto and against the live Reflex app for numbers. No socket/state dance.
- **Forecast exception:** the forecast builder is a JS island, not server fragments
  (see Phase 9). Server still owns authoritative numbers via `forecast_calc.py`.

---

## Phase 0 — Foundation & scaffold
**Goal:** an empty Flask app that boots, renders the shell, and deploys.
- New branch `migrate/flask`. New top-level package (e.g. `webapp/`) — leave `reflex_app/` intact until cutover.
- Flask app factory, config from `.env` (`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SECRET_KEY`).
- Copy `db.py`, `formulas.py`, `forecast_calc.py` in verbatim; confirm zero `reflex` imports.
- Deps: `flask`, `flask-htmx`, `supabase`, `python-dotenv`, `gunicorn`.
- `base.html` + `_partial.html`; `before_request` sets `request.htmx`.
- Extract CSS from `proto.html` → `static/css/app.css`; fonts; favicon.
- Railway: `Procfile`/`railway.toml` → `gunicorn`. Health route `/healthz`.
- **Done when:** app boots locally + on Railway, base shell renders empty panel slot.

## Phase 1 — Auth & session
**Goal:** real login/logout against Supabase.
- Templates: `login.html`, `signup.html` (styling from proto).
- Routes: `POST /login` → `db.sign_in` → store `access_token`/`user_id`/`email` in session → redirect `/dashboard`; `POST /signup`; `GET /logout`.
- `@login_required` decorator; redirect to `/login` on missing/expired token (mirror `state.py` auth-error handling).
- **Behavior source:** `state.py` `login`, `_on_db_error` (auth-error → logout); `db.sign_in`.
- **Done when:** log in with a real account, session persists across requests, protected routes guard correctly.

## Phase 2 — Dashboard shell
**Goal:** the persistent shell with working panel injection + month nav.
- `base.html`: desktop sidebar, mobile header + bottom nav, month switcher, Ready-to-Assign block, user footer, Add-Transaction CTA. Lift markup from `proto.html`.
- Panel slot `#panel` + HTMX nav links; `hx-push-url` for clean URLs + back/forward.
- Per-request data: `db.load_all(uid, token)` → request-scoped cache; active-month helper.
- Month prev/next (store active month id in session or URL) → recompute + re-render shell bits.
- One placeholder panel so nav is exercised.
- **Behavior source:** `pages/dashboard.py`, `components/sidebar.py`, `state.py` month-switch handlers + `formulas.ready_to_spend`.
- **Done when:** shell renders desktop + mobile, nav swaps panels via HTMX, month switch updates RTS.

## Phase 3 — Buckets panel  *(pattern-proving slice)*
**Goal:** first full vertical slice; locks in the HTMX recipe.
- `buckets.html` partial from proto (category groups, bucket rows, inline alloc/budget fields).
- Routes: `GET /buckets` (full+partial); inline edit alloc/budget (`hx-post` → row partial); add bucket; bucket settings; archive; reorder.
- **OOB:** allocation change returns row partial + `hx-swap-oob` RTS update.
- **Behavior source:** `components/buckets.py`, `state.py` bucket/alloc handlers; `formulas.bucket_available`, `b_alloc`, `ready_to_spend`; `db.upsert_alloc`, `update_bucket`, `insert_bucket`.
- **Done when:** edit an allocation → row + RTS update with no reload; numbers match Reflex & `FORMULAS.md`.

## Phase 4 — Transactions
**Goal:** the global Add-Transaction flow + edit/delete.
- Add-transaction sheet (HTMX load + POST); edit/delete.
- Recompute affected bucket + account balances + RTS via OOB swaps.
- **Behavior source:** `state.py` transaction handlers; `db.insert_transaction`; `formulas.acct_balance`.
- **Done when:** add a tx → bucket, account, and RTS all reflect it immediately.

## Phase 5 — Accounts, ledger & reconciliation
**Goal:** accounts panel with balances, per-account ledger, reconcile flow.
- `accounts.html`; account cards (`formulas.acct_balance`); ledger list; add/edit account; debt payoff.
- Reconciliation: checkbox UI with Alpine running-balance, POST to commit.
- **Behavior source:** `components/accounts.py` + matching `state.py` handlers; `db` account/tx functions.
- **Done when:** balances match Reflex; reconcile commits correctly.

## Phase 6 — Setup wizard
**Goal:** paychecks, categories, allocation rules CRUD.
- `setup.html`; forms + HTMX add/edit/delete for each.
- **Behavior source:** `components/setup.py` + `state.py`; relevant `db` functions.
- **Done when:** all setup entities CRUD correctly and feed the rest of the app.

## Phase 7 — Reports
**Goal:** read-only analytics panels.
- `reports.html`: snapshots, budget-vs-actual, trends, payee analysis.
- Mostly server-rendered computed data; minimal interactivity.
- **Behavior source:** `components/reports.py` + `state.py` report builders; `formulas`.
- **Done when:** report figures match Reflex.

## Phase 8 — Payday modal
**Goal:** one-click paycheck distribution via allocation rules.
- Payday sheet (HTMX); apply rules → allocations; OOB updates.
- **Behavior source:** `components/payday.py` + `state.py` payday handlers.
- **Done when:** running payday allocates exactly as Reflex did.

## Phase 9 — Forecast builder  *(JS island)*
**Goal:** mount `forecast-proto.html` as the Forecast panel, wired to real data, with the server owning authoritative numbers.
- Panel embeds the proto markup + its JS engine.
- `GET /api/forecast/data` → real buckets/income/accounts (from `db.load_all`).
- Timeline/What-If edits POST to `POST /api/forecast/compute` → **`forecast_calc.compute_forecast`** returns authoritative periods/balance; client renders them (the "heart" stays in Python).
- Scenarios: `GET/POST /api/forecast/scenarios` → `db.list_scenarios` / `db.save_scenario`.
- **Behavior source:** `forecast_calc.py` (authoritative); `forecast-proto.html` (interaction); `state.py` `_run_whatif`, scenario save/load.
- **Done when:** the proto runs against real data, the grid edits recompute via Python, scenarios round-trip to Supabase.

## Phase 10 — Parity, polish & cutover
**Goal:** confirm full parity and switch Railway over.
- Behavior diff every panel vs. the Reflex app; mobile (390) + desktop (1280) QA.
- Flash messages, `htmx-indicator` loading states, error pages, empty states.
- Per-request `load_all` caching; basic perf check.
- Deploy Flask alongside Reflex; verify with a real account.
- Flip Railway to the Flask service; archive `reflex_app/` (kept in git history).
- **Done when:** Flask app is the deployed app at full parity; Reflex retired.

---

## Notes / risks

- **Build order rationale:** auth + shell are the foundation; Buckets proves the pattern;
  Transactions/Accounts/Setup feed everything; Forecast is last (it's an island and depends on
  real data from earlier phases).
- **Keep Reflex running** until Phase 10 — every phase is verifiable against the live app.
- **Single source of truth for math:** never reimplement a formula in JS. The forecast island
  posts to Python for authoritative numbers.
- **Local verification is now trivial:** Flask pages open directly in a browser — no serve +
  socket + token dance like Reflex required.
