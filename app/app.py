import os
import traceback
from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client
from dotenv import load_dotenv
from formulas import (
    current_month_id, parse_month_id, month_id,
    b_alloc, b_budget, b_spent, rollover_bal, bucket_available, ready_to_spend,
)

MONTH_NAMES = ["January","February","March","April","May","June",
               "July","August","September","October","November","December"]

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]


@app.template_filter("money")
def money_filter(value):
    try:
        v = float(value or 0)
        if v < 0:
            return f"-${abs(v):,.2f}"
        return f"${v:,.2f}"
    except (TypeError, ValueError):
        return "$0.00"


def get_supabase(access_token: str | None = None) -> Client:
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    if access_token:
        client.postgrest.auth(access_token)
    return client


def logged_in() -> bool:
    return "access_token" in session


def load_budget(access_token: str) -> dict:
    try:
        sb = get_supabase(access_token)
        resp = (sb.table("bcc_budget_state")
                  .select("data")
                  .single()
                  .execute())
        return resp.data.get("data", {}) if resp.data else {}
    except Exception as e:
        app.logger.error("load_budget failed: %s\n%s", e, traceback.format_exc())
        return {}


def bucket_status(alloc: float, spent: float, avail: float) -> str:
    if avail < 0:
        return "OVER"
    if alloc > 0 and spent >= alloc:
        return "PAID"
    if alloc > 0:
        return "OK"
    return ""


@app.route("/")
def index():
    if not logged_in():
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        try:
            sb = get_supabase()
            resp = sb.auth.sign_in_with_password({"email": email, "password": password})
            session["access_token"] = resp.session.access_token
            session["user_email"] = resp.user.email
            return redirect(url_for("dashboard"))
        except Exception:
            error = "Invalid email or password."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/health")
def health():
    return {"status": "ok"}


@app.route("/dashboard")
def dashboard():
    if not logged_in():
        return redirect(url_for("login"))

    try:
        return _dashboard_inner()
    except Exception as e:
        app.logger.error("dashboard error: %s\n%s", e, traceback.format_exc())
        raise


def _dashboard_inner():
    S = load_budget(session["access_token"])

    accounts   = S.get("accounts") or []
    all_buckets = S.get("buckets") or []
    cats       = S.get("cats") or []
    all_months = S.get("months") or []
    txs        = S.get("txs") or []

    # Active month — prefer URL param, fall back to stored activeMonth, then today
    mid_param = request.args.get("month", "")
    try:
        parse_month_id(mid_param)
        active_mid = mid_param
    except Exception:
        active_mid = S.get("activeMonth") or current_month_id()

    year, m0 = parse_month_id(active_mid)
    prev_mid = month_id(year - 1, 11) if m0 == 0 else month_id(year, m0 - 1)
    next_mid = month_id(year + 1, 0) if m0 == 11 else month_id(year, m0 + 1)

    # Find the active month record (empty scaffold if it doesn't exist yet)
    active_month = next(
        (m for m in all_months if m.get("id") == active_mid),
        {"id": active_mid, "allocations": {}, "budgets": {}, "rolloverReleased": {}, "skippedBuckets": {}},
    )

    active_buckets = [b for b in all_buckets if not b.get("archived")]

    # Build category groups sorted by order
    cats_sorted = sorted(cats, key=lambda c: c.get("order", 0))

    category_groups = []
    grand = dict(alloc=0.0, budget=0.0, rollover=0.0, spent=0.0, avail=0.0)

    for cat in cats_sorted:
        cid = cat["id"]
        cat_buckets = sorted(
            [b for b in active_buckets if b.get("catId") == cid],
            key=lambda b: b.get("order", 0),
        )
        if not cat_buckets:
            continue

        rows = []
        totals = dict(alloc=0.0, budget=0.0, rollover=0.0, spent=0.0, avail=0.0)

        for b in cat_buckets:
            alloc  = b_alloc(active_month, b["id"])
            budget = b_budget(active_month, b["id"])
            roll   = rollover_bal(b, active_month, all_months, txs)
            spent  = b_spent(active_mid, b["id"], txs)
            avail  = bucket_available(b, active_month, all_months, txs)
            status = bucket_status(alloc, spent, avail)

            rows.append({
                "id":      b["id"],
                "name":    b["name"],
                "type":    b.get("type", "regular"),
                "rollover": b.get("rollover", False),
                "alloc":   alloc,
                "budget":  budget,
                "rollover_val": roll,
                "spent":   spent,
                "avail":   avail,
                "status":  status,
            })

            totals["alloc"]   += alloc
            totals["budget"]  += budget
            totals["rollover"] += roll
            totals["spent"]   += spent
            totals["avail"]   += avail

        category_groups.append({
            "name":    cat.get("name", ""),
            "color":   cat.get("color", ""),
            "buckets": rows,
            "totals":  totals,
        })

        for k in grand:
            grand[k] += totals[k]

    rts = ready_to_spend(active_month, all_months, accounts, active_buckets, txs)

    return render_template(
        "dashboard.html",
        user_email=session.get("user_email"),
        active_mid=active_mid,
        month_display=f"{MONTH_NAMES[m0]} {year}",
        prev_mid=prev_mid,
        next_mid=next_mid,
        category_groups=category_groups,
        grand=grand,
        rts=rts,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_ENV") == "development")
