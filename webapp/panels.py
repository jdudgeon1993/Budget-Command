"""Panels — the dashboard shell + injected panel content.

Each panel route renders the same template two ways: full page on a hard load,
just the #panel fragment on an HTMX request (SPA-feel, no reload).
"""

from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, current_app, flash)

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
    # Find the freshly-computed row + its category color.
    vm = D.bucket_rows()
    row = color = None
    for grp in vm["groups"]:
        for b in grp["buckets"]:
            if b["id"] == bid:
                row, color = b, grp["color"]
    shell = D.shell_ctx("buckets")
    return (render_template("panels/_bucket_row.html", b=row, cat_color=color)
            + render_template("panels/_oob_rts.html", shell=shell))


# ── Month navigation ──────────────────────────────────────────────────────────

@bp.route("/accounts")
@login_required
def accounts():
    return render_panel("panels/accounts.html", "accounts", **D.accounts_view())


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


@bp.route("/transaction/new")
@login_required
def transaction_new():
    tx_type = request.args.get("type", "out")
    back = session.get("active_panel", "buckets")
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
    return redirect(url_for("panels." + (f.get("back") or "buckets")))


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
