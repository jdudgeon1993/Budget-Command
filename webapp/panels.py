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
    """Full page on normal load, bare fragment on HTMX request."""
    session["active_panel"] = active_panel
    htmx = request.headers.get("HX-Request") == "true"
    layout = "_partial.html" if htmx else "base.html"
    return render_template(template, layout=layout,
                           shell=D.shell_ctx(active_panel), **ctx)


@bp.route("/")
def index():
    return redirect(url_for("panels.buckets"))


@bp.route("/dashboard")
@login_required
def dashboard():
    return redirect(url_for("panels.buckets"))


# ── Buckets ───────────────────────────────────────────────────────────────────

@bp.route("/buckets")
@login_required
def buckets():
    return render_panel("panels/buckets.html", "buckets", **D.bucket_rows())


@bp.route("/buckets/<bid>/alloc", methods=["POST"])
@login_required
def set_alloc(bid):
    """Inline allocation edit -> returns the updated row + OOB shell refresh."""
    try:
        amount = round(float(request.form.get("alloc", "0").replace("$", "").replace(",", "")), 2)
    except ValueError:
        amount = 0.0
    data = D.load_data()
    month = D.active_month(data)
    month.setdefault("allocations", {})[bid] = amount
    if not current_app.config["DEV_SEED"]:
        DB.upsert_alloc(session["user_id"], session["access_token"],
                        D.active_mid(), bid, amount)
    # No-JS fallback: a plain form submit (Enter) reloads the panel.
    if request.headers.get("HX-Request") != "true":
        return redirect(url_for("panels.buckets"))
    # HTMX: swap just the row + out-of-band Ready-to-Assign.
    vm = D.bucket_rows()
    row = color = None
    for grp in vm["groups"]:
        for b in grp["buckets"]:
            if b["id"] == bid:
                row, color = b, grp["color"]
    shell = D.shell_ctx("buckets")
    return (render_template("panels/_bucket_row.html", b=row, cat_color=color)
            + render_template("panels/_oob_rts.html", shell=shell))


# ── Bucket fill / distribute ─────────────────────────────────────────────────

@bp.route("/buckets/<bid>/fill", methods=["POST"])
@login_required
def fill_bucket(bid):
    """Set allocation = budget for this bucket."""
    data = D.load_data()
    month = D.active_month(data)
    budget = D.F.b_budget(month, bid)
    month.setdefault("allocations", {})[bid] = budget
    if not current_app.config["DEV_SEED"]:
        DB.upsert_alloc(session["user_id"], session["access_token"],
                        D.active_mid(), bid, budget)
    flash(f"Filled.", "ok")
    return _buckets_response()


@bp.route("/buckets/distribute", methods=["POST"])
@login_required
def distribute_rts():
    """Spread remaining RTS evenly across underfunded buckets."""
    data = D.load_data()
    month = D.active_month(data)
    months = data.get("months", [])
    accounts = data.get("accounts", [])
    buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    txs = data.get("txs", [])

    rts = D.F.ready_to_spend(month, months, accounts, buckets, txs)
    if rts <= 0:
        return _buckets_response()

    underfunded = []
    for b in buckets:
        alloc = D.F.b_alloc(month, b["id"])
        budget = D.F.b_budget(month, b["id"])
        if budget > alloc:
            underfunded.append((b["id"], budget - alloc))

    if underfunded:
        per_bucket = min(rts / len(underfunded), max(n for _, n in underfunded))
        for bid, needed in underfunded:
            add = min(per_bucket, needed)
            new_alloc = D.F.b_alloc(month, bid) + add
            month.setdefault("allocations", {})[bid] = new_alloc
            if not current_app.config["DEV_SEED"]:
                DB.upsert_alloc(session["user_id"], session["access_token"],
                                D.active_mid(), bid, new_alloc)
    flash("RTS distributed.", "ok")
    return _buckets_response()


def _buckets_response():
    """Return buckets panel for HTMX or redirect for plain requests."""
    if request.headers.get("HX-Request") == "true":
        return render_panel("panels/buckets.html", "buckets", **D.bucket_rows())
    return redirect(url_for("panels.buckets"))


def _is_modal():
    return request.headers.get("HX-Target") == "modal-body"


def _panel_close_modal(panel_tmpl, active_panel, **ctx):
    """Return panel HTML + HX-Trigger:closeModal for HTMX form submits inside modals."""
    resp = make_response(render_panel(panel_tmpl, active_panel, **ctx))
    resp.headers["HX-Trigger"] = "closeModal"
    return resp


_PANEL_MAP = {
    "accounts": ("panels/accounts.html", lambda: D.accounts_view()),
    "buckets":  ("panels/buckets.html",  lambda: D.bucket_rows()),
    "reports":  ("panels/reports.html",  lambda: D.reports_view()),
    "setup":    ("panels/setup.html",    lambda: D.setup_view()),
}


# ── Bucket settings ───────────────────────────────────────────────────────────

@bp.route("/buckets/<bid>/settings", methods=["GET", "POST"])
@login_required
def bucket_settings(bid):
    data = D.load_data()
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bid), None)
    if not bucket:
        flash("Bucket not found.", "error")
        return redirect(url_for("panels.buckets"))
    cats = data.get("cats", [])
    if request.method == "POST":
        f = request.form
        def _num(key, default=0.0):
            try:
                return round(float((f.get(key) or "0").replace("$", "").replace(",", "")), 2)
            except ValueError:
                return default
        if not current_app.config["DEV_SEED"]:
            DB.upsert_bucket(session["user_id"], session["access_token"], bid, {
                "name": f.get("name", bucket["name"]).strip(),
                "cat_id": f.get("catId", bucket.get("catId", "")),
                "type": f.get("type", bucket.get("type", "expense")),
                "default_budget": _num("default_budget"),
                "rollover": f.get("rollover") == "1",
                "notes": f.get("notes", ""),
                "due_day": (f.get("due_day") or "").strip() or None,
                "due_amount": _num("due_amount"),
                "pay_freq": f.get("pay_freq") or None,
                "target_amount": _num("target_amount"),
                "target_date": f.get("target_date") or None,
                "contrib_freq": f.get("contrib_freq") or None,
                "recurring": f.get("recurring") == "1",
            })
            flash("Bucket updated.", "ok")
        else:
            flash("Dev mode: change not persisted.", "ok")
        if request.headers.get("HX-Request") == "true":
            return _panel_close_modal("panels/buckets.html", "buckets", **D.bucket_rows())
        return redirect(url_for("panels.buckets"))
    data_ctx = D.load_data()
    debt_accounts = [{"id": a["id"], "name": a["name"]}
                     for a in data_ctx.get("accounts", [])
                     if a.get("type") == "debt" and not a.get("archived")]
    if _is_modal():
        return render_template("panels/_frag_bucket.html", bucket=bucket, cats=cats,
                               debt_accounts=debt_accounts)
    return render_panel("panels/edit_bucket.html", "buckets",
                        bucket=bucket, cats=cats, debt_accounts=debt_accounts)


@bp.route("/buckets/<bid>/archive", methods=["POST"])
@login_required
def archive_bucket(bid):
    if not current_app.config["DEV_SEED"]:
        DB.upsert_bucket(session["user_id"], session["access_token"], bid, {"archived": True})
        flash("Bucket archived.", "ok")
    else:
        flash("Dev mode: change not persisted.", "ok")
    if request.headers.get("HX-Request") == "true":
        return _panel_close_modal("panels/buckets.html", "buckets", **D.bucket_rows())
    return redirect(url_for("panels.buckets"))


@bp.route("/buckets/<bid>/vault-transfer", methods=["GET", "POST"])
@login_required
def vault_transfer(bid):
    data = D.load_data()
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bid), None)
    if not bucket or bucket.get("type") != "vault":
        return redirect(url_for("panels.buckets"))
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
            new_from = max(0.0, round(from_alloc - amount, 2))
            new_to = round(to_alloc + amount, 2)
            if not current_app.config["DEV_SEED"]:
                DB.vault_transfer(session["user_id"], session["access_token"],
                                  mid, bid, to_bid, amount, new_from, new_to)
                flash(f"Transferred ${amount:,.2f} from vault.", "ok")
            else:
                flash("Dev mode: transfer not persisted.", "ok")
        if request.headers.get("HX-Request") == "true":
            return _panel_close_modal("panels/buckets.html", "buckets", **D.bucket_rows())
        return redirect(url_for("panels.buckets"))
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
        return redirect(url_for("panels.buckets"))
    if request.method == "POST":
        f = request.form
        try:
            amount = round(float(f.get("amount", "0").replace("$", "").replace(",", "")), 2)
        except ValueError:
            amount = 0.0
        if amount > 0:
            month = D.active_month(data)
            mid = D.active_mid()
            current_alloc = D.F.b_alloc(month, bid)
            if not current_app.config["DEV_SEED"]:
                DB.vault_release_to_pool(session["user_id"], session["access_token"],
                                         mid, bid, amount, current_alloc)
                flash(f"Released ${amount:,.2f} from vault to pool.", "ok")
            else:
                flash("Dev mode: release not persisted.", "ok")
        if request.headers.get("HX-Request") == "true":
            return _panel_close_modal("panels/buckets.html", "buckets", **D.bucket_rows())
        return redirect(url_for("panels.buckets"))
    # GET — render release form in modal
    month = D.active_month(data)
    vault_alloc = D.F.b_alloc(month, bid)
    vault_accum = D.F.vault_accumulated(bid, data.get("months", []))
    return render_template("panels/_frag_vault_release.html",
                           bucket=bucket, vault_alloc=vault_alloc, vault_accum=vault_accum)


# ── Budget inline edit ───────────────────────────────────────────────────────

@bp.route("/buckets/<bid>/budget", methods=["POST"])
@login_required
def set_budget(bid):
    try:
        amount = round(float(request.form.get("budget", "0").replace("$", "").replace(",", "")), 2)
    except ValueError:
        amount = 0.0
    data = D.load_data()
    month = D.active_month(data)
    month.setdefault("budgets", {})[bid] = amount
    if not current_app.config["DEV_SEED"]:
        DB.upsert_budget(session["user_id"], session["access_token"],
                         D.active_mid(), bid, amount)
    if request.headers.get("HX-Request") != "true":
        return redirect(url_for("panels.buckets"))
    vm = D.bucket_rows()
    row = color = None
    for grp in vm["groups"]:
        for b in grp["buckets"]:
            if b["id"] == bid:
                row, color = b, grp["color"]
    shell = D.shell_ctx("buckets")
    return (render_template("panels/_bucket_row.html", b=row, cat_color=color)
            + render_template("panels/_oob_rts.html", shell=shell))


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
        flash("Bucket added.", "ok")
    elif current_app.config["DEV_SEED"]:
        flash("Dev mode: bucket not persisted.", "ok")
    else:
        flash("Name and category are required.", "error")
    return _buckets_response()


# ── Bucket reorder ────────────────────────────────────────────────────────────

@bp.route("/buckets/<bid>/move/<direction>", methods=["POST"])
@login_required
def move_bucket(bid, direction):
    data = D.load_data()
    buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    this_b = next((b for b in buckets if b["id"] == bid), None)
    if not this_b:
        return redirect(url_for("panels.buckets"))
    siblings = sorted(
        [b for b in buckets if b.get("catId") == this_b.get("catId")],
        key=lambda b: b.get("order", 0)
    )
    idx = next((i for i, b in enumerate(siblings) if b["id"] == bid), -1)
    swap_idx = idx - 1 if direction == "up" else idx + 1
    if 0 <= idx < len(siblings) and 0 <= swap_idx < len(siblings):
        b1, b2 = siblings[idx], siblings[swap_idx]
        o1 = b1.get("order", idx)
        o2 = b2.get("order", swap_idx)
        if not current_app.config["DEV_SEED"]:
            DB.update_bucket_order(session["user_id"], session["access_token"], b1["id"], o2)
            DB.update_bucket_order(session["user_id"], session["access_token"], b2["id"], o1)
    return _buckets_response()


# ── Month workflow ────────────────────────────────────────────────────────────

@bp.route("/month/copy", methods=["POST"])
@login_required
def month_copy():
    mid = D.active_mid()
    y, m0 = D.F.parse_month_id(mid)
    total = y * 12 + m0 - 1
    prev_mid = f"m_{total // 12}_{total % 12}"
    if not current_app.config["DEV_SEED"]:
        DB.copy_month_allocs(session["user_id"], session["access_token"], mid, prev_mid)
        flash("Allocations copied from last month.", "ok")
    else:
        flash("Dev mode: copy not persisted.", "ok")
    return _buckets_response()


@bp.route("/month/close", methods=["POST"])
@login_required
def month_close():
    data = D.load_data()
    if not current_app.config["DEV_SEED"]:
        DB.close_month(session["user_id"], session["access_token"],
                       D.active_mid(), data.get("accounts", []), data.get("txs", []))
        flash("Month closed.", "ok")
    else:
        flash("Dev mode: close not persisted.", "ok")
    return _buckets_response()


@bp.route("/month/reopen", methods=["POST"])
@login_required
def month_reopen():
    if not current_app.config["DEV_SEED"]:
        DB.reopen_month(session["user_id"], session["access_token"], D.active_mid())
        flash("Month reopened.", "ok")
    else:
        flash("Dev mode: reopen not persisted.", "ok")
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
            flash("Account added.", "ok")
        elif current_app.config["DEV_SEED"]:
            flash("Dev mode: account not persisted.", "ok")
        else:
            flash("Name is required.", "error")
        if request.headers.get("HX-Request") == "true":
            return _panel_close_modal("panels/accounts.html", "accounts", **D.accounts_view())
        return redirect(url_for("panels.accounts"))
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
        return redirect(url_for("panels.accounts"))
    if request.method == "POST":
        f = request.form
        try:
            ob = round(float(f.get("opening_balance", "0").replace("$", "").replace(",", "")), 2)
        except ValueError:
            ob = 0.0
        if not current_app.config["DEV_SEED"]:
            DB.update_account(session["user_id"], session["access_token"], aid, {
                "name": f.get("name", "").strip(),
                "type": f.get("type", "budget"),
                "color": f.get("color", "#818cf8"),
                "opening_balance": ob,
            })
            flash("Account updated.", "ok")
        else:
            flash("Dev mode: change not persisted.", "ok")
        if request.headers.get("HX-Request") == "true":
            return _panel_close_modal("panels/accounts.html", "accounts", **D.accounts_view())
        return redirect(url_for("panels.accounts"))
    if _is_modal():
        return render_template("panels/_frag_account.html", account=account)
    return render_panel("panels/edit_account.html", "accounts", account=account)


@bp.route("/accounts/<aid>/archive", methods=["POST"])
@login_required
def account_archive(aid):
    if not current_app.config["DEV_SEED"]:
        DB.update_account(session["user_id"], session["access_token"], aid, {"archived": True})
        flash("Account archived.", "ok")
    else:
        flash("Dev mode: change not persisted.", "ok")
    if request.headers.get("HX-Request") == "true":
        return _panel_close_modal("panels/accounts.html", "accounts", **D.accounts_view())
    return redirect(url_for("panels.accounts"))


@bp.route("/reports")
@login_required
def reports():
    return render_panel("panels/reports.html", "reports", **D.reports_view())


@bp.route("/setup")
@login_required
def setup():
    return render_panel("panels/setup.html", "setup", **D.setup_view())


@bp.route("/insights")
@login_required
def insights():
    return render_panel("panels/forecast.html", "insights")


def _dev_or(fn):
    """Run a db mutation, or flash a dev-mode note when seeding."""
    if current_app.config["DEV_SEED"]:
        flash("Dev mode: change not persisted (no database).", "ok")
    else:
        fn(session["user_id"], session["access_token"])
        flash("Saved.", "ok")
    return redirect(url_for("panels.setup"))


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


@bp.route("/setup/category", methods=["POST"])
@login_required
def add_category():
    f = request.form
    return _dev_or(lambda u, t: DB.insert_category(
        u, t, f.get("name", "Category"), f.get("color") or "#818cf8"))


@bp.route("/setup/rule", methods=["POST"])
@login_required
def add_rule():
    f = request.form
    val = float(f.get("value", "0").replace("$", "").replace("%", "") or 0)
    vtype = "pct" if f.get("value_type") == "pct" else "fixed"
    return _dev_or(lambda u, t: DB.insert_alloc_rule(
        u, t, f.get("name", "Rule"), "internal", vtype, val, f.get("bucketId", "")))


@bp.route("/setup/rule/<rid>/delete", methods=["POST"])
@login_required
def del_rule(rid):
    return _dev_or(lambda u, t: DB.delete_alloc_rule(u, t, rid))


@bp.route("/setup/paycheck/<pid>/edit", methods=["POST"])
@login_required
def edit_paycheck(pid):
    f = request.form
    try:
        amt = round(float(f.get("amount", "0").replace("$", "").replace(",", "")), 2)
    except ValueError:
        amt = 0.0
    if not current_app.config["DEV_SEED"]:
        DB.update_paycheck(session["user_id"], session["access_token"],
                           pid, f.get("label", "Paycheck"), amt,
                           int(f.get("freq") or 14),
                           f.get("anchor") or D.tx_form_ctx()["today"])
        flash("Paycheck updated.", "ok")
    else:
        flash("Dev mode: change not persisted.", "ok")
    return redirect(url_for("panels.setup"))


@bp.route("/setup/category/<cid>/edit", methods=["POST"])
@login_required
def edit_category(cid):
    f = request.form
    if not current_app.config["DEV_SEED"]:
        DB.update_category(session["user_id"], session["access_token"], cid,
                           {"name": f.get("name", ""), "color": f.get("color", "#818cf8")})
        flash("Category updated.", "ok")
    else:
        flash("Dev mode: change not persisted.", "ok")
    return redirect(url_for("panels.setup"))


@bp.route("/setup/category/<cid>/delete", methods=["POST"])
@login_required
def del_category(cid):
    if not current_app.config["DEV_SEED"]:
        DB.update_category(session["user_id"], session["access_token"], cid, {"archived": True})
        flash("Category archived.", "ok")
    else:
        flash("Dev mode: change not persisted.", "ok")
    return redirect(url_for("panels.setup"))


@bp.route("/setup/rule/<rid>/toggle", methods=["POST"])
@login_required
def toggle_rule(rid):
    if not current_app.config["DEV_SEED"]:
        DB.toggle_alloc_rule(session["user_id"], session["access_token"], rid)
    return redirect(url_for("panels.setup"))


# ── Forecast builder (iframe with real data) ──────────────────────────────────

@bp.route("/forecast/builder")
@login_required
def forecast_builder():
    import os, json as _json
    live_data = D.forecast_data_ctx()
    proto_path = os.path.join(current_app.static_folder, "forecast-proto.html")
    with open(proto_path, "r") as fh:
        content = fh.read()
    injection = f'<script>window.CURA_LIVE = {_json.dumps(live_data)};</script>\n'
    content = content.replace("</head>", injection + "</head>", 1)
    return Response(content, content_type="text/html")


@bp.route("/api/forecast-data")
@login_required
def forecast_data_api():
    return jsonify(D.forecast_data_ctx())


@bp.route("/transaction/<tid>/edit", methods=["GET", "POST"])
@login_required
def transaction_edit(tid):
    tx = D.tx_by_id(tid)
    if not tx:
        flash("Transaction not found.", "error")
        return redirect(url_for("panels.accounts"))
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
            })
            flash("Transaction updated.", "ok")
        else:
            flash("Dev mode: change not persisted.", "ok")
        back_panel = f.get("back") or "accounts"
        if request.headers.get("HX-Request") == "true":
            tmpl, ctx_fn = _PANEL_MAP.get(back_panel, _PANEL_MAP["accounts"])
            return _panel_close_modal(tmpl, back_panel, **ctx_fn())
        return redirect(url_for("panels." + back_panel))
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
        flash("Transaction deleted.", "ok")
    else:
        flash("Dev mode: change not persisted.", "ok")
    if request.headers.get("HX-Request") == "true":
        tmpl, ctx_fn = _PANEL_MAP.get(back_panel, _PANEL_MAP["accounts"])
        return _panel_close_modal(tmpl, back_panel, **ctx_fn())
    return redirect(url_for("panels." + back_panel))


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
    }
    if current_app.config["DEV_SEED"]:
        flash("Dev mode: transaction not persisted (no database).", "ok")
    elif amount > 0 and tx["accountId"]:
        DB.insert_transaction(session["user_id"], session["access_token"], tx)
        flash("Transaction added.", "ok")
    else:
        flash("Amount and account are required.", "error")
    back_panel = f.get("back") or "buckets"
    if request.headers.get("HX-Request") == "true":
        tmpl, ctx_fn = _PANEL_MAP.get(back_panel, _PANEL_MAP["accounts"])
        return _panel_close_modal(tmpl, back_panel, **ctx_fn())
    return redirect(url_for("panels." + back_panel))


@bp.route("/month/<direction>")
@login_required
def month_nav(direction):
    y, m0 = D.F.parse_month_id(D.active_mid())
    total = y * 12 + m0 + (1 if direction == "next" else -1)
    session["active_mid"] = f"m_{total // 12}_{total % 12}"
    return redirect(url_for("panels." + session.get("active_panel", "buckets")))


# ── Stub panels (built in later phases) ───────────────────────────────────────

def _stub(name, title):
    @login_required
    def view():
        return render_panel("panels/_stub.html", name, title=title)
    view.__name__ = name
    return view


# (all panels now have real routes)
