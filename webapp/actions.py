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
    dev_seed_msg: str = "Dev mode: change not persisted."


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

    if not current_app.config["DEV_SEED"]:
        action.fn(session["user_id"], session["access_token"], form, data)
        D.invalidate_cache()
        msg = action.flash_msg(form) if action.flash_msg else None
    else:
        msg = (action.dev_seed_msg, "ok")
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
