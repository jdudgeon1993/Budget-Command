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
