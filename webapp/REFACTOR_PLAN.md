# Action-Registry Refactor — Phase Plan

Goal: replace the ~30 near-identical mutation routes in `panels.py` with a
small action registry + generic dispatcher, without changing the live,
everything-reads-everything behavior. See `ROUTES.md` for the full
route-by-route inventory this plan is based on (keep it updated as routes
migrate — it's the fallback reference if something regresses).

## Phase 1 — Inventory (done)
- `ROUTES.md`: every route, its DB calls, back-panel, modal behavior.
- Classify routes into: simple single-call mutations, multi-call/loop
  mutations, dynamic-back-panel routes, OOB-response routes, read-only
  modal routes (out of scope).

## Phase 2 — Build the registry primitives (no route changes yet)
- Define the `Action` shape: `name`, `fn(uid, token, form, data) -> None`,
  `back_panel` (static or resolver function), `response_mode`
  (`"panel"` | `"close_modal"` | `"oob"`), optional `flash` builder.
- Generic dispatcher `POST /actions/<name>`: validates login, runs the
  action's `fn` (skipped under DEV_SEED), calls `D.invalidate_cache()`,
  renders the response per `response_mode`.
- Add this alongside existing routes — nothing removed yet. Write a couple
  of throwaway test actions to prove the dispatcher works end-to-end.

## Phase 3 — Migrate simple single-call mutations (done)
- Targets: `add_bucket`, `set_alloc`, `fill_bucket`, `set_budget`,
  `archive_bucket`, `move_bucket`, `toggle_handled`, `account_archive`,
  `add_paycheck`/`edit_paycheck`/`del_paycheck`, `add_category`/
  `edit_category`/`del_category`/`move_category`, `add_rule`/`edit_rule`/
  `del_rule`/`toggle_rule`.
- Old route stays as a thin redirect to the new action endpoint (or is
  deleted directly if templates are updated in the same pass — prefer
  updating templates' `hx-post`/`action` URLs in the same commit per group
  to avoid a long dual-route period).
- Update `ROUTES.md` row-by-row as each migrates (mark "migrated").

## Phase 4 — Migrate multi-call / loop mutations (done)
- Targets: `distribute_rts`, `apply_rules`, `apply_paycheck_distribute`,
  `vault_release_to_pool`, `vault_transfer`, `set_budget`'s future-month
  propagation.
- Action `fn` bodies stay imperative (loops over obligations/rules) — the
  win here is just shedding the `_dev_or_panel` boilerplate at the edges,
  not forcing these into single DB calls.

## Phase 5 — Dynamic back-panel + OOB response modes (done)
- Targets: `transaction_create`, `transaction_edit`, `transaction_delete`
  (back-panel from `request.form["back"]`), and `scenario_*` (OOB forecast
  fragment response mode).
- Extend dispatcher's `response_mode` handling to cover these two cases
  generically so no route-specific glue remains.
- Added `always_run` (fn runs even under DEV_SEED, self-checks before DB
  writes) and tuple-return flash overrides to `Action`/`dispatch()` to
  support dynamic flash messages and validation-only paths.
- Added `"oob"` response_mode: `fn` returns the full `Response` directly
  (used by `tx_create`'s paycheck-distribute branch and `scenario_*`'s
  forecast-fragment swap).

## Phase 6 — Cleanup (done)
- Removed now-unused `_dev_or`, `_dev_or_panel`, and panels.py's local
  `_PANEL_MAP` (superseded by `actions._PANEL_MAP`).
- Kept `_panel_close_modal`, `_buckets_response`, `_is_modal`, and
  `render_panel` — still used by the remaining read-only modal routes
  (bucket/account settings, debt payment/interest, vault transfer/release
  GET, scenario editor, add/edit-tx GET).
- `ROUTES.md` updated row-by-row; every mutation route is either migrated
  to `/actions/<name>` or intentionally standalone (read-only modal GETs).

## Status: all phases complete.

## Testing strategy throughout
- Each phase: `python -m compileall webapp`, template-render check (already
  in CI), then manual smoke test of the migrated panel's primary flows
  (dev-seed mode, `DEV_SEED=1`).
- Migrate one panel's routes at a time (e.g. all of Setup in one PR/commit)
  so a regression is easy to bisect and `ROUTES.md` stays a trustworthy
  fallback map.
