"""Panels — the dashboard shell + injected panel content.

Each panel route renders the same template two ways: full page on a hard load,
just the #panel fragment on an HTMX request (SPA-feel, no reload).
"""

from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, current_app)

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


for _name, _title in [("accounts", "Accounts"), ("insights", "Forecast"),
                      ("reports", "Reports"), ("setup", "Setup")]:
    bp.add_url_rule(f"/{_name}", endpoint=_name, view_func=_stub(_name, _title))
