"""Action registry — Phase 2 of the route-consolidation refactor.

An Action bundles what today is hand-copied at the tail of every mutation
route: run a DB call (skipped under DEV_SEED), invalidate the cache, flash a
message, and render a response in one of three shapes:

  - "panel"       — re-render the back panel in place (HTMX swap or redirect)
  - "close_modal" — re-render the back panel + HX-Trigger: closeModal
  - "oob"         — render an out-of-band fragment swap (e.g. forecast preview)

See REFACTOR_PLAN.md for the migration phases and ROUTES.md for the full
route inventory this is replacing piece by piece. Nothing is wired into
panels.py yet beyond the /actions/<name> dispatcher itself — existing routes
are untouched until they're migrated one group at a time.
"""

from dataclasses import dataclass
from typing import Callable, Optional

from flask import (request, redirect, url_for, session, current_app,
                   flash, make_response, render_template)

from . import db as DB
from . import data as D


@dataclass
class Action:
    name: str
    # fn(uid, token, form, data) -> None — performs the DB write(s).
    # Not called at all under DEV_SEED.
    fn: Callable
    # Static panel name, or fn(form) -> panel name for dynamic back-panels
    # (e.g. transaction routes that read request.form["back"]).
    back_panel: "str | Callable[[dict], str]" = "buckets"
    response_mode: str = "panel"  # "panel" | "close_modal" | "oob"
    # flash(form) -> (message, category) | None
    flash_msg: Optional[Callable] = None
    dev_seed_msg: Optional[str] = "Dev mode: change not persisted."
    # If True, fn always runs (even under DEV_SEED) and is responsible for
    # checking current_app.config["DEV_SEED"] itself before any DB write.
    # fn may optionally return a (message, category) tuple to override the
    # flash message.
    always_run: bool = False


_REGISTRY: dict[str, Action] = {}


def register(action: Action) -> Action:
    _REGISTRY[action.name] = action
    return action


def get(name: str) -> Optional[Action]:
    return _REGISTRY.get(name)


# ── Shared panel render helpers (mirrors panels._PANEL_MAP) ──────────────────

_PANEL_MAP = {
    "accounts": ("panels/accounts.html", lambda: D.accounts_view()),
    "buckets":  ("panels/buckets.html",  lambda: D.bucket_rows()),
    "reports":  ("panels/reports.html",  lambda: D.reports_view()),
    "setup":    ("panels/setup.html",    lambda: D.setup_view()),
}


def _render_panel(panel: str, htmx: bool):
    from .panels import render_panel  # local import to avoid a circular import
    tmpl, ctx_fn = _PANEL_MAP[panel]
    return render_panel(tmpl, panel, **ctx_fn())


def dispatch(name: str):
    """Generic handler for POST /actions/<name>. See Action docstring."""
    action = get(name)
    if action is None:
        return ("Unknown action", 404)

    form = request.form
    data = D.load_data()

    dev_seed = current_app.config["DEV_SEED"]
    result = None
    if action.always_run or not dev_seed:
        result = action.fn(session["user_id"], session["access_token"], form, data)
        if not dev_seed:
            D.invalidate_cache()

    if action.response_mode == "oob":
        return result

    if isinstance(result, tuple):
        msg = result
    elif not dev_seed:
        msg = action.flash_msg(form) if action.flash_msg else None
    else:
        msg = (action.dev_seed_msg, "ok") if action.dev_seed_msg else None
    if msg:
        flash(*msg)

    panel = action.back_panel(form) if callable(action.back_panel) else action.back_panel
    htmx = request.headers.get("HX-Request") == "true"

    if action.response_mode == "close_modal":
        resp = make_response(_render_panel(panel, htmx))
        resp.headers["HX-Trigger"] = "closeModal"
        return resp
    if action.response_mode == "panel":
        if htmx:
            return _render_panel(panel, htmx)
        return redirect(url_for(f"panels.{panel}"))
    raise ValueError(f"Unsupported response_mode for /actions dispatch: {action.response_mode!r}")


# ── Setup actions (paychecks, categories, allocation rules) ─────────────────
# Migrated from panels.py per REFACTOR_PLAN.md Phase 3. Forms post the row's
# id (and direction, where relevant) as hidden fields rather than URL segments.

def _rule_value_type(raw: "str | None") -> str:
    """Normalize the rule form's value_type into one of: pct, fund, fixed."""
    if raw == "pct":
        return "pct"
    if raw == "fund":
        return "fund"
    return "fixed"


def _paycheck_add(u, t, f, data):
    amt = D.parse_amount(f.get("amount", "0"))
    DB.insert_paycheck(u, t, f.get("label", "Paycheck"), amt, int(f.get("freq") or 14),
                       f.get("anchor") or D.tx_form_ctx()["today"])


register(Action("paycheck_add", _paycheck_add, "setup"))


def _paycheck_edit(u, t, f, data):
    amt = D.parse_amount(f.get("amount", "0"))
    DB.update_paycheck(u, t, f.get("id", ""), f.get("label", "Paycheck"), amt,
                        int(f.get("freq") or 14), f.get("anchor") or D.tx_form_ctx()["today"])


register(Action("paycheck_edit", _paycheck_edit, "setup"))


def _paycheck_delete(u, t, f, data):
    DB.delete_paycheck(u, t, f.get("id", ""))


register(Action("paycheck_delete", _paycheck_delete, "setup"))


def _category_add(u, t, f, data):
    DB.insert_category(u, t, f.get("name", "Category"), f.get("color") or "#818cf8")


register(Action("category_add", _category_add, "setup"))


def _category_edit(u, t, f, data):
    DB.update_category(u, t, f.get("id", ""),
                        {"name": f.get("name", ""), "color": f.get("color", "#818cf8")})


register(Action("category_edit", _category_edit, "setup"))


def _category_delete(u, t, f, data):
    DB.update_category(u, t, f.get("id", ""), {"archived": True})


register(Action("category_delete", _category_delete, "setup"))


def _category_move(u, t, f, data):
    cid, direction = f.get("id", ""), f.get("direction", "")
    cats = sorted(data.get("cats", []), key=lambda c: c.get("order", 0))
    idx = next((i for i, c in enumerate(cats) if c["id"] == cid), -1)
    swap_idx = idx - 1 if direction == "up" else idx + 1
    if 0 <= idx < len(cats) and 0 <= swap_idx < len(cats):
        c1, c2 = cats[idx], cats[swap_idx]
        o1, o2 = c1.get("order", idx), c2.get("order", swap_idx)
        DB.update_category_order(u, t, c1["id"], o2)
        DB.update_category_order(u, t, c2["id"], o1)


register(Action("category_move", _category_move, "setup"))


def _rule_add(u, t, f, data):
    vtype = _rule_value_type(f.get("value_type"))
    val = 0.0 if vtype == "fund" else D.parse_amount(f.get("value", "0").replace("%", ""))
    rtype = "external" if f.get("rule_type") == "external" else "internal"
    DB.insert_alloc_rule(u, t, f.get("name", "Rule"), rtype, vtype, val, f.get("bucketId", ""))


register(Action("rule_add", _rule_add, "setup"))


def _rule_edit(u, t, f, data):
    vtype = _rule_value_type(f.get("value_type"))
    val = 0.0 if vtype == "fund" else D.parse_amount(f.get("value", "0").replace("%", ""))
    rtype = "external" if f.get("rule_type") == "external" else "internal"
    DB.update_alloc_rule(u, t, f.get("id", ""), f.get("name", "Rule"), rtype, vtype, val,
                          f.get("bucketId", ""))


register(Action("rule_edit", _rule_edit, "setup"))


def _rule_delete(u, t, f, data):
    DB.delete_alloc_rule(u, t, f.get("id", ""))


register(Action("rule_delete", _rule_delete, "setup"))


def _rule_toggle(u, t, f, data):
    DB.toggle_alloc_rule(u, t, f.get("id", ""))


register(Action("rule_toggle", _rule_toggle, "setup"))


# ── Temporary: planned/unplanned reconcile toggle ────────────────────────────

def _tx_planned_toggle(u, t, f, data):
    tid = f.get("id", "")
    planned = f.get("planned") == "1"
    if not current_app.config["DEV_SEED"]:
        DB.update_transaction(u, t, tid, {"planned": planned})
        D.invalidate_cache()


register(Action("tx_planned_toggle", _tx_planned_toggle, "setup"))


# ── Bucket actions ────────────────────────────────────────────────────────

def _bucket_add(u, t, f, data):
    name = f.get("name", "").strip()
    cat_id = f.get("catId", "")
    btype = f.get("type", "expense")
    if not (name and cat_id):
        return ("Name and category are required.", "error")
    if not current_app.config["DEV_SEED"]:
        DB.insert_bucket(u, t, name, cat_id, btype)
        return ("Bucket added.", "ok")
    return ("Dev mode: bucket not persisted.", "ok")


register(Action("bucket_add", _bucket_add, "buckets", always_run=True))


def _bucket_alloc_set(u, t, f, data):
    bid = f.get("id", "")
    submitted = D.parse_amount(f.get("alloc", "0"))
    month = D.active_month(data)
    mid = D.active_mid()
    # The alloc field shows committed (alloc + carryover) so the user edits
    # a single total. Strip carryover before storing so it isn't double-counted.
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bid), {})
    btype = bucket.get("type", "expense")
    is_flex = bucket.get("flex", False) and btype == "expense"
    is_regular_expense = btype not in ("vault", "sinking", "goal") and not is_flex
    if is_regular_expense:
        txs = data.get("txs", [])
        months = data.get("months", [])
        loaded_mids = [t.get("monthId") for t in txs if t.get("monthId")]
        min_key = min((D.F.parse_month_id(m) for m in loaded_mids), default=D.F.parse_month_id(mid))
        prior_months = [m for m in D.F.months_before(mid, months)
                        if D.F.parse_month_id(m["id"]) >= min_key]
        carryover = sum(
            max(0.0, D.F.b_alloc(m, bid) - D.F.b_spent(m["id"], bid, txs))
            for m in prior_months
        )
        amount = max(0.0, round(submitted - carryover, 2))
    else:
        amount = submitted
    month.setdefault("allocations", {})[bid] = amount
    if not current_app.config["DEV_SEED"]:
        DB.ensure_month(u, t, mid)
        DB.upsert_alloc(u, t, mid, bid, amount)


register(Action("bucket_alloc_set", _bucket_alloc_set, "buckets", always_run=True, dev_seed_msg=None))


def _bucket_fill(u, t, f, data):
    bid = f.get("id", "")
    mid = D.active_mid()
    month = D.active_month(data)
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bid), {})
    txs = data.get("txs", [])
    months = data.get("months", [])
    budget = D.F.b_budget(month, bid, float(bucket.get("defaultBudget") or 0))
    spent = D.F.b_spent(mid, bid, txs)
    # Compute carryover so Fill doesn't over-allocate: we need committed=budget,
    # and committed = carryover + alloc, so store alloc = max(0, target - carryover).
    btype = bucket.get("type", "expense")
    is_flex = bucket.get("flex", False) and btype == "expense"
    is_regular_expense = btype not in ("vault", "sinking", "goal") and not is_flex
    if is_regular_expense:
        loaded_mids = [t.get("monthId") for t in txs if t.get("monthId")]
        min_key = min((D.F.parse_month_id(m) for m in loaded_mids), default=D.F.parse_month_id(mid))
        prior_months = [m for m in D.F.months_before(mid, months)
                        if D.F.parse_month_id(m["id"]) >= min_key]
        carryover = sum(
            max(0.0, D.F.b_alloc(m, bid) - D.F.b_spent(m["id"], bid, txs))
            for m in prior_months
        )
        target = max(budget, spent)
        new_alloc = max(0.0, round(target - carryover, 2))
    else:
        new_alloc = max(budget, spent)
    month.setdefault("allocations", {})[bid] = new_alloc
    if not current_app.config["DEV_SEED"]:
        DB.ensure_month(u, t, mid)
        DB.upsert_alloc(u, t, mid, bid, new_alloc)
    return ("Covered." if spent > budget else "Filled.", "ok")


register(Action("bucket_fill", _bucket_fill, "buckets", always_run=True))


def _fc_quick_move(u, t, f, data):
    """Add `amount` to a bucket's allocation from forecast sidebar suggestion."""
    bid = f.get("bucket_id", "")
    amount = D.parse_amount(f.get("amount", "0"))
    mid = f.get("mid") or D.active_mid()
    if not bid or amount <= 0:
        return ("Nothing to move.", "warn")
    month = D.active_month(data, mid)
    new_alloc = round(D.F.b_alloc(month, bid) + amount, 2)
    if not current_app.config["DEV_SEED"]:
        DB.upsert_alloc(u, t, mid, bid, new_alloc)
    return ("Moved.", "ok")


register(Action("fc_quick_move", _fc_quick_move, "buckets", always_run=True, dev_seed_msg=None))


def _bucket_budget_set(u, t, f, data):
    bid = f.get("id", "")
    amount = D.parse_amount(f.get("budget", "0"))
    month = D.active_month(data)
    # Write month-specific override so this month reflects the value immediately.
    month.setdefault("budgets", {})[bid] = amount
    # Also update the bucket-level default so all future months without an
    # explicit override naturally inherit this value via b_budget() fallback.
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bid), {})
    if bucket:
        bucket["defaultBudget"] = amount
    if not current_app.config["DEV_SEED"]:
        DB.ensure_month(u, t, D.active_mid())
        DB.upsert_budget(u, t, D.active_mid(), bid, amount)
        DB.upsert_bucket(u, t, bid, {"default_budget": amount})


register(Action("bucket_budget_set", _bucket_budget_set, "buckets", always_run=True, dev_seed_msg=None))


def _bucket_archive(u, t, f, data):
    DB.upsert_bucket(u, t, f.get("id", ""), {"archived": True})


register(Action("bucket_archive", _bucket_archive, "buckets",
                 flash_msg=lambda f: ("Bucket archived.", "ok")))


def _bucket_handled_toggle(u, t, f, data):
    """Mark/unmark a bucket as handled for the active month.

    Marking handled releases any unspent allocation back to Ready to
    Spend (alloc -> spent) and collapses the bucket's effective target to
    that allocation (see formulas.b_budget), so it reads as fully funded
    everywhere — no lingering "short" gap to chase. Unmarking just clears
    the flag; it does not restore the released allocation.
    """
    bid = f.get("id", "")
    mid = D.active_mid()
    month = D.active_month(data)
    currently = bool((month.get("handledBuckets") or {}).get(bid))
    DB.ensure_month(u, t, mid)
    if not currently:
        b = next((b for b in data.get("buckets", []) if b["id"] == bid), None)
        if b:
            alloc = D.F.b_alloc(month, bid)
            spent = D.F.b_spent(mid, bid, data.get("txs", []))
            if spent < alloc - 0.005:
                DB.upsert_alloc(u, t, mid, bid, round(spent, 2))
    DB.toggle_handled(u, t, mid, bid, currently)


register(Action("bucket_handled_toggle", _bucket_handled_toggle, "buckets", dev_seed_msg=None))


# ── Account actions ──────────────────────────────────────────────────────

def _account_archive(u, t, f, data):
    DB.update_account(u, t, f.get("id", ""), {"archived": True})


register(Action("account_archive", _account_archive, "accounts",
                 flash_msg=lambda f: ("Account archived.", "ok")))


# ── Multi-call / loop mutations (Phase 4) ───────────────────────────────────

def _distribute_apply(u, t, f, data):
    """Apply the selected obligations and rule suggestions from the Distribute modal.

    Re-derives suggested amounts server-side (never trusts client-submitted
    dollar figures) and only funds the items the user left checked.
    """
    if "submitted" not in f:
        checked_ob, checked_rule = None, None
    else:
        checked_ob, checked_rule = set(f.getlist("ob")), set(f.getlist("rule"))
    ctx = D.distribute_ctx(checked_ob=checked_ob, checked_rule=checked_rule)
    month = D.active_month(data)

    def _bump(bid, add):
        if add <= 0.005:
            return
        new_alloc = round(D.F.b_alloc(month, bid) + add, 2)
        month.setdefault("allocations", {})[bid] = new_alloc
        if not current_app.config["DEV_SEED"]:
            DB.upsert_alloc(u, t, D.active_mid(), bid, new_alloc)

    for o in ctx["obligations"]:
        if o["checked"]:
            _bump(o["id"], o["gap"])
    for r in ctx["rule_suggestions"]:
        if r["checked"]:
            _bump(r["bucket_id"], r["computed"])

    return ("Distribution applied.", "ok")


register(Action("distribute_apply", _distribute_apply, "buckets",
                 response_mode="close_modal", always_run=True))


def _tx_apply_rules(u, t, f, data):
    tid = f.get("id", "")
    tx = next((tr for tr in data.get("txs", []) if tr.get("id") == tid), None)
    if not tx:
        return ("Transaction not found.", "error")

    amount = float(tx.get("amount") or 0)
    mid = tx.get("monthId") or D.active_mid()
    month = next((m for m in data.get("months", []) if m.get("id") == mid),
                 {"id": mid, "allocations": {}})
    rules_raw = sorted(
        [r for r in data.get("allocationRules", []) if r.get("active", True)],
        key=lambda r: r.get("sort_order", 0))

    applied = 0
    remaining = amount
    for r in rules_raw:
        v = float(r.get("value") or 0)
        vtype = r.get("value_type", "fixed")
        if vtype == "fund":
            computed = round(max(0.0, remaining), 2)
        else:
            computed = round(amount * v / 100, 2) if vtype == "pct" else v
        remaining = round(remaining - computed, 2)

        if r.get("rule_type", "internal") == "external":
            continue
        bid = r.get("bucket_id") or r.get("bucketId") or ""
        if not bid or computed <= 0:
            continue
        new_alloc = round(D.F.b_alloc(month, bid) + computed, 2)
        if not current_app.config["DEV_SEED"]:
            DB.upsert_alloc(u, t, mid, bid, new_alloc)
        applied += 1

    return (f"Applied {applied} allocation rule{'s' if applied != 1 else ''}.", "ok")


register(Action("tx_apply_rules", _tx_apply_rules, "buckets",
                 response_mode="close_modal", always_run=True))


def _tx_paycheck_distribute(u, t, f, data):
    tid = f.get("id", "")
    tx = next((tr for tr in data.get("txs", []) if tr.get("id") == tid), None)
    if not tx:
        return ("Transaction not found.", "error")

    amount = float(tx.get("amount") or 0)
    mid = tx.get("monthId") or D.active_mid()
    ctx = D.paycheck_distribute_ctx(
        amount, mid,
        checked_rule=set(f.getlist("rule")),
        checked_ob=set(f.getlist("ob")),
        checked_fund=set(f.getlist("fund")),
        checked_next=set(f.getlist("next_ob")),
        checked_forecast_ob=set(f.getlist("forecast_ob")),
    )
    if not current_app.config["DEV_SEED"]:
        month = D.active_month(data, mid)
        next_mid = ctx["next_mid"]
        next_month = D.active_month(data, next_mid)
        for r in ctx["internal_rules"]:
            if r["checked"] and r["computed"] > 0:
                new_alloc = round(D.F.b_alloc(month, r["bucket_id"]) + r["computed"], 2)
                DB.upsert_alloc(u, t, mid, r["bucket_id"], new_alloc)
        for o in ctx["obligations"]:
            if o["checked"] and o["gap"] > 0:
                new_alloc = round(D.F.b_alloc(month, o["id"]) + o["gap"], 2)
                DB.upsert_alloc(u, t, mid, o["id"], new_alloc)
        for r in ctx["fund_rules"]:
            if r["checked"] and r["computed"] > 0:
                new_alloc = round(D.F.b_alloc(month, r["bucket_id"]) + r["computed"], 2)
                DB.upsert_alloc(u, t, mid, r["bucket_id"], new_alloc)
        for o in ctx["next_obligations"]:
            if o["checked"] and o["gap"] > 0:
                new_alloc = round(D.F.b_alloc(next_month, o["id"]) + o["gap"], 2)
                DB.upsert_alloc(u, t, next_mid, o["id"], new_alloc)
        for fo in ctx["forecast_obligations"]:
            if fo["checked"] and fo["amount_raw"] > 0:
                new_alloc = round(D.F.b_alloc(month, fo["bucket_id"]) + fo["amount_raw"], 2)
                DB.upsert_alloc(u, t, mid, fo["bucket_id"], new_alloc)

    total_dist = round(ctx["total_applied"] + ctx["total_forecast_ob"], 2)
    return (f"Distributed {total_dist:,.2f}.", "ok")


register(Action("tx_paycheck_distribute", _tx_paycheck_distribute, "buckets",
                 response_mode="close_modal", always_run=True))


def _vault_transfer(u, t, f, data):
    bid = f.get("id", "")
    to_bid = f.get("to_bid", "")
    amount = D.parse_amount(f.get("amount", "0"))
    if not (amount > 0 and to_bid):
        return None

    month = D.active_month(data)
    mid = D.active_mid()
    from_alloc = D.F.b_alloc(month, bid)
    to_alloc = D.F.b_alloc(month, to_bid)
    new_from = max(0.0, round(from_alloc - amount, 2))
    new_to = round(to_alloc + amount, 2)
    if not current_app.config["DEV_SEED"]:
        DB.vault_transfer(u, t, mid, bid, to_bid, amount, new_from, new_to)
        return (f"Transferred ${amount:,.2f} from vault.", "ok")
    return ("Dev mode: transfer not persisted.", "ok")


register(Action("vault_transfer", _vault_transfer, "buckets",
                 response_mode="close_modal", always_run=True))


def _vault_release(u, t, f, data):
    bid = f.get("id", "")
    amount = D.parse_amount(f.get("amount", "0"))
    if not (amount > 0):
        return None

    month = D.active_month(data)
    mid = D.active_mid()
    current_alloc = D.F.b_alloc(month, bid)
    if not current_app.config["DEV_SEED"]:
        DB.vault_release_to_pool(u, t, mid, bid, amount, current_alloc)
        reason = f.get("reason", "").strip()
        is_planned = f.get("is_planned") == "1"
        if reason:
            DB.log_vault_release(u, t, mid, bid, amount, reason, is_planned)
        return (f"Released ${amount:,.2f} from vault to pool.", "ok")
    return ("Dev mode: release not persisted.", "ok")


register(Action("vault_release", _vault_release, "buckets",
                 response_mode="close_modal", always_run=True))


# ── Transaction actions (Phase 5: dynamic back-panel) ───────────────────────

def _tx_back_panel(f):
    back = f.get("back") or "accounts"
    return back if back in _PANEL_MAP else "accounts"


def _tx_update(u, t, f, data):
    tid = f.get("id", "")
    amount = D.parse_amount(f.get("amount", "0"))
    iso = f.get("date") or D.tx_form_ctx()["today"]
    y, m, _ = (iso[:10].split("-") + ["1", "1", "1"])[:3]
    mid = D.F.month_id(int(y), int(m) - 1)
    if not current_app.config["DEV_SEED"]:
        DB.update_transaction(u, t, tid, {
            "account_id": f.get("accountId", ""),
            "month_id": mid,
            "type": f.get("type", "out"),
            "amount": amount,
            "date": iso,
            "description": f.get("desc", ""),
            "bucket_id": f.get("bucketId") or None,
            "to_account_id": f.get("toAccountId") or None,
            "reconciled": f.get("reconciled") == "1",
            "income_type": f.get("incomeType") or None,
            "paycheck_id": f.get("paycheckId") or None,
            "planned": f.get("planned", "1") == "1",
        })
        return ("Transaction updated.", "ok")
    return ("Dev mode: change not persisted.", "ok")


register(Action("tx_update", _tx_update, back_panel=_tx_back_panel,
                 response_mode="close_modal", always_run=True))


def _tx_delete(u, t, f, data):
    if not current_app.config["DEV_SEED"]:
        DB.delete_transaction(u, t, f.get("id", ""))
        return ("Transaction deleted.", "ok")
    return ("Dev mode: change not persisted.", "ok")


register(Action("tx_delete", _tx_delete, back_panel=_tx_back_panel,
                 response_mode="close_modal", always_run=True))


def _close_panel(back_panel, htmx):
    if htmx:
        resp = make_response(_render_panel(back_panel, htmx))
        resp.headers["HX-Trigger"] = "closeModal"
        return resp
    return redirect(url_for(f"panels.{back_panel}"))


def _tx_create(u, t, f, data):
    amount = D.parse_amount(f.get("amount", "0"))
    iso = f.get("date") or D.tx_form_ctx()["today"]
    y, m, _ = (iso[:10].split("-") + ["1", "1", "1"])[:3]
    mid = D.F.month_id(int(y), int(m) - 1)
    tx = {
        "accountId": f.get("accountId", ""), "monthId": mid,
        "type": f.get("type", "out"), "amount": amount, "date": iso,
        "desc": f.get("desc", ""), "bucketId": f.get("bucketId") or "",
        "toAccountId": f.get("toAccountId") or "",
        "incomeType": f.get("incomeType") or "paycheck",
        "paycheckId": f.get("paycheckId") or "",
        "planned": f.get("planned", "1") == "1",
    }
    back_panel = _tx_back_panel(f)
    htmx = request.headers.get("HX-Request") == "true"

    # Block vault buckets from receiving transactions
    bucket_id = tx.get("bucketId", "")
    if bucket_id:
        bkt = next((b for b in data.get("buckets", []) if b["id"] == bucket_id), None)
        if bkt and bkt.get("type") == "vault":
            flash("Vault buckets cannot hold transactions. Use Transfer instead.", "error")
            return _close_panel(back_panel, htmx)

    again = f.get("again") == "1"

    # Split transaction across multiple buckets: one row per split, each its
    # own transaction sharing date/account/payee.
    split_bkts = [b for b in f.getlist("split_bucket") if b]
    split_amts = [D.parse_amount(a) for a in f.getlist("split_amount")]
    if split_bkts and tx["type"] == "out":
        splits = [(b, a) for b, a in zip(split_bkts, split_amts) if a > 0]
        bkt_by_id = {b["id"]: b for b in data.get("buckets", [])}
        vault_split = next((b for b, _ in splits if bkt_by_id.get(b, {}).get("type") == "vault"), None)
        split_total = round(sum(a for _, a in splits), 2)
        if vault_split:
            flash("Vault buckets cannot hold transactions. Use Transfer instead.", "error")
            return _close_panel(back_panel, htmx)
        elif not splits or abs(split_total - round(amount, 2)) > 0.005:
            flash(f"Splits must total ${amount:,.2f} (currently ${split_total:,.2f}).", "error")
            return _close_panel(back_panel, htmx)
        elif current_app.config["DEV_SEED"]:
            flash("Dev mode: transaction not persisted (no database).", "ok")
        elif tx["accountId"]:
            for bid, a in splits:
                DB.insert_transaction(u, t, {**tx, "amount": a, "bucketId": bid})
            D.invalidate_cache()
            flash(f"Split transaction added across {len(splits)} buckets.", "ok")
        else:
            flash("Account is required.", "error")
        return _close_panel(back_panel, htmx)

    if current_app.config["DEV_SEED"]:
        flash("Dev mode: transaction not persisted (no database).", "ok")
    elif amount > 0 and tx["accountId"]:
        new_tid = DB.insert_transaction(u, t, tx)
        D.invalidate_cache()
        if again and htmx:
            shell = D.shell_ctx(back_panel)
            resp = make_response(
                render_template("panels/_frag_add_tx.html", tx_type=tx["type"], back=back_panel,
                                **D.tx_form_ctx())
                + render_template("panels/_oob_rts.html", shell=shell)
                + f'<div data-toast-msg="Transaction added." data-toast-type="ok"></div>')
            return resp
        flash("Transaction added.", "ok")
        # After a paycheck, open the combined distribute modal
        if tx["type"] == "in" and tx.get("incomeType") == "paycheck" and htmx:
            ctx = D.paycheck_distribute_ctx(amount, mid)
            shell = D.shell_ctx(back_panel)
            resp = make_response(
                render_template("panels/_frag_paycheck_distribute.html",
                                tid=new_tid, back=back_panel, **ctx)
                + render_template("panels/_oob_rts.html", shell=shell))
            resp.headers["HX-Retarget"] = "#modal-body"
            resp.headers["HX-Reswap"] = "innerHTML"
            return resp
    else:
        flash("Amount and account are required.", "error")

    return _close_panel(back_panel, htmx)


register(Action("tx_create", _tx_create, response_mode="oob", always_run=True))


# ── Scenario actions (Phase 5: OOB forecast fragment) ───────────────────────

def _scenario_create(u, t, f, data):
    from .panels import _fc_frag_response, _safe_n_months, _parse_scenario_form
    allocs = _parse_scenario_form(f, data)
    name = (f.get("name") or "Scenario").strip()[:40]
    n_months = _safe_n_months(f.get("n_months"))
    if not current_app.config["DEV_SEED"]:
        sid = DB.save_scenario(u, t, name, allocs)
        D.invalidate_cache()
    else:
        sid = ""
    return _fc_frag_response(active_sid=sid, n_months=n_months)


register(Action("scenario_create", _scenario_create, response_mode="oob", always_run=True))


def _scenario_update(u, t, f, data):
    from .panels import _fc_frag_response, _safe_n_months, _parse_scenario_form
    sid = f.get("id", "")
    allocs = _parse_scenario_form(f, data)
    name = (f.get("name") or "Scenario").strip()[:40]
    n_months = _safe_n_months(f.get("n_months"))
    if not current_app.config["DEV_SEED"]:
        DB.update_scenario(u, t, sid, name, allocs)
        D.invalidate_cache()
    return _fc_frag_response(active_sid=sid, n_months=n_months)


register(Action("scenario_update", _scenario_update, response_mode="oob", always_run=True))


def _scenario_delete(u, t, f, data):
    from .panels import _fc_frag_response, _safe_n_months
    n_months = _safe_n_months(f.get("n_months"))
    if not current_app.config["DEV_SEED"]:
        DB.delete_scenario(u, t, f.get("id", ""))
        D.invalidate_cache()
    return _fc_frag_response(active_sid="", n_months=n_months)


register(Action("scenario_delete", _scenario_delete, response_mode="oob", always_run=True))
