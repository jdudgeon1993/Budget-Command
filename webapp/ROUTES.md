# Route Map (Phase 1 reference)

Snapshot of every Flask route before the action-registry refactor. Use this
as the fallback/spec when migrating routes to the new dispatcher — each
mutation route here should map to one registered action with the same DB
call(s), same `back_panel`, and same DEV_SEED behavior.

Legend:
- **Type**: `read` (renders a panel/fragment, no DB write) or `mutation`
  (calls into `db.py`, needs `_dev_or_panel`/cache invalidation)
- **DB calls**: functions from `webapp/db.py` invoked
- **Back panel**: panel re-rendered after the action (via `_PANEL_MAP` /
  `_panel_close_modal` / `_buckets_response` / `_dev_or`)
- **Modal?**: whether the route also serves a modal fragment on GET

---

## Buckets

| Route | Methods | Function | Type | DB calls | Back panel | Modal? |
|---|---|---|---|---|---|---|
| `/buckets` | GET | `buckets` | read | — | buckets | — |
| `/actions/bucket_add` | POST | `_bucket_add` | **migrated** | `insert_bucket` | buckets | — |
| `/actions/bucket_alloc_set` | POST | `_bucket_alloc_set` | **migrated** | `upsert_alloc` | buckets | — |
| `/actions/bucket_fill` | POST | `_bucket_fill` | **migrated** | `upsert_alloc` | buckets | — |
| `/actions/bucket_budget_set` | POST | `_bucket_budget_set` | **migrated** | `upsert_budget` (+ future months if current month) | buckets | — |
| `/buckets/<bid>/settings` | GET, POST | `bucket_settings` | mutation | `upsert_bucket` | buckets | yes (`_frag_bucket`) |
| `/actions/bucket_archive` | POST | `_bucket_archive` | **migrated** | `upsert_bucket({archived:true})` | buckets | — |
| `/actions/bucket_move` | POST | `_bucket_move` | **migrated** | `update_bucket_order` ×2 | buckets | — |
| `/actions/bucket_handled_toggle` | POST | `_bucket_handled_toggle` | **migrated** | `ensure_month`, `toggle_handled` | buckets | — |
| `/buckets/<bid>/vault-transfer` | GET, POST | `vault_transfer` | mutation | `vault_transfer` | buckets | yes (`_frag_vault_transfer`) |
| `/buckets/<bid>/vault-release` | GET, POST | `vault_release_to_pool` | mutation | `vault_release_to_pool`, `log_vault_release` | buckets | yes (`_frag_vault_release`) |
| `/buckets/distribute` | GET | `distribute_modal` | read | — | — | yes (`_frag_distribute`) |
| `/buckets/distribute/preview` | POST | `distribute_preview` | read | — | — | yes (`_frag_distribute`) |
| `/buckets/distribute` | POST | `distribute_rts` | mutation | `upsert_alloc` (N×) | buckets | closes modal |

## Month workflow

| Route | Methods | Function | Type | DB calls | Back panel |
|---|---|---|---|---|---|
| `/month/close` | POST | `month_close` | mutation | `close_month` | buckets |
| `/month/reopen` | POST | `month_reopen` | mutation | `reopen_month` | buckets |
| `/month/<direction>` | GET | `month_nav` | read (session only) | — | active panel |
| `/month/today` | GET | `month_today` | read (session only) | — | active panel |

## Accounts

| Route | Methods | Function | Type | DB calls | Back panel | Modal? |
|---|---|---|---|---|---|---|
| `/accounts` | GET | `accounts` | read | — | accounts | — |
| `/accounts/new` | GET, POST | `account_new` | mutation | `insert_account` | accounts | yes (`_frag_account`) |
| `/accounts/<aid>/edit` | GET, POST | `account_edit` | mutation | `update_account` | accounts | yes (`_frag_account`) |
| `/accounts/<aid>/archive` | POST | `account_archive` | mutation | `update_account({archived:true})` | accounts | — |
| `/accounts/<aid>/pay` | GET, POST | `debt_payment` | mutation | `ensure_month`, `insert_debt_payment` | accounts | yes (`_frag_debt_payment`) |
| `/accounts/<aid>/payoff` | GET | `debt_payoff` | read | — | — | yes (`_frag_debt_tracker`, amortization calc) |
| `/accounts/<aid>/interest` | GET, POST | `post_interest` | mutation | `insert_tx` | accounts | yes (`_frag_post_interest`) |

## Transactions

| Route | Methods | Function | Type | DB calls | Back panel | Modal? |
|---|---|---|---|---|---|---|
| `/transaction/new` | GET | `transaction_new` | read | — | — | yes (`_frag_add_tx`) |
| `/transaction` | POST | `transaction_create` | mutation | `insert_transaction` | `back` form field (default buckets) | may open paycheck-distribute modal |
| `/transaction/<tid>/edit` | GET, POST | `transaction_edit` | mutation | `update_transaction` | `back` form field (default accounts) | yes (`_frag_edit_tx`) |
| `/transaction/<tid>/delete` | POST | `transaction_delete` | mutation | `delete_transaction` | `back` form field (default accounts) | — |
| `/transaction/<tid>/apply-rules` | POST | `apply_rules` | mutation | `upsert_alloc` (N×) | buckets | — |
| `/transaction/<tid>/paycheck-distribute/preview` | POST | `paycheck_distribute_preview` | read | — | — | yes (`_frag_paycheck_distribute`) |
| `/transaction/<tid>/paycheck-distribute` | POST | `apply_paycheck_distribute` | mutation | `upsert_alloc` (N×, across current + next month) | buckets | closes modal |

## Reports / Insights / Forecast

| Route | Methods | Function | Type | DB calls | Back panel | Modal? |
|---|---|---|---|---|---|---|
| `/reports` | GET | `reports` | read | — | reports | — |
| `/insights` | GET | `insights` | read | — | insights | — |
| `/forecast/whatif` | POST | `forecast_whatif` | read (pure compute) | — | — | yes (`_frag_forecast_whatif`) |
| `/scenarios/editor` | GET | `scenario_editor_new` | read | — | — | yes (`_frag_scenario_editor`) |
| `/scenarios/<sid>/editor` | GET | `scenario_editor_edit` | read | — | — | yes (`_frag_scenario_editor`) |
| `/scenarios` | POST | `scenario_create` | mutation | `save_scenario` | — (OOB forecast frag) | closes modal |
| `/scenarios/<sid>/update` | POST | `scenario_update` | mutation | `update_scenario` | — (OOB forecast frag) | closes modal |
| `/scenarios/<sid>/delete` | POST | `scenario_delete` | mutation | `delete_scenario` | — (OOB forecast frag) | closes modal |

## Setup

| Route | Methods | Function | Type | DB calls | Back panel |
|---|---|---|---|---|---|
| `/setup` | GET | `setup` | read | — | setup |
| `/actions/paycheck_add` | POST | `_paycheck_add` | **migrated** | `insert_paycheck` | setup |
| `/actions/paycheck_edit` | POST | `_paycheck_edit` | **migrated** | `update_paycheck` | setup |
| `/actions/paycheck_delete` | POST | `_paycheck_delete` | **migrated** | `delete_paycheck` | setup |
| `/actions/category_add` | POST | `_category_add` | **migrated** | `insert_category` | setup |
| `/actions/category_edit` | POST | `_category_edit` | **migrated** | `update_category` | setup |
| `/actions/category_delete` | POST | `_category_delete` | **migrated** | `update_category({archived:true})` | setup |
| `/actions/category_move` | POST | `_category_move` | **migrated** | `update_category_order` ×2 | setup |
| `/actions/rule_add` | POST | `_rule_add` | **migrated** | `insert_alloc_rule` | setup |
| `/actions/rule_edit` | POST | `_rule_edit` | **migrated** | `update_alloc_rule` | setup |
| `/actions/rule_delete` | POST | `_rule_delete` | **migrated** | `delete_alloc_rule` | setup |
| `/actions/rule_toggle` | POST | `_rule_toggle` | **migrated** | `toggle_alloc_rule` | setup |

> All Setup actions now live in `actions.py` and run through `/actions/<name>`.
> Forms pass row id (and `direction` for reordering) as hidden fields.

## Top-level / misc

| Route | Methods | Function | Type |
|---|---|---|---|
| `/` | GET | `index` | redirect → buckets |
| `/dashboard` | GET | `dashboard` | redirect → buckets |

---

## Notes for Phase 2 (action registry design)

- **Simple single-call mutations** (clear majority — `add_*`, `edit_*`,
  `del_*`, `archive_*`, toggles, reorders) are the easiest first migration
  targets: one DB call, fixed back-panel, DEV_SEED-gated, optional flash.
  These already follow `_dev_or` / `_dev_or_panel` shape almost exactly.

- **Multi-call / loop mutations** (`distribute_rts`, `apply_rules`,
  `apply_paycheck_distribute`, `set_budget`'s future-month propagation,
  `vault_release_to_pool`'s optional log entry) need an action signature
  that accepts a list of `(db_fn, args)` tuples or a small imperative body
  — don't force these into "one DB call per action".

- **Routes with `back` form field** (`transaction_create`,
  `transaction_edit`, `transaction_delete`) need the dispatcher to support
  a *dynamic* back-panel resolved from form data, not just a static map
  entry.

- **Read-only modal routes** (settings forms, vault transfer/release GET,
  debt payment/interest/payoff GET, scenario editor, add-tx, distribute
  preview) are out of scope for the action registry — they stay as
  dedicated GET routes returning fragments.

- **OOB-response routes** (`scenario_*`, `transaction_create`'s
  paycheck-distribute branch) don't fit `_panel_close_modal`'s
  render-whole-panel model — the dispatcher needs an "OOB fragment" response
  mode alongside "full panel" and "close modal + panel".
