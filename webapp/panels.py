"""Panels — the dashboard shell + injected panel content.

Each panel route renders the same template two ways: full page on a hard load,
just the #panel fragment on an HTMX request (SPA-feel, no reload).
"""

from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, current_app, flash, jsonify, Response, make_response)

from . import db as DB
from . import data as D
from .auth import login_required

bp = Blueprint("panels", __name__)

PANELS = ["buckets", "accounts", "insights", "reports", "setup"]


def render_panel(template, active_panel, **ctx):
    """Full page on normal load, bare fragment on HTMX request.

    The same view functions are also mounted under the "proto" blueprint
    (see webapp/__init__.py) at /proto/v4 — a full live mirror used to
    redesign one section at a time without touching the production routes.
    request.blueprint tells us which mount served this request so the
    mirror gets its own full-page shell (nav links stay inside /proto/v4)
    while the HTMX partial layout is identical either way.
    """
    session["active_panel"] = active_panel
    htmx = request.headers.get("HX-Request") == "true"
    dash = None
    if htmx:
        layout = "_partial.html"
    else:
        layout = "proto_base.html" if request.blueprint == "proto" else "base.html"
        # Dashboard (layer 1) is part of the persistent v4 shell, rendered on
        # every hard page load — not recomputed for htmx fragment swaps,
        # which only ever replace #panel and never touch the shell around it.
        if request.blueprint == "proto":
            dash = D.dashboard_ctx()
    return render_template(template, layout=layout, dash=dash,
                           shell=D.shell_ctx(active_panel), **ctx)


def _bucket_template() -> str:
    """buckets.html normally; the redesigned v4 layout under the proto mirror."""
    return "panels/buckets_v4.html" if request.blueprint == "proto" else "panels/buckets.html"


def _bucket_settings_template() -> str:
    """Settings-form fragment: classic 3-field-group form, or the v4 redesign."""
    return "panels/_frag_bucket_v4.html" if request.blueprint == "proto" else "panels/_frag_bucket.html"


@bp.route("/")
def index():
    if request.blueprint == "proto":
        return redirect(url_for(".dashboard"))
    return redirect(url_for(".buckets"))


@bp.route("/dashboard")
@login_required
def dashboard():
    """Layer 1 of the map+sheet redesign — v4 prototype only.

    Classic keeps its old behavior (redirect straight to Buckets) untouched.
    """
    if request.blueprint != "proto":
        return redirect(url_for(".buckets"))
    return render_panel("panels/dashboard_v4.html", "buckets", sheet_open=False)


# ── Buckets ───────────────────────────────────────────────────────────────────

@bp.route("/buckets")
@login_required
def buckets():
    view_mid = request.args.get("m") or None
    return render_panel(_bucket_template(), "buckets", **D.bucket_rows(view_mid=view_mid))


@bp.route("/buckets/<bid>/alloc", methods=["POST"])
@login_required
def set_alloc(bid):
    """Inline allocation edit -> returns the updated row + OOB shell refresh.

    Targets the month being viewed (the "m" tab/param), not whatever the
    sidebar arrows last left session["active_mid"] at — those are two
    different navigation mechanisms and edits must follow the one the user
    is actually looking at.
    """
    try:
        amount = round(float(request.form.get("alloc", "0").replace("$", "").replace(",", "")), 2)
    except ValueError:
        amount = 0.0
    target_mid = request.values.get("m") or D.active_mid()
    data = D.load_data()
    month = D.active_month(data, target_mid)
    month.setdefault("allocations", {})[bid] = amount
    if not current_app.config["DEV_SEED"]:
        # A future month tab you've never touched before has no bcc_months
        # row yet — load_all() only ever attaches allocations to months it
        # finds there, so writing the allocation without this first creates
        # an orphaned row that silently vanishes on the next page load.
        DB.ensure_month(session["user_id"], session["access_token"], target_mid)
        DB.upsert_alloc(session["user_id"], session["access_token"],
                        target_mid, bid, amount)
        D.invalidate_cache()
    return _buckets_response(view_mid=target_mid)


# ── Bucket fill / distribute ─────────────────────────────────────────────────

@bp.route("/buckets/<bid>/fill", methods=["POST"])
@login_required
def fill_bucket(bid):
    """Set allocation = max(budget, spent) — fills to target or covers actual spend.

    Targets the viewed month (see set_alloc) — the "m" hidden field this
    button already sends was previously never read, so Fill/Cover on a
    future-month tab was silently applying to the wrong month.
    """
    target_mid = request.values.get("m") or D.active_mid()
    data = D.load_data()
    month = D.active_month(data, target_mid)
    budget = D.F.b_budget(month, bid)
    spent  = D.F.b_spent(target_mid, bid, data.get("txs", []))
    new_alloc = max(budget, spent)
    month.setdefault("allocations", {})[bid] = new_alloc
    if not current_app.config["DEV_SEED"]:
        DB.ensure_month(session["user_id"], session["access_token"], target_mid)
        DB.upsert_alloc(session["user_id"], session["access_token"],
                        target_mid, bid, new_alloc)
        D.invalidate_cache()
    flash("Covered." if spent > budget else "Filled.", "ok")
    return _buckets_response(view_mid=target_mid)


def _distribute_checks():
    """Checkbox state from the Distribute form, or None for the un-submitted default."""
    if "ob" not in request.form and "rule" not in request.form:
        return None, None
    return set(request.form.getlist("ob")), set(request.form.getlist("rule"))


@bp.route("/buckets/distribute")
@login_required
def distribute_modal():
    """Open the Distribute modal: ranked funding suggestions to review and apply."""
    ctx = D.distribute_ctx()
    if _is_modal():
        resp = make_response(render_template("panels/_frag_distribute.html", **ctx))
        resp.headers["HX-Retarget"] = "#modal-body"
        resp.headers["HX-Reswap"] = "innerHTML"
        return resp
    return _buckets_response()


@bp.route("/buckets/distribute/preview", methods=["POST"])
@login_required
def distribute_preview():
    """Re-render the Distribute modal reflecting the user's current checkbox state."""
    checked_ob, checked_rule = _distribute_checks()
    ctx = D.distribute_ctx(checked_ob=checked_ob, checked_rule=checked_rule)
    resp = make_response(render_template("panels/_frag_distribute.html", **ctx))
    resp.headers["HX-Retarget"] = "#modal-body"
    resp.headers["HX-Reswap"] = "innerHTML"
    return resp


@bp.route("/buckets/distribute", methods=["POST"])
@login_required
def distribute_rts():
    """Apply the selected obligations and rule suggestions from the Distribute modal.

    Re-derives suggested amounts server-side (never trusts client-submitted
    dollar figures) and only funds the items the user left checked.
    """
    checked_ob, checked_rule = _distribute_checks()
    ctx = D.distribute_ctx(checked_ob=checked_ob, checked_rule=checked_rule)
    data = D.load_data()
    month = D.active_month(data)

    def _bump(bid, add):
        if add <= 0.005:
            return
        new_alloc = round(D.F.b_alloc(month, bid) + add, 2)
        month.setdefault("allocations", {})[bid] = new_alloc
        if not current_app.config["DEV_SEED"]:
            DB.upsert_alloc(session["user_id"], session["access_token"],
                            D.active_mid(), bid, new_alloc)

    for o in ctx["obligations"]:
        if o["checked"]:
            _bump(o["id"], o["gap"])

    for r in ctx["rule_suggestions"]:
        if r["checked"]:
            _bump(r["bucket_id"], r["computed"])

    if not current_app.config["DEV_SEED"]:
        D.invalidate_cache()
    flash("Distribution applied.", "ok")
    if request.headers.get("HX-Request") == "true":
        return _panel_close_modal(_bucket_template(), "buckets", **D.bucket_rows())
    return _buckets_response()


def _buckets_response(view_mid: str = None):
    """Return buckets panel for HTMX or redirect for plain requests.

    Preserves whichever month the user was looking at (view_mid) so an edit
    to a future month doesn't snap the page back to the current month.
    """
    if request.headers.get("HX-Request") == "true":
        return render_panel(_bucket_template(), "buckets", **D.bucket_rows(view_mid=view_mid))
    return redirect(url_for(".buckets"))


def _is_modal():
    target = request.headers.get("HX-Target", "")
    return (target == "modal-body" or target.startswith("bkt-settings-")
            or target.startswith("tx-edit-") or target.startswith("acct-settings-"))


def _panel_close_modal(panel_tmpl, active_panel, **ctx):
    """Return panel HTML + HX-Trigger:closeModal for HTMX form submits inside modals."""
    resp = make_response(render_panel(panel_tmpl, active_panel, **ctx))
    resp.headers["HX-Trigger"] = "closeModal"
    return resp


_PANEL_MAP = {
    "accounts": ("panels/accounts.html", lambda: D.accounts_view()),
    "reports":  ("panels/reports.html",  lambda: D.reports_view()),
    "setup":    ("panels/setup.html",    lambda: D.setup_view()),
}


def _panel_lookup(back_panel: str):
    """Template + context-fn for a "back to panel X" redirect.

    Buckets needs the blueprint-aware template (see _bucket_template);
    everything else is a fixed 1:1 mapping via _PANEL_MAP.
    """
    if back_panel == "buckets":
        return _bucket_template(), (lambda: D.bucket_rows())
    return _PANEL_MAP.get(back_panel, _PANEL_MAP["accounts"])


# ── Bucket settings ───────────────────────────────────────────────────────────

@bp.route("/buckets/<bid>/settings", methods=["GET", "POST"])
@login_required
def bucket_settings(bid):
    data = D.load_data()
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bid), None)
    if not bucket:
        flash("Bucket not found.", "error")
        return redirect(url_for(".buckets"))
    cats = data.get("cats", [])
    if request.method == "POST":
        f = request.form
        def _num(key, default=0.0):
            try:
                return round(float((f.get(key) or "0").replace("$", "").replace(",", "")), 2)
            except ValueError:
                return default
        if not current_app.config["DEV_SEED"]:
            btype = f.get("type", bucket.get("type", "expense"))
            payload = {
                "name": f.get("name", bucket["name"]).strip(),
                "cat_id": f.get("catId", bucket.get("catId", "")),
                "type": btype,
                "notes": f.get("notes", ""),
            }
            if "target_budget" in f:
                # v4 form: one Target Budget field + one Frequency + one Due
                # Date, reused across types instead of three field-groups.
                # No Recurring Bill / Due Amount — dropped as redundant.
                target_budget = _num("target_budget")
                if btype in ("goal", "sinking"):
                    payload.update({
                        "target_amount": target_budget,
                        "target_date": f.get("due_date") or None,
                        "contrib_freq": f.get("frequency") or None,
                    })
                else:
                    payload["default_budget"] = target_budget
                    if btype == "expense":
                        payload.update({
                            "due_day": (f.get("due_date") or "").strip() or None,
                            "pay_freq": f.get("frequency") or None,
                            "flex": f.get("flex") == "1",
                        })
            else:
                payload["default_budget"] = _num("default_budget")
                if btype == "expense":
                    payload.update({
                        "due_day": (f.get("due_day") or "").strip() or None,
                        "due_amount": _num("due_amount"),
                        "pay_freq": f.get("pay_freq") or None,
                        "recurring": f.get("recurring") == "1",
                        "flex": f.get("flex") == "1",
                    })
                elif btype in ("goal", "sinking"):
                    payload.update({
                        "target_amount": _num("target_amount"),
                        "target_date": f.get("target_date") or None,
                        "contrib_freq": f.get("contrib_freq") or None,
                    })
            DB.upsert_bucket(session["user_id"], session["access_token"], bid, payload)
            D.invalidate_cache()
            flash("Bucket updated.", "ok")
        else:
            flash("Dev mode: change not persisted.", "ok")
        if request.headers.get("HX-Request") == "true":
            return _panel_close_modal(_bucket_template(), "buckets", **D.bucket_rows())
        return redirect(url_for(".buckets"))
    data_ctx = D.load_data()
    debt_accounts = [{"id": a["id"], "name": a["name"]}
                     for a in data_ctx.get("accounts", [])
                     if a.get("type") == "debt" and not a.get("archived")]
    if _is_modal():
        return render_template(_bucket_settings_template(), bucket=bucket, cats=cats,
                               debt_accounts=debt_accounts)
    return render_panel("panels/edit_bucket.html", "buckets",
                        bucket=bucket, cats=cats, debt_accounts=debt_accounts)


@bp.route("/buckets/<bid>/archive", methods=["POST"])
@login_required
def archive_bucket(bid):
    if not current_app.config["DEV_SEED"]:
        DB.upsert_bucket(session["user_id"], session["access_token"], bid, {"archived": True})
        D.invalidate_cache()
        flash("Bucket archived.", "ok")
    else:
        flash("Dev mode: change not persisted.", "ok")
    if request.headers.get("HX-Request") == "true":
        return _panel_close_modal(_bucket_template(), "buckets", **D.bucket_rows())
    return redirect(url_for(".buckets"))


@bp.route("/buckets/<bid>/vault-transfer", methods=["GET", "POST"])
@login_required
def vault_transfer(bid):
    data = D.load_data()
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bid), None)
    if not bucket or bucket.get("type") != "vault":
        return redirect(url_for(".buckets"))
    if request.method == "POST":
        f = request.form
        to_bid = f.get("to_bid", "")
        try:
            amount = round(float(f.get("amount", "0").replace("$", "").replace(",", "")), 2)
        except ValueError:
            amount = 0.0
        if amount > 0 and to_bid:
            month = D.active_month(data)
            mid = D.active_mid()
            from_alloc = D.F.b_alloc(month, bid)
            to_alloc = D.F.b_alloc(month, to_bid)
            # This route only ever touches the current month's own allocation
            # (it doesn't reach into prior-month accumulation the way vault
            # release does) — so the amount actually available to move is
            # capped at from_alloc. Both sides need to use that same clamped
            # figure; crediting the destination with the original, unclamped
            # amount while the source silently clamped to 0 would credit more
            # than was ever actually drained from the vault.
            amount = min(amount, from_alloc)
            new_from = max(0.0, round(from_alloc - amount, 2))
            new_to = round(to_alloc + amount, 2)
            if not current_app.config["DEV_SEED"]:
                DB.vault_transfer(session["user_id"], session["access_token"],
                                  mid, bid, to_bid, amount, new_from, new_to)
                D.invalidate_cache()
                flash(f"Transferred ${amount:,.2f} from vault.", "ok")
            else:
                flash("Dev mode: transfer not persisted.", "ok")
        if request.headers.get("HX-Request") == "true":
            return _panel_close_modal(_bucket_template(), "buckets", **D.bucket_rows())
        return redirect(url_for(".buckets"))
    # GET — render transfer form in modal
    dest_buckets = [b for b in data.get("buckets", [])
                    if not b.get("archived") and b.get("type") != "vault"]
    cats = sorted(data.get("cats", []), key=lambda c: c.get("order", 0))
    bkt_name = {b["id"]: b["name"] for b in data.get("buckets", [])}
    month = D.active_month(data)
    vault_alloc = D.F.b_alloc(month, bid)
    vault_accum = D.F.vault_accumulated(bid, data.get("months", []))
    dest_by_cat = []
    for c in cats:
        bkts = [b for b in dest_buckets if b.get("catId") == c["id"]]
        if bkts:
            dest_by_cat.append({"cat": c["name"], "buckets": bkts})
    return render_template("panels/_frag_vault_transfer.html",
                           bucket=bucket, dest_by_cat=dest_by_cat,
                           vault_alloc=vault_alloc, vault_accum=vault_accum)


@bp.route("/buckets/<bid>/vault-release", methods=["GET", "POST"])
@login_required
def vault_release_to_pool(bid):
    data = D.load_data()
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bid), None)
    if not bucket or bucket.get("type") != "vault":
        return redirect(url_for(".buckets"))
    if request.method == "POST":
        f = request.form
        try:
            amount = round(float(f.get("amount", "0").replace("$", "").replace(",", "")), 2)
        except ValueError:
            amount = 0.0
        # The form pre-fills this with the accumulated total, but it's a
        # plain editable text field the client can submit anything through
        # (including a stale/duplicate figure from a modal that wasn't
        # refreshed between two release attempts). Never trust it past what
        # the vault actually holds right now — clamping here is what stops
        # a double-submit from draining the same savings twice and going
        # negative.
        true_accum = max(D.F.vault_accumulated(bid, data.get("months", [])), 0.0)
        amount = min(amount, true_accum)
        if amount > 0:
            month = D.active_month(data)
            mid = D.active_mid()
            current_alloc = D.F.b_alloc(month, bid)
            if not current_app.config["DEV_SEED"]:
                DB.vault_release_to_pool(session["user_id"], session["access_token"],
                                         mid, bid, amount, current_alloc)
                reason = f.get("reason", "").strip()
                is_planned = f.get("is_planned") == "1"
                if reason:
                    DB.log_vault_release(session["user_id"], session["access_token"],
                                         mid, bid, amount, reason, is_planned)
                D.invalidate_cache()
                flash(f"Released ${amount:,.2f} from vault to pool.", "ok")
            else:
                flash("Dev mode: release not persisted.", "ok")
        if request.headers.get("HX-Request") == "true":
            return _panel_close_modal(_bucket_template(), "buckets", **D.bucket_rows())
        return redirect(url_for(".buckets"))
    # GET — render release form in modal
    month = D.active_month(data)
    vault_alloc = D.F.b_alloc(month, bid)
    vault_accum = D.F.vault_accumulated(bid, data.get("months", []))
    return render_template("panels/_frag_vault_release.html",
                           bucket=bucket, vault_alloc=vault_alloc, vault_accum=vault_accum)


@bp.route("/buckets/<bid>/vault-adjust", methods=["GET", "POST"])
@login_required
def vault_adjust_balance(bid):
    """Correct a vault's accumulated total to a true value.

    Not a normal contribution or release — this exists for fixing bad
    historical data (e.g. a bug that let a release overshoot what the
    vault actually held), recorded as an explicit, audited adjustment
    rather than quietly hand-editing a month's numbers.
    """
    data = D.load_data()
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bid), None)
    if not bucket or bucket.get("type") != "vault":
        return redirect(url_for(".buckets"))
    current_accum = D.F.vault_accumulated(bid, data.get("months", []))
    if request.method == "POST":
        f = request.form
        try:
            target = round(float(f.get("target", "0").replace("$", "").replace(",", "")), 2)
        except ValueError:
            target = current_accum
        target = max(target, 0.0)
        delta = round(target - current_accum, 2)
        if abs(delta) > 0.005:
            mid = D.active_mid()
            if not current_app.config["DEV_SEED"]:
                DB.ensure_month(session["user_id"], session["access_token"], mid)
                DB.vault_adjust_balance(session["user_id"], session["access_token"],
                                        mid, bid, delta)
                reason = f.get("reason", "").strip() or "Balance correction"
                DB.log_vault_release(session["user_id"], session["access_token"],
                                     mid, bid, abs(delta), f"Correction: {reason}", True)
                D.invalidate_cache()
                flash(f"Corrected {bucket['name']} to ${target:,.2f}.", "ok")
            else:
                flash("Dev mode: correction not persisted.", "ok")
        if request.headers.get("HX-Request") == "true":
            return _panel_close_modal(_bucket_template(), "buckets", **D.bucket_rows())
        return redirect(url_for(".buckets"))
    # GET — render correction form in modal
    return render_template("panels/_frag_vault_adjust.html",
                           bucket=bucket, current_accum=current_accum)


# ── Budget inline edit ───────────────────────────────────────────────────────

@bp.route("/buckets/<bid>/budget", methods=["POST"])
@login_required
def set_budget(bid):
    """Targets the viewed month (see set_alloc for why this matters)."""
    try:
        amount = round(float(request.form.get("budget", "0").replace("$", "").replace(",", "")), 2)
    except ValueError:
        amount = 0.0
    saving_mid = request.values.get("m") or D.active_mid()
    data = D.load_data()
    month = D.active_month(data, saving_mid)
    month.setdefault("budgets", {})[bid] = amount
    if not current_app.config["DEV_SEED"]:
        DB.ensure_month(session["user_id"], session["access_token"], saving_mid)
        DB.upsert_budget(session["user_id"], session["access_token"],
                         saving_mid, bid, amount)
        if saving_mid == D.F.current_month_id():
            for m in data.get("months", []):
                if D.F.month_status(m["id"]) == "future":
                    DB.upsert_budget(session["user_id"], session["access_token"],
                                     m["id"], bid, amount)
        D.invalidate_cache()
    return _buckets_response(view_mid=saving_mid)


@bp.route("/buckets/<bid>/target-amount", methods=["POST"])
@login_required
def set_target_amount(bid):
    """Inline edit for a Goal/Sinking bucket's overall target amount.

    Unlike set_budget, this isn't month-scoped — targetAmount lives on the
    bucket record itself, the same one field editable in Settings. Making
    it inline too matches the "Allocated vs Target is the same rule for
    every type" decision (see plan) rather than treating Goal as a special
    case that needs its own drawer trip just to nudge the number.
    """
    try:
        amount = round(float(request.form.get("target_amount", "0").replace("$", "").replace(",", "")), 2)
    except ValueError:
        amount = 0.0
    if not current_app.config["DEV_SEED"]:
        DB.upsert_bucket(session["user_id"], session["access_token"], bid, {"target_amount": amount})
        D.invalidate_cache()
    return _buckets_response(view_mid=request.values.get("m") or None)


# ── Add bucket ────────────────────────────────────────────────────────────────

@bp.route("/buckets", methods=["POST"])
@login_required
def add_bucket():
    f = request.form
    name = f.get("name", "").strip()
    cat_id = f.get("catId", "")
    btype = f.get("type", "expense")
    if name and cat_id and not current_app.config["DEV_SEED"]:
        DB.insert_bucket(session["user_id"], session["access_token"], name, cat_id, btype)
        D.invalidate_cache()
        flash("Bucket added.", "ok")
    elif current_app.config["DEV_SEED"]:
        flash("Dev mode: bucket not persisted.", "ok")
    else:
        flash("Name and category are required.", "error")
    return _buckets_response()


# ── Bucket reorder ────────────────────────────────────────────────────────────

@bp.route("/buckets/<bid>/handled", methods=["POST"])
@login_required
def toggle_handled(bid):
    mid = D.active_mid()
    data = D.load_data()
    month = D.active_month(data)
    currently = bool((month.get("handledBuckets") or {}).get(bid))
    if not current_app.config["DEV_SEED"]:
        DB.ensure_month(session["user_id"], session["access_token"], mid)
        DB.toggle_handled(session["user_id"], session["access_token"], mid, bid, currently)
        D.invalidate_cache()
    return _buckets_response()


# ── Month workflow ────────────────────────────────────────────────────────────

@bp.route("/month/close", methods=["POST"])
@login_required
def month_close():
    data = D.load_data()
    if not current_app.config["DEV_SEED"]:
        DB.close_month(session["user_id"], session["access_token"],
                       D.active_mid(), data.get("accounts", []), data.get("txs", []))
        D.invalidate_cache()
        flash("Month closed.", "ok")
    return _buckets_response()


@bp.route("/month/reopen", methods=["POST"])
@login_required
def month_reopen():
    if not current_app.config["DEV_SEED"]:
        DB.reopen_month(session["user_id"], session["access_token"], D.active_mid())
        D.invalidate_cache()
        flash("Month reopened.", "ok")
    return _buckets_response()


# ── Month navigation ──────────────────────────────────────────────────────────

@bp.route("/accounts")
@login_required
def accounts():
    return render_panel("panels/accounts.html", "accounts", **D.accounts_view())


# ── Add / edit account ────────────────────────────────────────────────────────

@bp.route("/accounts/new", methods=["GET", "POST"])
@login_required
def account_new():
    if request.method == "POST":
        f = request.form
        try:
            ob = round(float(f.get("opening_balance", "0").replace("$", "").replace(",", "")), 2)
        except ValueError:
            ob = 0.0
        name = f.get("name", "").strip()
        if name and not current_app.config["DEV_SEED"]:
            DB.insert_account(session["user_id"], session["access_token"],
                              name, f.get("type", "budget"),
                              f.get("color", "#818cf8"), ob)
            D.invalidate_cache()
            flash("Account added.", "ok")
        elif current_app.config["DEV_SEED"]:
            flash("Dev mode: account not persisted.", "ok")
        else:
            flash("Name is required.", "error")
        if request.headers.get("HX-Request") == "true":
            return _panel_close_modal("panels/accounts.html", "accounts", **D.accounts_view())
        return redirect(url_for(".accounts"))
    if _is_modal():
        return render_template("panels/_frag_account.html", account=None)
    return render_panel("panels/edit_account.html", "accounts", account=None)


@bp.route("/accounts/<aid>/edit", methods=["GET", "POST"])
@login_required
def account_edit(aid):
    data = D.load_data()
    account = next((a for a in data.get("accounts", []) if a["id"] == aid), None)
    if not account:
        flash("Account not found.", "error")
        return redirect(url_for(".accounts"))
    if request.method == "POST":
        f = request.form
        try:
            ob = round(float(f.get("opening_balance", "0").replace("$", "").replace(",", "")), 2)
        except ValueError:
            ob = 0.0
        def _numf(key):
            try:
                v = (f.get(key) or "").replace("$", "").replace(",", "").replace("%", "").strip()
                return round(float(v), 4) if v else None
            except ValueError:
                return None
        fields = {
            "name": f.get("name", "").strip(),
            "type": f.get("type", "budget"),
            "color": f.get("color", "#818cf8"),
            "opening_balance": ob,
        }
        if f.get("type") == "debt":
            apr = _numf("debt_apr")
            min_pay = _numf("debt_min_payment")
            credit = _numf("credit_limit")
            if apr is not None: fields["debt_apr"] = apr
            if min_pay is not None: fields["debt_min_payment"] = min_pay
            if credit is not None: fields["credit_limit"] = credit
            fields["is_promo"] = f.get("is_promo") == "1"
            fields["promo_end_date"] = f.get("promo_end_date") or None
        if not current_app.config["DEV_SEED"]:
            DB.update_account(session["user_id"], session["access_token"], aid, fields)
            D.invalidate_cache()
            flash("Account updated.", "ok")
        else:
            flash("Dev mode: change not persisted.", "ok")
        if request.headers.get("HX-Request") == "true":
            return _panel_close_modal("panels/accounts.html", "accounts", **D.accounts_view())
        return redirect(url_for(".accounts"))
    if _is_modal():
        return render_template("panels/_frag_account.html", account=account)
    return render_panel("panels/edit_account.html", "accounts", account=account)


@bp.route("/accounts/<aid>/archive", methods=["POST"])
@login_required
def account_archive(aid):
    if not current_app.config["DEV_SEED"]:
        DB.update_account(session["user_id"], session["access_token"], aid, {"archived": True})
        D.invalidate_cache()
        flash("Account archived.", "ok")
    else:
        flash("Dev mode: change not persisted.", "ok")
    if request.headers.get("HX-Request") == "true":
        return _panel_close_modal("panels/accounts.html", "accounts", **D.accounts_view())
    return redirect(url_for(".accounts"))


@bp.route("/accounts/<aid>/pay", methods=["GET", "POST"])
@login_required
def debt_payment(aid):
    data = D.load_data()
    account = next((a for a in data.get("accounts", []) if a["id"] == aid), None)
    if not account or account.get("type") != "debt":
        return redirect(url_for(".accounts"))
    if request.method == "POST":
        f = request.form
        try:
            amount = round(float(f.get("amount", "0").replace("$", "").replace(",", "")), 2)
        except ValueError:
            amount = 0.0
        from_aid = f.get("from_aid", "")
        pay_date = f.get("date") or D.tx_form_ctx()["today"]
        iso = pay_date[:10]
        y, m, _ = (iso.split("-") + ["1", "1", "1"])[:3]
        mid = D.F.month_id(int(y), int(m) - 1)
        bucket_id = f.get("bucketId") or ""
        if amount > 0 and from_aid and not current_app.config["DEV_SEED"]:
            DB.ensure_month(session["user_id"], session["access_token"], mid)
            DB.insert_debt_payment(session["user_id"], session["access_token"],
                                   aid, from_aid, amount, iso, mid,
                                   account["name"], bucket_id)
            D.invalidate_cache()
            flash(f"Payment of {amount:,.2f} recorded.", "ok")
        elif current_app.config["DEV_SEED"]:
            flash("Dev mode: payment not persisted.", "ok")
        if request.headers.get("HX-Request") == "true":
            return _panel_close_modal("panels/accounts.html", "accounts", **D.accounts_view())
        return redirect(url_for(".accounts"))
    # GET — render payment form
    from_accounts = [{"id": a["id"], "name": a["name"]}
                     for a in data.get("accounts", [])
                     if a.get("type") != "debt" and not a.get("archived")]
    from datetime import date as _date
    return render_template("panels/_frag_debt_payment.html",
                           account=account, from_accounts=from_accounts,
                           today=_date.today().isoformat())


@bp.route("/accounts/<aid>/payoff", methods=["GET", "POST"])
@login_required
def debt_payoff(aid):
    return debt_payment(aid)


@bp.route("/accounts/<aid>/interest", methods=["GET", "POST"])
@login_required
def post_interest(aid):
    data = D.load_data()
    account = next((a for a in data.get("accounts", []) if a["id"] == aid), None)
    if not account or account.get("type") != "debt":
        return redirect(url_for(".accounts"))
    if request.method == "POST":
        f = request.form
        try:
            amount = round(float(f.get("amount", "0").replace("$", "").replace(",", "")), 2)
        except ValueError:
            amount = 0.0
        desc = f.get("desc", "").strip() or "Interest charge"
        pay_date = f.get("date") or D.tx_form_ctx()["today"]
        if amount > 0 and not current_app.config["DEV_SEED"]:
            DB.insert_tx(session["user_id"], session["access_token"], {
                "accountId": aid, "type": "out", "amount": amount,
                "desc": desc, "date": pay_date, "monthId": D.active_mid(),
            })
            D.invalidate_cache()
        flash("Interest posted.", "ok")
        if request.headers.get("HX-Request") == "true":
            return _panel_close_modal("panels/accounts.html", "accounts", **D.accounts_view())
        return redirect(url_for(".accounts"))
    # GET — show form
    balance = abs(D.F.acct_balance(account, data.get("txs", [])))
    apr = account.get("debtAPR") or 0
    suggested = round(balance * (apr / 100) / 12, 2) if apr and balance else None
    from datetime import date as _date
    return render_template("panels/_frag_post_interest.html",
                           account=account, suggested=suggested,
                           today=_date.today().isoformat())


@bp.route("/reports")
@login_required
def reports():
    view_mid = request.args.get("m") or None
    return render_panel("panels/reports.html", "reports", **D.reports_view(view_mid=view_mid))


@bp.route("/setup")
@login_required
def setup():
    return render_panel("panels/setup.html", "setup", **D.setup_view())


@bp.route("/insights")
@login_required
def insights():
    return render_panel("panels/forecast.html", "insights", **D.forecast_view())


@bp.route("/forecast/whatif", methods=["POST"])
@login_required
def forecast_whatif():
    f = request.form
    try:
        n_months = max(1, min(12, int(f.get("n_months", 3))))
    except (ValueError, TypeError):
        n_months = 3
    try:
        inc_raw = (f.get("income_override") or "0").replace("$", "").replace(",", "").strip()
        income_override = max(0.0, float(inc_raw or 0))
    except (ValueError, TypeError):
        income_override = 0.0
    skip_raw = f.get("skip_dates", "")
    skip_dates = [s.strip() for s in skip_raw.split(",") if s.strip()]
    toggle_skip = (f.get("toggle_skip_date") or "").strip()
    if toggle_skip:
        if toggle_skip in skip_dates:
            skip_dates.remove(toggle_skip)
        else:
            skip_dates.append(toggle_skip)

    no_accrue_raw = f.get("no_accrue_dates", "")
    no_accrue_dates = [s.strip() for s in no_accrue_raw.split(",") if s.strip()]
    toggle_na = (f.get("toggle_no_accrue_date") or "").strip()
    if toggle_na:
        if toggle_na in no_accrue_dates:
            no_accrue_dates.remove(toggle_na)
        else:
            no_accrue_dates.append(toggle_na)

    active_sid = (f.get("active_scenario_id") or "").strip()
    data = D.load_data()
    scenarios = _load_scenarios()
    bucket_overrides, off_buckets, schedule, phantom_monthly = \
        _scenario_fc_params(scenarios, active_sid, n_months, data)

    from . import forecast_calc as FC
    fc = FC.compute_forecast(data, n_months=n_months, income_override=income_override,
                             skipped_pay_dates=skip_dates,
                             no_accrue_dates=no_accrue_dates,
                             bucket_overrides=bucket_overrides,
                             off_buckets=off_buckets,
                             schedule=schedule,
                             phantom_monthly=phantom_monthly)
    svg = FC.build_balance_svg(fc["periods"])
    return render_template("panels/_frag_forecast_whatif.html",
                           forecast=fc, balance_svg=svg,
                           n_months=n_months, income_override=income_override,
                           skipped_pay_dates=skip_dates,
                           skip_dates_str=",".join(skip_dates),
                           no_accrue_dates=no_accrue_dates,
                           no_accrue_dates_str=",".join(no_accrue_dates),
                           scenarios=scenarios,
                           active_scenario_id=active_sid)


# ── Scenario helpers ──────────────────────────────────────────────────────────

def _load_scenarios() -> list:
    if current_app.config.get("DEV_SEED"):
        return []
    uid = session.get("user_id", "")
    token = session.get("access_token", "")
    if not uid or not token:
        return []
    try:
        return DB.list_scenarios(uid, token)
    except Exception:
        return []


def _mid_seq(n_months: int) -> list:
    """Generate n_months+3 month IDs starting from current month."""
    from .formulas import current_month_id, parse_month_id, month_id as _mkid
    sy, sm0 = parse_month_id(current_month_id())
    result = []
    for i in range(n_months + 3):
        total = sm0 + i
        result.append(_mkid(sy + total // 12, total % 12))
    return result


def _mid_lt(a: str, b: str) -> bool:
    """True if month_id a is strictly before month_id b."""
    from .formulas import parse_month_id
    ya, ma = parse_month_id(a)
    yb, mb = parse_month_id(b)
    return ya * 12 + ma < yb * 12 + mb


_FREQ_BILL_TYPES = {"weekly", "biweekly", "triweekly", "monthly"}


def _build_fc_params(allocs: dict, data: dict, n_months: int = 12):
    """Translate scenario allocations blob into (bucket_overrides, off_buckets, schedule, phantom_monthly)."""
    bucket_overrides = dict(allocs.get("bucket_overrides") or {})
    off_buckets = list(allocs.get("off_buckets") or [])
    off_set = set(off_buckets)
    changes = allocs.get("changes") or []
    schedule = {}
    if changes:
        all_mids = _mid_seq(n_months)
        for ch in changes:
            bid = ch.get("bid", "")
            from_mid = ch.get("from_mid", "")
            ctype = ch.get("type", "off")
            if not bid or not from_mid:
                continue
            if ctype == "off":
                for mid in all_mids:
                    if not _mid_lt(mid, from_mid):
                        schedule[f"{bid}_{mid}"] = "off"
            elif ctype == "amount":
                amt = ch.get("amount")
                if amt is not None:
                    bucket_overrides[bid] = float(amt)
                for mid in all_mids:
                    if _mid_lt(mid, from_mid):
                        schedule[f"{bid}_{mid}"] = "off"
    # Buckets with no recurrence that the scenario explicitly enables/overrides
    phantom_monthly = []
    for b in data.get("buckets", []):
        if b.get("archived"):
            continue
        bid = b["id"]
        if bid in off_set:
            continue
        if b.get("dueDay") is not None or b.get("payFreq") in _FREQ_BILL_TYPES:
            continue
        amt = float(bucket_overrides.get(bid) or b.get("dueAmount") or b.get("defaultBudget") or 0)
        if amt <= 0:
            continue
        phantom_monthly.append({"id": bid, "name": b["name"], "amount": amt})
    return (bucket_overrides or None, off_buckets or None,
            schedule or None, phantom_monthly or None)


def _scenario_fc_params(scenarios: list, active_sid: str, n_months: int, data: dict):
    """Extract (bucket_overrides, off_buckets, schedule, phantom_monthly) for the active scenario."""
    if not active_sid:
        return None, None, None, None
    sc = next((s for s in scenarios if s["id"] == active_sid), None)
    if not sc:
        return None, None, None, None
    return _build_fc_params(sc.get("allocations") or {}, data, n_months)


def _parse_scenario_form(f, data: dict) -> dict:
    """Build allocations blob from the scenario editor form POST."""
    buckets = [b for b in data.get("buckets", [])
               if not b.get("archived") and b.get("type") != "vault"]
    bucket_overrides, off_buckets, changes = {}, [], []
    for b in buckets:
        bid = b["id"]
        if f.get(f"bucket_on_{bid}") != "1":
            off_buckets.append(bid)
        amt_raw = (f.get(f"bucket_amt_{bid}") or "").strip()
        if amt_raw:
            try:
                bucket_overrides[bid] = float(amt_raw.replace("$", "").replace(",", ""))
            except ValueError:
                pass
        ctype = (f.get(f"change_type_{bid}") or "").strip()
        from_mid = (f.get(f"change_from_{bid}") or "").strip()
        if ctype and from_mid:
            ch = {"bid": bid, "type": ctype, "from_mid": from_mid}
            if ctype == "amount":
                ca_raw = (f.get(f"change_amt_{bid}") or "").strip()
                if ca_raw:
                    try:
                        ch["amount"] = float(ca_raw.replace("$", "").replace(",", ""))
                    except ValueError:
                        pass
            changes.append(ch)
    return {"bucket_overrides": bucket_overrides, "off_buckets": off_buckets, "changes": changes}


def _scenario_editor_ctx(data: dict, scenario=None) -> dict:
    """Build template context for the scenario editor modal."""
    from .formulas import current_month_id, parse_month_id, month_id as _mkid
    _MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun",
                    "Jul","Aug","Sep","Oct","Nov","Dec"]
    buckets = [b for b in data.get("buckets", [])
               if not b.get("archived") and b.get("type") != "vault"]
    cats_raw = data.get("cats", [])
    cat_order = {c["id"]: c.get("order", 0) for c in cats_raw}
    cat_name  = {c["id"]: c.get("name", "Other") for c in cats_raw}
    by_cat: dict[str, list] = {}
    for b in buckets:
        cid = b.get("catId", "")
        by_cat.setdefault(cid, []).append(b)
    buckets_by_cat = [
        {"cat_name": cat_name.get(cid, "Other"), "buckets": bkts}
        for cid, bkts in sorted(by_cat.items(), key=lambda x: cat_order.get(x[0], 999))
    ]
    allocs = (scenario.get("allocations") or {}) if scenario else {}
    off_bucket_ids = set(allocs.get("off_buckets") or [])
    bucket_overrides = dict(allocs.get("bucket_overrides") or {})
    changes_by_bid = {ch["bid"]: ch for ch in (allocs.get("changes") or [])}
    sy, sm0 = parse_month_id(current_month_id())
    month_options = []
    for i in range(1, 13):
        total = sm0 + i
        yr = sy + total // 12
        mo0 = total % 12
        month_options.append({"mid": _mkid(yr, mo0),
                               "label": f"{_MONTH_NAMES[mo0]} {yr}"})
    return {
        "scenario": scenario,
        "buckets_by_cat": buckets_by_cat,
        "off_bucket_ids": off_bucket_ids,
        "bucket_overrides": bucket_overrides,
        "changes_by_bid": changes_by_bid,
        "month_options": month_options,
    }


def _fc_frag_response(active_sid: str = "", skip_dates: list = None,
                       no_accrue_dates: list = None, n_months: int = 3,
                       income_override: float = 0.0):
    """Render forecast fragment as OOB response, used after scenario save/delete."""
    skip_dates = skip_dates or []
    no_accrue_dates = no_accrue_dates or []
    data = D.load_data()
    scenarios = _load_scenarios()
    bucket_overrides, off_buckets, schedule, phantom_monthly = \
        _scenario_fc_params(scenarios, active_sid, n_months, data)
    from . import forecast_calc as FC
    fc = FC.compute_forecast(data, n_months=n_months, income_override=income_override,
                             skipped_pay_dates=skip_dates,
                             no_accrue_dates=no_accrue_dates,
                             bucket_overrides=bucket_overrides,
                             off_buckets=off_buckets,
                             schedule=schedule,
                             phantom_monthly=phantom_monthly)
    svg = FC.build_balance_svg(fc["periods"])
    fragment = render_template("panels/_frag_forecast_whatif.html",
                               forecast=fc, balance_svg=svg,
                               n_months=n_months, income_override=income_override,
                               skipped_pay_dates=skip_dates,
                               skip_dates_str=",".join(skip_dates),
                               no_accrue_dates=no_accrue_dates,
                               no_accrue_dates_str=",".join(no_accrue_dates),
                               scenarios=scenarios,
                               active_scenario_id=active_sid)
    oob = f'<div id="fc-whatif-content" hx-swap-oob="innerHTML">{fragment}</div>'
    resp = make_response(oob)
    resp.headers["HX-Trigger"] = "closeModal"
    return resp


# ── Scenario routes ───────────────────────────────────────────────────────────

@bp.route("/scenarios/editor", methods=["GET"])
@login_required
def scenario_editor_new():
    data = D.load_data()
    n_months = _safe_n_months(request.args.get("n_months"))
    ctx = _scenario_editor_ctx(data)
    return render_template("panels/_frag_scenario_editor.html", n_months=n_months, **ctx)


@bp.route("/scenarios/<sid>/editor", methods=["GET"])
@login_required
def scenario_editor_edit(sid):
    data = D.load_data()
    scenarios = _load_scenarios()
    sc = next((s for s in scenarios if s["id"] == sid), None)
    n_months = _safe_n_months(request.args.get("n_months"))
    ctx = _scenario_editor_ctx(data, sc)
    return render_template("panels/_frag_scenario_editor.html", n_months=n_months, **ctx)


@bp.route("/scenarios", methods=["POST"])
@login_required
def scenario_create():
    f = request.form
    data = D.load_data()
    allocs = _parse_scenario_form(f, data)
    name = (f.get("name") or "Scenario").strip()[:40]
    n_months = _safe_n_months(f.get("n_months"))
    if not current_app.config.get("DEV_SEED"):
        sid = DB.save_scenario(session["user_id"], session["access_token"], name, allocs)
    else:
        sid = ""
    return _fc_frag_response(active_sid=sid, n_months=n_months)


@bp.route("/scenarios/<sid>/update", methods=["POST"])
@login_required
def scenario_update(sid):
    f = request.form
    data = D.load_data()
    allocs = _parse_scenario_form(f, data)
    name = (f.get("name") or "Scenario").strip()[:40]
    n_months = _safe_n_months(f.get("n_months"))
    if not current_app.config.get("DEV_SEED"):
        DB.update_scenario(session["user_id"], session["access_token"], sid, name, allocs)
    return _fc_frag_response(active_sid=sid, n_months=n_months)


@bp.route("/scenarios/<sid>/delete", methods=["POST"])
@login_required
def scenario_delete(sid):
    f = request.form
    n_months = _safe_n_months(f.get("n_months"))
    if not current_app.config.get("DEV_SEED"):
        DB.delete_scenario(session["user_id"], session["access_token"], sid)
    return _fc_frag_response(active_sid="", n_months=n_months)


def _safe_n_months(raw) -> int:
    try:
        return max(1, min(12, int(raw or 3)))
    except (ValueError, TypeError):
        return 3


def _setup_panel():
    return render_panel("panels/setup.html", "setup", **D.setup_view())


def _dev_or(fn):
    if not current_app.config["DEV_SEED"]:
        fn(session["user_id"], session["access_token"])
        D.invalidate_cache()
    return _setup_panel()


@bp.route("/setup/paycheck", methods=["POST"])
@login_required
def add_paycheck():
    f = request.form
    amt = float(f.get("amount", "0").replace("$", "").replace(",", "") or 0)
    return _dev_or(lambda u, t: DB.insert_paycheck(
        u, t, f.get("label", "Paycheck"), amt, int(f.get("freq", 14)),
        f.get("anchor") or D.tx_form_ctx()["today"]))


@bp.route("/setup/paycheck/<pid>/delete", methods=["POST"])
@login_required
def del_paycheck(pid):
    return _dev_or(lambda u, t: DB.delete_paycheck(u, t, pid))


@bp.route("/setup/paycheck/<pid>/edit", methods=["POST"])
@login_required
def edit_paycheck(pid):
    f = request.form
    try:
        amt = round(float(f.get("amount", "0").replace("$", "").replace(",", "")), 2)
    except ValueError:
        amt = 0.0
    return _dev_or(lambda u, t: DB.update_paycheck(
        u, t, pid, f.get("label", "Paycheck"), amt,
        int(f.get("freq") or 14),
        f.get("anchor") or D.tx_form_ctx()["today"]))


@bp.route("/setup/category", methods=["POST"])
@login_required
def add_category():
    f = request.form
    return _dev_or(lambda u, t: DB.insert_category(
        u, t, f.get("name", "Category"), f.get("color") or "#818cf8"))


@bp.route("/setup/category/<cid>/edit", methods=["POST"])
@login_required
def edit_category(cid):
    f = request.form
    return _dev_or(lambda u, t: DB.update_category(
        u, t, cid, {"name": f.get("name", ""), "color": f.get("color", "#818cf8")}))


@bp.route("/setup/category/<cid>/delete", methods=["POST"])
@login_required
def del_category(cid):
    return _dev_or(lambda u, t: DB.update_category(u, t, cid, {"archived": True}))


@bp.route("/setup/category/<cid>/move/<direction>", methods=["POST"])
@login_required
def move_category(cid, direction):
    data = D.load_data()
    cats = sorted(data.get("cats", []), key=lambda c: c.get("order", 0))
    idx = next((i for i, c in enumerate(cats) if c["id"] == cid), -1)
    swap_idx = idx - 1 if direction == "up" else idx + 1
    if 0 <= idx < len(cats) and 0 <= swap_idx < len(cats):
        c1, c2 = cats[idx], cats[swap_idx]
        o1, o2 = c1.get("order", idx), c2.get("order", swap_idx)
        if not current_app.config["DEV_SEED"]:
            DB.update_category_order(session["user_id"], session["access_token"], c1["id"], o2)
            DB.update_category_order(session["user_id"], session["access_token"], c2["id"], o1)
            D.invalidate_cache()
    return _setup_panel()


def _rule_value_type(raw: str | None) -> str:
    """Normalize the rule form's value_type into one of: pct, fund, fixed."""
    if raw == "pct":
        return "pct"
    if raw == "fund":
        return "fund"
    return "fixed"


@bp.route("/setup/rule", methods=["POST"])
@login_required
def add_rule():
    f = request.form
    vtype = _rule_value_type(f.get("value_type"))
    val = 0.0 if vtype == "fund" else float(f.get("value", "0").replace("$", "").replace("%", "") or 0)
    rtype = "external" if f.get("rule_type") == "external" else "internal"
    return _dev_or(lambda u, t: DB.insert_alloc_rule(
        u, t, f.get("name", "Rule"), rtype, vtype, val, f.get("bucketId", "")))


@bp.route("/setup/rule/<rid>/edit", methods=["POST"])
@login_required
def edit_rule(rid):
    f = request.form
    vtype = _rule_value_type(f.get("value_type"))
    try:
        val = 0.0 if vtype == "fund" else float(f.get("value", "0").replace("$", "").replace("%", "") or 0)
    except ValueError:
        val = 0.0
    rtype = "external" if f.get("rule_type") == "external" else "internal"
    return _dev_or(lambda u, t: DB.update_alloc_rule(
        u, t, rid, f.get("name", "Rule"), rtype, vtype, val, f.get("bucketId", "")))


@bp.route("/setup/rule/<rid>/delete", methods=["POST"])
@login_required
def del_rule(rid):
    return _dev_or(lambda u, t: DB.delete_alloc_rule(u, t, rid))


@bp.route("/setup/rule/<rid>/toggle", methods=["POST"])
@login_required
def toggle_rule(rid):
    if not current_app.config["DEV_SEED"]:
        DB.toggle_alloc_rule(session["user_id"], session["access_token"], rid)
        D.invalidate_cache()
    return _setup_panel()


@bp.route("/transaction/<tid>/paycheck-distribute/preview", methods=["POST"])
@login_required
def paycheck_distribute_preview(tid):
    """Live recompute when a checkbox changes in the paycheck distribute modal."""
    tx = next((t for t in D.load_data().get("txs", []) if t.get("id") == tid), None)
    if not tx:
        return "", 404
    amount = float(tx.get("amount") or 0)
    mid = tx.get("monthId") or D.active_mid()
    f = request.form
    ctx = D.paycheck_distribute_ctx(
        amount, mid,
        checked_rule=set(f.getlist("rule")),
        checked_ob=set(f.getlist("ob")),
        checked_fund=set(f.getlist("fund")),
        checked_next=set(f.getlist("next_ob")),
    )
    return render_template("panels/_frag_paycheck_distribute.html", tid=tid, **ctx)


@bp.route("/transaction/<tid>/paycheck-distribute", methods=["POST"])
@login_required
def apply_paycheck_distribute(tid):
    """Apply the combined paycheck distribution (rules + obligations + catch-alls + next month)."""
    data = D.load_data()
    tx = next((t for t in data.get("txs", []) if t.get("id") == tid), None)
    if not tx:
        flash("Transaction not found.", "error")
        return redirect(url_for(".buckets"))
    amount = float(tx.get("amount") or 0)
    mid = tx.get("monthId") or D.active_mid()
    f = request.form
    # Recompute server-side — never trust client-submitted amounts
    ctx = D.paycheck_distribute_ctx(
        amount, mid,
        checked_rule=set(f.getlist("rule")),
        checked_ob=set(f.getlist("ob")),
        checked_fund=set(f.getlist("fund")),
        checked_next=set(f.getlist("next_ob")),
    )
    if not current_app.config["DEV_SEED"]:
        month = D.active_month(data, mid)
        next_mid = ctx["next_mid"]
        next_month = D.active_month(data, next_mid)
        for r in ctx["internal_rules"]:
            if r["checked"] and r["computed"] > 0:
                new_alloc = round(D.F.b_alloc(month, r["bucket_id"]) + r["computed"], 2)
                DB.upsert_alloc(session["user_id"], session["access_token"], mid, r["bucket_id"], new_alloc)
        for o in ctx["obligations"]:
            if o["checked"] and o["gap"] > 0:
                new_alloc = round(D.F.b_alloc(month, o["id"]) + o["gap"], 2)
                DB.upsert_alloc(session["user_id"], session["access_token"], mid, o["id"], new_alloc)
        for r in ctx["fund_rules"]:
            if r["checked"] and r["computed"] > 0:
                new_alloc = round(D.F.b_alloc(month, r["bucket_id"]) + r["computed"], 2)
                DB.upsert_alloc(session["user_id"], session["access_token"], mid, r["bucket_id"], new_alloc)
        for o in ctx["next_obligations"]:
            if o["checked"] and o["gap"] > 0:
                new_alloc = round(D.F.b_alloc(next_month, o["id"]) + o["gap"], 2)
                DB.upsert_alloc(session["user_id"], session["access_token"], next_mid, o["id"], new_alloc)
        D.invalidate_cache()
    flash(f"Distributed {ctx['total_applied']:,.2f}.", "ok")
    return _panel_close_modal(_bucket_template(), "buckets", **D.bucket_rows())




@bp.route("/transaction/<tid>/edit", methods=["GET", "POST"])
@login_required
def transaction_edit(tid):
    tx = D.tx_by_id(tid)
    if not tx:
        flash("Transaction not found.", "error")
        return redirect(url_for(".accounts"))
    if request.method == "POST":
        f = request.form
        try:
            amount = round(float(f.get("amount", "0").replace("$", "").replace(",", "")), 2)
        except ValueError:
            amount = 0.0
        iso = f.get("date") or D.tx_form_ctx()["today"]
        y, m, _ = (iso[:10].split("-") + ["1", "1", "1"])[:3]
        mid = D.F.month_id(int(y), int(m) - 1)
        if not current_app.config["DEV_SEED"]:
            DB.update_transaction(session["user_id"], session["access_token"], tid, {
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
            })
            D.invalidate_cache()
            flash("Transaction updated.", "ok")
        else:
            flash("Dev mode: change not persisted.", "ok")
        back_panel = f.get("back") or "accounts"
        if request.headers.get("HX-Request") == "true":
            tmpl, ctx_fn = _panel_lookup(back_panel)
            return _panel_close_modal(tmpl, back_panel, **ctx_fn())
        return redirect(url_for("." + back_panel))
    back = session.get("active_panel", "accounts")
    if _is_modal():
        return render_template("panels/_frag_edit_tx.html", tx=tx, back=back,
                               **D.tx_form_ctx())
    return render_panel("panels/edit_tx.html", back,
                        tx=tx, back=back, **D.tx_form_ctx())


@bp.route("/transaction/<tid>/delete", methods=["POST"])
@login_required
def transaction_delete(tid):
    back_panel = request.form.get("back") or "accounts"
    if not current_app.config["DEV_SEED"]:
        DB.delete_transaction(session["user_id"], session["access_token"], tid)
        D.invalidate_cache()
        flash("Transaction deleted.", "ok")
    else:
        flash("Dev mode: change not persisted.", "ok")
    if request.headers.get("HX-Request") == "true":
        tmpl, ctx_fn = _panel_lookup(back_panel)
        return _panel_close_modal(tmpl, back_panel, **ctx_fn())
    return redirect(url_for("." + back_panel))


@bp.route("/transaction/new")
@login_required
def transaction_new():
    tx_type = request.args.get("type", "out")
    back = session.get("active_panel", "buckets")
    if _is_modal():
        return render_template("panels/_frag_add_tx.html", tx_type=tx_type, back=back,
                               **D.tx_form_ctx())
    return render_panel("panels/add_tx.html", back, tx_type=tx_type, back=back,
                        **D.tx_form_ctx())


@bp.route("/transaction", methods=["POST"])
@login_required
def transaction_create():
    f = request.form
    try:
        amount = round(float(f.get("amount", "0").replace("$", "").replace(",", "")), 2)
    except ValueError:
        amount = 0.0
    iso = f.get("date") or D.tx_form_ctx()["today"]
    y, m, _ = (iso[:10].split("-") + ["1", "1", "1"])[:3]
    mid = D.F.month_id(int(y), int(m) - 1)
    tx = {
        "accountId": f.get("accountId", ""), "monthId": mid,
        "type": f.get("type", "out"), "amount": amount, "date": iso,
        "desc": f.get("desc", ""), "bucketId": f.get("bucketId") or "",
        "toAccountId": f.get("toAccountId") or "",
        "incomeType": f.get("incomeType") or "paycheck",
    }
    # Block vault buckets from receiving transactions
    bucket_id = tx.get("bucketId", "")
    if bucket_id:
        _bkt = next((b for b in D.load_data().get("buckets", []) if b["id"] == bucket_id), None)
        if _bkt and _bkt.get("type") == "vault":
            flash("Vault buckets cannot hold transactions. Use Transfer instead.", "error")
            back_panel = f.get("back") or session.get("active_panel", "buckets")
            if request.headers.get("HX-Request") == "true":
                tmpl, ctx_fn = _panel_lookup(back_panel)
                return _panel_close_modal(tmpl, back_panel, **ctx_fn())
            return redirect(url_for("." + back_panel))

    back_panel = f.get("back") or session.get("active_panel", "buckets")
    if current_app.config["DEV_SEED"]:
        flash("Dev mode: transaction not persisted (no database).", "ok")
    elif amount > 0 and tx["accountId"]:
        new_tid = DB.insert_transaction(session["user_id"], session["access_token"], tx)
        D.invalidate_cache()
        flash("Transaction added.", "ok")
        # After a paycheck, open the combined distribute modal
        if (tx["type"] == "in" and tx.get("incomeType") == "paycheck"
                and request.headers.get("HX-Request") == "true"):
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
    if request.headers.get("HX-Request") == "true":
        tmpl, ctx_fn = _panel_lookup(back_panel)
        return _panel_close_modal(tmpl, back_panel, **ctx_fn())
    return redirect(url_for("." + back_panel))


@bp.route("/month/<direction>")
@login_required
def month_nav(direction):
    y, m0 = D.F.parse_month_id(D.active_mid())
    total = y * 12 + m0 + (1 if direction == "next" else -1)
    session["active_mid"] = f"m_{total // 12}_{total % 12}"
    return redirect(url_for("." + session.get("active_panel", "buckets")))


@bp.route("/month/today")
@login_required
def month_today():
    """Jump the active month back to today's calendar month."""
    session["active_mid"] = D.F.current_month_id()
    return redirect(url_for("." + session.get("active_panel", "buckets")))


# ── Stub panels (built in later phases) ───────────────────────────────────────

def _stub(name, title):
    @login_required
    def view():
        return render_panel("panels/_stub.html", name, title=title)
    view.__name__ = name
    return view


# (all panels now have real routes)
