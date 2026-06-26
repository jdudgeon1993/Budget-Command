"""Panels — the dashboard shell + injected panel content.

Each panel route renders the same template two ways: full page on a hard load,
just the #panel fragment on an HTMX request (SPA-feel, no reload).
"""

from flask import (Blueprint, render_template, request, redirect, url_for,
                   session, current_app, flash, jsonify, Response, make_response)

from . import db as DB
from . import data as D
from . import actions as A
from .auth import login_required, quick_required

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
    view_mid = request.args.get("m") or None
    return render_panel("panels/buckets.html", "buckets", **D.bucket_rows(view_mid=view_mid))


@bp.route("/buckets/faq")
@login_required
def buckets_faq():
    return render_panel("panels/buckets_faq.html", "buckets")


# ── Bucket fill / distribute ─────────────────────────────────────────────────

def _distribute_checks():
    """Checkbox state from the Distribute form, or None for the un-submitted default."""
    if "submitted" not in request.form:
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


def _buckets_response():
    """Return buckets panel for HTMX or redirect for plain requests."""
    if request.headers.get("HX-Request") == "true":
        return render_panel("panels/buckets.html", "buckets", **D.bucket_rows())
    return redirect(url_for("panels.buckets"))


def _is_modal():
    target = request.headers.get("HX-Target", "")
    return (target == "modal-body" or target.startswith("bkt-settings-")
            or target.startswith("tx-edit-") or target.startswith("acct-settings-"))


def _panel_close_modal(panel_tmpl, active_panel, **ctx):
    """Return panel HTML + HX-Trigger:closeModal for HTMX form submits inside modals."""
    resp = make_response(render_panel(panel_tmpl, active_panel, **ctx))
    resp.headers["HX-Trigger"] = "closeModal"
    return resp


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
            return D.parse_amount(f.get(key), default)
        if not current_app.config["DEV_SEED"]:
            btype = f.get("type", bucket.get("type", "expense"))
            payload = {
                "name": f.get("name", bucket["name"]).strip(),
                "cat_id": f.get("catId", bucket.get("catId", "")),
                "type": btype,
                "default_budget": _num("default_budget"),
                "notes": f.get("notes", ""),
            }
            if btype == "expense":
                payload.update({
                    "due_day": (f.get("due_day") or "").strip() or None,
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
            elif btype == "vault":
                payload.update({
                    "vault_locked": f.get("vault_locked") == "1",
                    "vault_paused": f.get("vault_paused") == "1",
                })
            DB.upsert_bucket(session["user_id"], session["access_token"], bid, payload)
            D.invalidate_cache()
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


@bp.route("/buckets/<bid>/vault-transfer", methods=["GET"])
@login_required
def vault_transfer(bid):
    data = D.load_data()
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bid), None)
    if not bucket or bucket.get("type") != "vault":
        return redirect(url_for("panels.buckets"))
    if bucket.get("locked"):
        flash("This vault is locked — unlock it first.", "error")
        return redirect(url_for("panels.buckets"))
    all_buckets = data.get("buckets", [])
    dest_non_vault = [b for b in all_buckets
                      if not b.get("archived") and b.get("type") != "vault"]
    dest_vaults = [b for b in all_buckets
                   if not b.get("archived") and b.get("type") == "vault" and b["id"] != bid]
    cats = sorted(data.get("cats", []), key=lambda c: c.get("order", 0))
    month = D.active_month(data)
    vault_alloc = D.F.b_alloc(month, bid)
    vault_accum = D.F.vault_accumulated(bid, data.get("months", []))
    dest_by_cat = []
    for c in cats:
        bkts = [b for b in dest_non_vault if b.get("catId") == c["id"]]
        if bkts:
            dest_by_cat.append({"cat": c["name"], "buckets": bkts})
    return render_template("panels/_frag_vault_transfer.html",
                           bucket=bucket, dest_by_cat=dest_by_cat,
                           dest_vaults=dest_vaults,
                           vault_alloc=vault_alloc, vault_accum=vault_accum)


@bp.route("/buckets/<bid>/vault-ledger", methods=["GET"])
@login_required
def vault_ledger(bid):
    data = D.load_data()
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bid), None)
    if not bucket or bucket.get("type") != "vault":
        return redirect(url_for("panels.buckets"))
    months = data.get("months", [])
    from .formulas import parse_month_id
    import calendar as _cal
    month_history = []
    for m in sorted(months, key=lambda x: parse_month_id(x["id"]), reverse=True):
        alloc = float((m.get("allocations") or {}).get(bid) or 0)
        wd = float((m.get("vaultWithdrawals") or {}).get(bid) or 0)
        if alloc > 0 or wd > 0:
            y, m0 = parse_month_id(m["id"])
            label = f"{_cal.month_name[m0 + 1]} {y}"
            net = round(alloc - wd, 2)
            month_history.append({
                "label": label, "alloc": alloc, "alloc_fmt": f"${alloc:,.2f}",
                "withdrawal": wd, "withdrawal_fmt": f"${wd:,.2f}" if wd > 0 else "—",
                "net": net, "net_fmt": f"${net:,.2f}",
            })
    history = DB.fetch_vault_history(session.get("user_id"), session.get("access_token"), bid)
    vault_accum = D.F.vault_accumulated(bid, months)
    return render_template("panels/_frag_vault_ledger.html",
                           bucket=bucket, month_history=month_history,
                           transfers=history.get("transfers", []),
                           releases=history.get("releases", []),
                           vault_accum=vault_accum)


@bp.route("/vaults/bulk-rebalance", methods=["GET"])
@login_required
def vault_bulk_rebalance_open():
    data = D.load_data()
    month = D.active_month(data)
    months = data.get("months", [])
    vault_buckets = sorted(
        [b for b in data.get("buckets", []) if b.get("type") == "vault" and not b.get("archived")],
        key=lambda b: b.get("order", 0),
    )
    vaults = []
    for b in vault_buckets:
        bid = b["id"]
        alloc = D.F.b_alloc(month, bid)
        accum = D.F.vault_accumulated(bid, months)
        streak = D.F.vault_streak(bid, months)
        vaults.append({
            "id": bid, "name": b["name"],
            "alloc": alloc, "alloc_fmt": f"{alloc:.2f}",
            "accum": accum, "accum_fmt": f"${accum:,.2f}",
            "streak": streak,
            "locked": b.get("locked", False),
            "paused": b.get("paused", False),
        })
    return render_template("panels/_frag_vault_bulk_rebalance.html", vaults=vaults)


@bp.route("/buckets/<bid>/vault-release", methods=["GET"])
@login_required
def vault_release_to_pool(bid):
    data = D.load_data()
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bid), None)
    if not bucket or bucket.get("type") != "vault":
        return redirect(url_for("panels.buckets"))
    # GET — render release form in modal
    month = D.active_month(data)
    vault_alloc = D.F.b_alloc(month, bid)
    vault_accum = D.F.vault_accumulated(bid, data.get("months", []))
    return render_template("panels/_frag_vault_release.html",
                           bucket=bucket, vault_alloc=vault_alloc, vault_accum=vault_accum)


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


@bp.route("/accounts/month/<direction>")
@login_required
def accounts_month_nav(direction):
    if direction not in ("next", "prev"):
        return redirect(url_for("panels.accounts"))
    from .formulas import parse_month_id
    y, m0 = parse_month_id(D.acct_mid())
    total = y * 12 + m0 + (1 if direction == "next" else -1)
    session["acct_mid"] = f"m_{total // 12}_{total % 12}"
    return redirect(url_for("panels.accounts"))


@bp.route("/accounts/month/today")
@login_required
def accounts_month_today():
    session.pop("acct_mid", None)
    return redirect(url_for("panels.accounts"))


# ── Add / edit account ────────────────────────────────────────────────────────

@bp.route("/accounts/new", methods=["GET", "POST"])
@login_required
def account_new():
    if request.method == "POST":
        f = request.form
        ob = D.parse_amount(f.get("opening_balance", "0"))
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
        ob = D.parse_amount(f.get("opening_balance", "0"))
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
        return redirect(url_for("panels.accounts"))
    if _is_modal():
        return render_template("panels/_frag_account.html", account=account)
    return render_panel("panels/edit_account.html", "accounts", account=account)


@bp.route("/accounts/<aid>/pay", methods=["GET", "POST"])
@login_required
def debt_payment(aid):
    data = D.load_data()
    account = next((a for a in data.get("accounts", []) if a["id"] == aid), None)
    if not account or account.get("type") != "debt":
        return redirect(url_for("panels.accounts"))
    if request.method == "POST":
        f = request.form
        amount = D.parse_amount(f.get("amount", "0"))
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
        return redirect(url_for("panels.accounts"))
    # GET — render payment form
    from_accounts = [{"id": a["id"], "name": a["name"]}
                     for a in data.get("accounts", [])
                     if a.get("type") != "debt" and not a.get("archived")]
    from datetime import date as _date
    return render_template("panels/_frag_debt_payment.html",
                           account=account, from_accounts=from_accounts,
                           today=_date.today().isoformat())


@bp.route("/debt-planner")
@login_required
def debt_planner():
    data = D.load_data()
    txs = data.get("txs", [])
    debts = []
    for a in data.get("accounts", []):
        if a.get("archived") or a.get("type") != "debt":
            continue
        if not a.get("debtAPR"):
            continue
        bal = abs(D.F.acct_balance(a, txs))
        if bal <= 0.005:
            continue
        debts.append({
            "id": a["id"], "name": a["name"], "balance": round(bal, 2),
            "apr": a.get("debtAPR") or 0,
            "min_payment": a.get("debtMinPayment") or 0,
        })
    return render_template("panels/_frag_debt_planner.html", debts=debts)


@bp.route("/accounts/<aid>/payoff")
@login_required
def debt_payoff(aid):
    data = D.load_data()
    account = next((a for a in data.get("accounts", []) if a["id"] == aid), None)
    if not account or account.get("type") != "debt":
        return redirect(url_for("panels.accounts"))
    balance = abs(D.F.acct_balance(account, data.get("txs", [])))
    return render_template("panels/_frag_debt_tracker.html",
                           account=account, balance=balance)


@bp.route("/accounts/<aid>/interest", methods=["GET", "POST"])
@login_required
def post_interest(aid):
    data = D.load_data()
    account = next((a for a in data.get("accounts", []) if a["id"] == aid), None)
    if not account or account.get("type") != "debt":
        return redirect(url_for("panels.accounts"))
    if request.method == "POST":
        f = request.form
        amount = D.parse_amount(f.get("amount", "0"))
        desc = f.get("desc", "").strip() or "Interest charge"
        pay_date = f.get("date") or D.tx_form_ctx()["today"]
        if amount > 0:
            if not current_app.config["DEV_SEED"]:
                DB.insert_transaction(session["user_id"], session["access_token"], {
                    "accountId": aid, "type": "out", "amount": amount,
                    "desc": desc, "date": pay_date, "monthId": D.active_mid(),
                })
                D.invalidate_cache()
            flash("Interest posted.", "ok")
        else:
            flash("Enter an amount greater than zero.", "error")
        if request.headers.get("HX-Request") == "true":
            return _panel_close_modal("panels/accounts.html", "accounts", **D.accounts_view())
        return redirect(url_for("panels.accounts"))
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


@bp.route("/forecast/move-suggestions")
@login_required
def forecast_move_suggestions():
    try:
        amount = float(request.args.get("amount", 0))
    except (ValueError, TypeError):
        amount = 0.0
    ctx = D.forecast_move_suggestions(amount)
    return render_template("panels/_frag_forecast_move_suggestions.html", **ctx)


@bp.route("/forecast/whatif", methods=["POST"])
@login_required
def forecast_whatif():
    f = request.form
    try:
        n_months = max(1, min(12, int(f.get("n_months", 1))))
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
    bucket_overrides, off_buckets, schedule, phantom_monthly, sc_pc_overrides = \
        _scenario_fc_params(scenarios, active_sid, n_months, data)

    # Per-paycheck income overrides from the What-If form (ad-hoc, not saved)
    form_pc_overrides = {}
    for pc in data.get("paychecks", []):
        pc_id = str(pc.get("id", ""))
        raw = (f.get(f"paycheck_override_{pc_id}") or "").replace("$", "").replace(",", "").strip()
        if raw:
            try:
                form_pc_overrides[pc_id] = float(raw)
            except ValueError:
                pass
    # Form overrides take precedence over scenario overrides
    paycheck_overrides = {**(sc_pc_overrides or {}), **form_pc_overrides} or None

    paychecks_ctx = [{"id": str(pc.get("id", "")), "label": pc.get("label", "Paycheck"),
                      "amount": float(pc.get("amount") or 0)}
                     for pc in data.get("paychecks", [])]

    from . import forecast_calc as FC
    fc = FC.compute_forecast(data, n_months=n_months, income_override=income_override,
                             skipped_pay_dates=skip_dates,
                             no_accrue_dates=no_accrue_dates,
                             bucket_overrides=bucket_overrides,
                             off_buckets=off_buckets,
                             schedule=schedule,
                             phantom_monthly=phantom_monthly,
                             paycheck_overrides=paycheck_overrides)
    svg = FC.build_balance_svg(fc["periods"])
    cal_data = FC.compute_calendar_data(data, 60, off_buckets=off_buckets)
    whatif_html = render_template("panels/_frag_forecast_whatif.html",
                                  forecast=fc, balance_svg=svg,
                                  n_months=n_months, income_override=income_override,
                                  skipped_pay_dates=skip_dates,
                                  skip_dates_str=",".join(skip_dates),
                                  no_accrue_dates=no_accrue_dates,
                                  no_accrue_dates_str=",".join(no_accrue_dates),
                                  scenarios=scenarios,
                                  active_scenario_id=active_sid,
                                  paychecks=paychecks_ctx,
                                  paycheck_overrides_form=form_pc_overrides,
                                  is_htmx=True)
    timeline_html = render_template("panels/_frag_forecast_timeline.html",
                                    cal_data=cal_data)
    oob_timeline = f'<div id="fc-timeline-inner" hx-swap-oob="innerHTML">{timeline_html}</div>'
    return make_response(whatif_html + oob_timeline)


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
    """Translate scenario allocations blob into 5-tuple:
    (bucket_overrides, off_buckets, schedule, phantom_monthly, paycheck_overrides)."""
    bucket_overrides    = dict(allocs.get("bucket_overrides") or {})
    paycheck_overrides  = dict(allocs.get("paycheck_overrides") or {})
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
        amt = float(bucket_overrides.get(bid) or b.get("defaultBudget") or 0)
        if amt <= 0:
            continue
        phantom_monthly.append({"id": bid, "name": b["name"], "amount": amt})
    return (bucket_overrides or None, off_buckets or None,
            schedule or None, phantom_monthly or None,
            paycheck_overrides or None)


def _scenario_fc_params(scenarios: list, active_sid: str, n_months: int, data: dict):
    """Extract forecast params for the active scenario (5-tuple)."""
    if not active_sid:
        return None, None, None, None, None
    sc = next((s for s in scenarios if s["id"] == active_sid), None)
    if not sc:
        return None, None, None, None, None
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
    paycheck_overrides = {}
    for pc in data.get("paychecks", []):
        pc_id = str(pc.get("id", ""))
        raw = (f.get(f"paycheck_amt_{pc_id}") or "").strip()
        if raw:
            try:
                paycheck_overrides[pc_id] = float(raw.replace("$", "").replace(",", ""))
            except ValueError:
                pass
    return {"bucket_overrides": bucket_overrides, "off_buckets": off_buckets,
            "changes": changes, "paycheck_overrides": paycheck_overrides}


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
    paycheck_overrides = dict(allocs.get("paycheck_overrides") or {})
    changes_by_bid = {ch["bid"]: ch for ch in (allocs.get("changes") or [])}
    paychecks = [{"id": str(pc.get("id", "")), "label": pc.get("label", "Paycheck"),
                  "amount": float(pc.get("amount") or 0)}
                 for pc in data.get("paychecks", [])]
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
        "paycheck_overrides": paycheck_overrides,
        "paychecks": paychecks,
        "changes_by_bid": changes_by_bid,
        "month_options": month_options,
    }


def _fc_frag_response(active_sid: str = "", skip_dates: list = None,
                       no_accrue_dates: list = None, n_months: int = 3,
                       income_override: float = 0.0):
    """Render forecast fragments as OOB response after scenario save/delete.
    Updates the what-if content, KPI bar (already OOB inside the whatif fragment),
    and the 60-day timeline so all three stay in sync with the active scenario.
    """
    skip_dates = skip_dates or []
    no_accrue_dates = no_accrue_dates or []
    data = D.load_data()
    scenarios = _load_scenarios()
    bucket_overrides, off_buckets, schedule, phantom_monthly, pc_ovr = \
        _scenario_fc_params(scenarios, active_sid, n_months, data)
    effective_pc_overrides = pc_ovr
    from . import forecast_calc as FC
    fc = FC.compute_forecast(data, n_months=n_months, income_override=income_override,
                             skipped_pay_dates=skip_dates,
                             no_accrue_dates=no_accrue_dates,
                             bucket_overrides=bucket_overrides,
                             off_buckets=off_buckets,
                             schedule=schedule,
                             phantom_monthly=phantom_monthly,
                             paycheck_overrides=effective_pc_overrides)
    svg = FC.build_balance_svg(fc["periods"])
    cal_data = FC.compute_calendar_data(data, 60, off_buckets=off_buckets)
    whatif_html = render_template("panels/_frag_forecast_whatif.html",
                                  forecast=fc, balance_svg=svg,
                                  n_months=n_months, income_override=income_override,
                                  skipped_pay_dates=skip_dates,
                                  skip_dates_str=",".join(skip_dates),
                                  no_accrue_dates=no_accrue_dates,
                                  no_accrue_dates_str=",".join(no_accrue_dates),
                                  scenarios=scenarios,
                                  active_scenario_id=active_sid,
                                  paychecks=data.get("paychecks", []),
                                  paycheck_overrides_form={},
                                  is_htmx=True)
    timeline_html = render_template("panels/_frag_forecast_timeline.html",
                                    cal_data=cal_data)
    oob = (f'<div id="fc-whatif-content" hx-swap-oob="innerHTML">{whatif_html}</div>'
           f'<div id="fc-timeline-inner" hx-swap-oob="innerHTML">{timeline_html}</div>')
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


def _safe_n_months(raw) -> int:
    try:
        return max(1, min(12, int(raw or 3)))
    except (ValueError, TypeError):
        return 3


@bp.route("/transaction/<tid>/paycheck-distribute", methods=["GET"])
@login_required
def paycheck_distribute_open(tid):
    """Open the paycheck-distribute modal with smart defaults (e.g. for a
    paycheck logged via Quick Add, prompted on next full-app visit)."""
    tx = next((t for t in D.load_data().get("txs", []) if t.get("id") == tid), None)
    if not tx:
        return "", 404
    amount = float(tx.get("amount") or 0)
    mid = tx.get("monthId") or D.active_mid()
    ctx = D.paycheck_distribute_ctx(amount, mid)
    return render_template("panels/_frag_paycheck_distribute.html", tid=tid, **ctx)


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
        checked_forecast_ob=set(f.getlist("forecast_ob")),
    )
    return render_template("panels/_frag_paycheck_distribute.html", tid=tid, **ctx)


@bp.route("/transaction/<tid>/edit", methods=["GET"])
@login_required
def transaction_edit(tid):
    tx = D.tx_by_id(tid)
    if not tx:
        flash("Transaction not found.", "error")
        return redirect(url_for("panels.accounts"))
    back = session.get("active_panel", "accounts")
    if _is_modal():
        return render_template("panels/_frag_edit_tx.html", tx=tx, back=back,
                               **D.tx_form_ctx())
    return render_panel("panels/edit_tx.html", back,
                        tx=tx, back=back, **D.tx_form_ctx())


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


@bp.route("/month/<direction>")
@login_required
def month_nav(direction):
    y, m0 = D.F.parse_month_id(D.active_mid())
    total = y * 12 + m0 + (1 if direction == "next" else -1)
    session["active_mid"] = f"m_{total // 12}_{total % 12}"
    return redirect(url_for("panels." + session.get("active_panel", "buckets")))


@bp.route("/month/today")
@login_required
def month_today():
    """Jump the active month back to today's calendar month."""
    session["active_mid"] = D.F.current_month_id()
    return redirect(url_for("panels." + session.get("active_panel", "buckets")))


# ── Stub panels (built in later phases) ───────────────────────────────────────

def _stub(name, title):
    @login_required
    def view():
        return render_panel("panels/_stub.html", name, title=title)
    view.__name__ = name
    return view


# (all panels now have real routes)


# ── Action registry dispatcher (Phase 2 of REFACTOR_PLAN.md) ─────────────────
# New mutation routes register an Action in actions.py and run through here.
# Existing routes are migrated one group at a time per REFACTOR_PLAN.md —
# nothing below replaces them yet.

@bp.route("/actions/<name>", methods=["POST"])
@login_required
def run_action(name):
    return A.dispatch(name)


@bp.route("/health")
@login_required
def health():
    """Full app health check and diagnostics page."""
    import json as _json
    from datetime import datetime as _dt
    from . import db as _DB
    from . import formulas as _F
    from collections import defaultdict as _dd

    generated_at = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
    issues, hints = [], []
    db_errors = ""

    try:
        raw = _DB.load_all(session["user_id"], session["access_token"])
    except Exception as e:
        raw = {"accounts": [], "cats": [], "buckets": [], "txs": [], "months": [],
               "paychecks": [], "allocationRules": []}
        db_errors = f"{type(e).__name__}: {e}"
        issues.append("DB load failed")

    accounts = raw.get("accounts", [])
    buckets  = raw.get("buckets", [])
    txs      = raw.get("txs", [])
    months   = raw.get("months", [])
    cats     = raw.get("cats", [])

    # ── Data counts ──────────────────────────────────────────────────────────
    data_counts = [
        {"label": "Accounts",         "count": len(accounts)},
        {"label": "Categories",       "count": len(cats)},
        {"label": "Buckets",          "count": len(buckets)},
        {"label": "Transactions",     "count": len(txs)},
        {"label": "Month records",    "count": len(months)},
        {"label": "Paychecks",        "count": len(raw.get("paychecks", []))},
        {"label": "Allocation rules", "count": len(raw.get("allocationRules", []))},
    ]
    if len(accounts) == 0:   issues.append("No accounts")
    if len(txs) == 0:        hints.append("No transactions loaded")
    if len(buckets) == 0:    issues.append("No buckets")
    if len(cats) == 0:       issues.append("No categories")

    # ── Session info ─────────────────────────────────────────────────────────
    today_mid = _F.current_month_id()
    acct_mid_val = session.get("acct_mid") or today_mid
    active_mid_val = session.get("active_mid") or today_mid
    session_info = [
        {"label": "Logged in as",    "value": session.get("email", "—")},
        {"label": "Today's month",   "value": today_mid},
        {"label": "Buckets month",   "value": active_mid_val},
        {"label": "Accounts month",  "value": acct_mid_val},
        {"label": "DEV_SEED",        "value": "yes" if current_app.config.get("DEV_SEED") else "no"},
    ]

    # ── Account health ────────────────────────────────────────────────────────
    tx_by_acct = _dd(int)
    opening_accts = set()
    for t in txs:
        tx_by_acct[t.get("accountId", "")] += 1
        if t.get("type") == "opening":
            opening_accts.add(t.get("accountId", ""))

    account_health = []
    for a in accounts:
        if a.get("archived"):
            continue
        bal = _F.acct_balance(a, txs)
        has_opening = a["id"] in opening_accts
        if not has_opening:
            hints.append(f"No opening tx for '{a['name']}'")
        account_health.append({
            "name": a["name"], "type": a.get("type", "budget"),
            "balance": bal, "tx_count": tx_by_acct[a["id"]],
            "has_opening": has_opening,
        })

    # ── Tx by type ────────────────────────────────────────────────────────────
    type_counts = _dd(int)
    for t in txs:
        type_counts[t.get("type", "out")] += 1
    tx_by_type = [{"type": k, "count": v}
                  for k, v in sorted(type_counts.items(), key=lambda x: -x[1])]

    # ── Tx by month (last 6) ──────────────────────────────────────────────────
    mid_counts = _dd(int)
    for t in txs:
        mid_counts[t.get("monthId", "")] += 1
    recent_mids = [_F.month_offset(today_mid, -i) for i in range(6)]
    from . import data as _D
    tx_by_month = [
        {"label": _D.month_label(m), "count": mid_counts.get(m, 0)}
        for m in recent_mids
    ]
    if all(r["count"] == 0 for r in tx_by_month):
        issues.append(f"No recent transactions in any of the last 6 months (oldest loaded: {min((t['monthId'] for t in txs if t.get('monthId')), default='none')})")

    # ── Bucket issues ─────────────────────────────────────────────────────────
    bkt_map = {b["id"]: b for b in buckets}
    bucket_issues = []
    for b in buckets:
        if b.get("archived"):
            continue
        if not b.get("catId"):
            bucket_issues.append({"name": b["name"], "issue": "No category assigned", "value": "—"})
        if b.get("type") == "expense" and not b.get("defaultBudget"):
            pass  # fine — open-ended expense bucket
    # Check for orphaned bucket references in txs
    orphaned_bids = set()
    for t in txs:
        bid = t.get("bucketId")
        if bid and bid not in bkt_map:
            orphaned_bids.add(bid)
    if orphaned_bids:
        bucket_issues.append({"name": "—", "issue": f"Transactions reference {len(orphaned_bids)} deleted bucket(s)", "value": ", ".join(list(orphaned_bids)[:3])})

    # ── Month health ──────────────────────────────────────────────────────────
    def _mlabel(mid):
        try:
            y, m0 = _F.parse_month_id(mid)
            import calendar as _cal
            return f"{_cal.month_name[m0+1][:3]} {y}"
        except Exception:
            return mid

    month_health = sorted([{
        "label": _mlabel(m["id"]),
        "sort_key": _F.parse_month_id(m["id"]) if "_" in m["id"] else (0, 0),
        "alloc_count": len(m.get("allocations", {})),
        "budget_count": len(m.get("budgets", {})),
        "closed": bool(m.get("closed")),
    } for m in months], key=lambda x: x["sort_key"], reverse=True)[:12]

    # ── Shared base values (needed by all sections below) ────────────────────
    today_month = next((m for m in months if m["id"] == today_mid),
                       {"id": today_mid, "allocations": {}, "budgets": {}})
    active_buckets = [b for b in buckets if not b.get("archived")]

    # ── Budget metrics ────────────────────────────────────────────────────────
    budget_metrics = []
    rts = total_cash = income = allocated = spent = 0.0
    try:
        rts        = _F.ready_to_spend(today_month, months, accounts, active_buckets, txs)
        total_cash = _F.total_cash(accounts, txs)
        income     = _F.month_income(today_mid, txs, accounts)
        allocated  = _F.total_allocated(today_month, active_buckets)
        spent      = sum(_F.b_spent(today_mid, b["id"], txs) for b in active_buckets)
        budget_metrics = [
            {"label": "Ready to Spend",   "value": f"${rts:,.2f}",        "alert": rts < 0},
            {"label": "Total Cash",       "value": f"${total_cash:,.2f}",  "alert": total_cash < 0},
            {"label": "Month Income",     "value": f"${income:,.2f}",      "alert": False},
            {"label": "Month Allocated",  "value": f"${allocated:,.2f}",   "alert": False},
            {"label": "Month Spent",      "value": f"${spent:,.2f}",       "alert": False},
        ]
        if rts < 0:
            issues.append(f"Negative RTS (${rts:,.2f})")
        if total_cash < 0:
            hints.append(f"Total cash is negative (${total_cash:,.2f})")
    except Exception as e:
        budget_metrics = [{"label": "Error", "value": str(e), "alert": True}]
        issues.append(f"Budget metrics error: {e}")

    # ── Cash flow: last 6 months ──────────────────────────────────────────────
    cash_flow_months = []
    cash_flow_error = ""
    try:
        recent_6 = [_F.month_offset(today_mid, -i) for i in range(6)]
        for mid_ in recent_6:
            inc_ = _F.month_income(mid_, txs, accounts)
            sp_  = sum(_F.b_spent(mid_, b["id"], txs) for b in active_buckets)
            net_ = round(inc_ - sp_, 2)
            cash_flow_months.append({
                "label": _D.month_label(mid_),
                "income": inc_, "spent": sp_, "net": net_,
                "net_pos": net_ >= 0,
            })
    except Exception as e:
        cash_flow_error = str(e)

    # ── Allocation breakdown ──────────────────────────────────────────────────
    allocation_breakdown = []
    allocation_error = ""
    try:
        vault_bkts   = [b for b in active_buckets if b.get("type") == "vault"]
        expense_bkts = [b for b in active_buckets if b.get("type") not in ("vault", "sinking", "goal")]
        savings_bkts = [b for b in active_buckets if b.get("type") in ("sinking", "goal")]
        alloc_expense = sum(_F.b_alloc(today_month, b["id"]) for b in expense_bkts)
        alloc_vault   = sum(_F.b_alloc(today_month, b["id"]) for b in vault_bkts)
        alloc_savings = sum(_F.b_alloc(today_month, b["id"]) for b in savings_bkts)
        # Single O(M) pass instead of O(V×M) separate vault_accumulated() calls
        _vault_bid_set = {b["id"] for b in vault_bkts}
        _vault_accum: dict[str, float] = {}
        for _m in months:
            _allocs = _m.get("allocations") or {}
            _wds    = _m.get("vaultWithdrawals") or {}
            for _bid in _vault_bid_set:
                _vault_accum[_bid] = _vault_accum.get(_bid, 0.0) + float(_allocs.get(_bid) or 0) - float(_wds.get(_bid) or 0)
        vault_total = sum(max(0.0, v) for v in _vault_accum.values())
        bb            = _F.budget_bal(accounts, txs)
        alloc_rate    = round(allocated / bb * 100, 1) if bb > 0 else 0.0
        locked_ct     = sum(1 for b in vault_bkts if b.get("locked"))
        paused_ct     = sum(1 for b in vault_bkts if b.get("paused") and not b.get("locked"))
        allocation_breakdown = [
            {"label": "Month allocated",          "value": f"${allocated:,.2f}",     "alert": False},
            {"label": "Month income (txns in)",   "value": f"${income:,.2f}",        "alert": False},
            {"label": "Alloc rate (vs cash)",     "value": f"{alloc_rate}%",         "alert": alloc_rate > 100},
            {"label": "Ready to Spend (unalloc)", "value": f"${rts:,.2f}",           "alert": rts < 0},
            {"label": "→ Expense buckets",        "value": f"${alloc_expense:,.2f}", "alert": False},
            {"label": "→ Vault buckets",          "value": f"${alloc_vault:,.2f}",   "alert": False},
            {"label": "→ Sinking / goal",         "value": f"${alloc_savings:,.2f}", "alert": False},
            {"label": "Vault portfolio total",    "value": f"${vault_total:,.2f}",   "alert": False},
            {"label": "Vault count",              "value": f"{len(vault_bkts)} ({locked_ct} locked, {paused_ct} paused)", "alert": False},
        ]
        if alloc_rate > 100:
            issues.append(f"Allocated ${allocated:,.2f} exceeds liquid cash ${bb:,.2f}")
    except Exception as e:
        allocation_error = str(e)

    # ── RTS verification (ZBB identity: bb = RTS + cur_claimed + future) ─────
    rts_verify = []
    rts_verify_error = ""
    bucket_claims_detail = []   # per-bucket breakdown for current claims
    future_allocs_detail = []   # per-bucket breakdown for future allocations
    try:
        bb_v        = _F.budget_bal(accounts, txs)
        future_mids = _F.months_after(today_mid, months)

        # Per-bucket current claims (non-zero only, sorted largest first)
        raw_claims = []
        for b in active_buckets:
            claim = _F.bucket_available(b, today_month, months, txs)
            if abs(claim) > 0.005:
                raw_claims.append({"name": b["name"], "type": b.get("type","expense"), "claim": round(claim, 2)})
        bucket_claims_detail = sorted(raw_claims, key=lambda x: -x["claim"])

        cur_claimed = sum(c["claim"] for c in raw_claims)

        # Per-bucket future allocations (non-zero only, sorted largest first)
        raw_future: dict = {}
        for fm in future_mids:
            for b in active_buckets:
                amt = _F.b_alloc(fm, b["id"])
                if amt > 0.005:
                    raw_future.setdefault(b["id"], {"name": b["name"], "amount": 0.0})["amount"] += amt
        future_allocs_detail = sorted(raw_future.values(), key=lambda x: -x["amount"])

        future_claimed = sum(x["amount"] for x in future_allocs_detail)

        zbb_check = round(bb_v - cur_claimed - future_claimed, 2)
        # Re-compute rts here independently so a budget_metrics failure doesn't
        # leave us comparing against the 0.0 default and producing a false drift.
        rts_actual = _F.ready_to_spend(today_month, months, accounts, active_buckets, txs)
        zbb_ok    = abs(zbb_check - rts_actual) < 0.02
        rts_verify = [
            {"label": "Bank balance (bb)",        "value": f"${bb_v:,.2f}",                  "alert": False,      "detail": None},
            {"label": "− Current bucket claims",  "value": f"${cur_claimed:,.2f}",           "alert": False,      "detail": "claims"},
            {"label": "− Future pre-allocations", "value": f"${future_claimed:,.2f}",        "alert": False,      "detail": "future"},
            {"label": "= Calculated RTS",         "value": f"${zbb_check:,.2f}",             "alert": not zbb_ok, "detail": None},
            {"label": "RTS displayed",            "value": f"${rts_actual:,.2f}",            "alert": not zbb_ok, "detail": None},
            {"label": "ZBB identity holds",       "value": "✓ Yes" if zbb_ok else f"✗ Drift ${abs(zbb_check - rts_actual):,.2f}", "alert": not zbb_ok, "detail": None},
        ]
        if not zbb_ok:
            issues.append(f"ZBB identity broken — drift ${abs(zbb_check - rts):,.2f}")
    except Exception as e:
        rts_verify_error = str(e)

    # ── Unassigned expense transactions ──────────────────────────────────────
    # Exclude debt accounts — interest charges legitimately have no bucket
    debt_aid_set = {a["id"] for a in accounts if a.get("type") == "debt"}
    unassigned_txs = sorted([
        {"date": t.get("date",""), "desc": t.get("desc","Transaction"),
         "amount": float(t.get("amount") or 0)}
        for t in txs
        if t.get("type") == "out" and not t.get("bucketId")
        and not _F.is_scheduled(t)
        and t.get("accountId") not in debt_aid_set
    ], key=lambda x: x["date"], reverse=True)
    if unassigned_txs:
        hints.append(f"{len(unassigned_txs)} expense transaction(s) not assigned to a bucket")

    # ── Raw JSON ──────────────────────────────────────────────────────────────
    raw_summary = {k: len(v) if isinstance(v, list) else str(v) for k, v in raw.items()}
    raw_json = _json.dumps(raw_summary, indent=2)

    return render_template("panels/health.html",
        generated_at=generated_at,
        issues=issues, hints=hints,
        data_counts=data_counts,
        session_info=session_info,
        account_health=account_health,
        tx_by_type=tx_by_type,
        tx_by_month=tx_by_month,
        bucket_issues=bucket_issues,
        month_health=month_health,
        budget_metrics=budget_metrics,
        cash_flow_months=cash_flow_months,
        cash_flow_error=cash_flow_error,
        allocation_breakdown=allocation_breakdown,
        allocation_error=allocation_error,
        rts_verify=rts_verify,
        rts_verify_error=rts_verify_error,
        bucket_claims_detail=bucket_claims_detail,
        future_allocs_detail=future_allocs_detail,
        unassigned_txs=unassigned_txs,
        db_errors=db_errors,
        raw_json=raw_json,
    )


# ── Quick Add — standalone, home-screen-installable transaction entry ───────

@bp.route("/quick", methods=["GET", "POST"])
@quick_required
def quick_add():
    from datetime import date as _date
    saved = False
    if request.method == "POST":
        f = request.form
        amount = D.parse_amount(f.get("amount", "0"))
        tx_type = f.get("type", "out")
        iso = f.get("date") or _date.today().isoformat()
        y, m, _d = (iso[:10].split("-") + ["1", "1", "1"])[:3]
        mid = D.F.month_id(int(y), int(m) - 1)
        tx = {
            "accountId": f.get("accountId", ""), "monthId": mid,
            "type": tx_type, "amount": amount, "date": iso,
            "desc": f.get("desc", ""), "bucketId": f.get("bucketId") or "",
            "toAccountId": f.get("toAccountId") or "",
            "incomeType": f.get("incomeType") or "paycheck",
            "planned": f.get("planned", "1") == "1",
        }
        data = D.load_data()
        bkt = next((b for b in data.get("buckets", []) if b["id"] == tx["bucketId"]), None)
        if bkt and bkt.get("type") == "vault":
            flash("Vault buckets cannot hold transactions. Use Transfer instead in the full app.", "error")
        elif current_app.config["DEV_SEED"]:
            flash("Dev mode: transaction not persisted (no database).", "ok")
        elif tx_type == "xfr" and not tx["toAccountId"]:
            flash("Pick a destination account for the transfer.", "error")
        elif amount > 0 and tx["accountId"]:
            new_tid = DB.insert_transaction(session["user_id"], session["access_token"], tx)
            D.invalidate_cache()
            saved = True
            flash("Transaction added.", "ok")
            if tx_type == "in" and tx["incomeType"] == "paycheck":
                session["pending_distribute_tid"] = new_tid
        else:
            flash("Amount and account are required.", "error")
        if saved:
            return redirect(url_for("panels.quick_add", saved="1"))
        return redirect(url_for("panels.quick_add"))
    saved = request.args.get("saved") == "1"
    ctx = D.tx_form_ctx()
    return render_template("quick.html", saved=saved, **ctx)
