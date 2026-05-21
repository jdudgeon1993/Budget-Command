import os
import traceback
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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


def load_budget_row(access_token: str) -> tuple:
    """Returns (row_id, data_dict). row_id is None if no row found."""
    try:
        sb = get_supabase(access_token)
        resp = (sb.table("bcc_budget_state")
                  .select("id,data")
                  .order("id", desc=True)
                  .limit(1)
                  .execute())
        if resp.data:
            return resp.data[0]["id"], resp.data[0].get("data", {})
    except Exception as e:
        app.logger.error("load_budget_row failed: %s\n%s", e, traceback.format_exc())
    return None, {}


def load_budget(access_token: str) -> dict:
    _, data = load_budget_row(access_token)
    return data


def save_budget_row(access_token: str, row_id, data: dict) -> None:
    try:
        sb = get_supabase(access_token)
        sb.table("bcc_budget_state").update({"data": data}).eq("id", row_id).execute()
    except Exception as e:
        app.logger.error("save_budget_row failed: %s\n%s", e, traceback.format_exc())


def _find_or_create_month(data: dict, mid: str) -> dict:
    months = data.setdefault("months", [])
    month = next((m for m in months if m["id"] == mid), None)
    if month is None:
        month = {"id": mid, "allocations": {}, "budgets": {}, "rolloverReleased": {}, "skippedBuckets": {}}
        months.append(month)
    return month


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


@app.route("/api/save", methods=["POST"])
def api_save():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body = request.get_json(silent=True) or {}
    field = body.get("field", "")
    bid   = body.get("id", "")
    value = body.get("value")
    mid   = body.get("month", "")

    row_id, data = load_budget_row(session["access_token"])
    if row_id is None:
        return jsonify({"ok": False, "error": "No data row found"}), 404

    bucket = next((b for b in data.get("buckets", []) if b["id"] == bid), None)

    if field == "cat_name":
        cat = next((c for c in data.get("cats", []) if c["id"] == bid), None)
        if cat:
            cat["name"] = str(value or "").strip()

    elif field == "bucket_name":
        if bucket:
            bucket["name"] = str(value or "").strip()

    elif field == "bucket_target":
        month = _find_or_create_month(data, mid)
        month.setdefault("budgets", {})[bid] = float(value or 0)

    elif field == "bucket_alloc":
        month = _find_or_create_month(data, mid)
        month.setdefault("allocations", {})[bid] = float(value or 0)

    elif field == "bucket_type":
        if bucket:
            bucket["type"] = str(value or "expense")

    elif field == "bucket_cat":
        if bucket:
            bucket["catId"] = str(value or "")

    elif field == "bucket_rollover":
        if bucket:
            bucket["rollover"] = bool(value)

    elif field == "bucket_recurring":
        if bucket:
            bucket["recurring"] = bool(value)

    elif field == "bucket_due_day":
        if bucket:
            v = str(value or "").strip()
            bucket["dueDay"] = int(v) if v.isdigit() else (v if v == "eom" else None)

    elif field == "bucket_pay_freq":
        if bucket:
            bucket["payFreq"] = str(value) if value else None

    elif field == "bucket_due_amount":
        if bucket:
            bucket["dueAmount"] = float(value) if value not in (None, "", 0) else None

    elif field == "bucket_debt_account":
        if bucket:
            bucket["debtAccountId"] = str(value) if value else None

    elif field == "bucket_notes":
        if bucket:
            bucket["notes"] = str(value or "").strip() or None

    elif field == "bucket_target_amount":
        if bucket:
            bucket["targetAmount"] = float(value) if value not in (None, "") else None

    elif field == "bucket_target_date":
        if bucket:
            bucket["targetDate"] = str(value) if value else None

    elif field == "bucket_contrib_freq":
        if bucket:
            bucket["contribFreq"] = str(value) if value else None

    elif field == "bucket_default_budget":
        if bucket:
            bucket["defaultBudget"] = float(value or 0)

    elif field == "bucket_skip":
        month = _find_or_create_month(data, mid)
        month.setdefault("skippedBuckets", {})[bid] = bool(value)

    elif field == "bucket_archive":
        if bucket:
            bucket["archived"] = True

    else:
        return jsonify({"ok": False, "error": f"Unknown field: {field}"}), 400

    save_budget_row(session["access_token"], row_id, data)

    result = {"ok": True}

    # Recompute avail + rts after alloc/target changes
    if field in ("bucket_alloc", "bucket_target") and mid:
        bucket = next((b for b in data.get("buckets", []) if b["id"] == bid), None)
        all_months = data.get("months", [])
        txs = data.get("txs", [])
        active_month = next((m for m in all_months if m["id"] == mid), None)
        if bucket and active_month:
            avail = bucket_available(bucket, active_month, all_months, txs)
            result["avail"] = avail
            accounts = data.get("accounts", [])
            active_buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
            result["rts"] = ready_to_spend(active_month, all_months, accounts, active_buckets, txs)

    return jsonify(result)


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

    accounts    = S.get("accounts") or []
    all_buckets = S.get("buckets") or []
    cats        = S.get("cats") or []
    all_months  = S.get("months") or []
    txs         = S.get("txs") or []

    mid_param = request.args.get("month", "")
    try:
        parse_month_id(mid_param)
        active_mid = mid_param
    except Exception:
        active_mid = S.get("activeMonth") or current_month_id()

    year, m0 = parse_month_id(active_mid)
    prev_mid = month_id(year - 1, 11) if m0 == 0 else month_id(year, m0 - 1)
    next_mid = month_id(year + 1, 0) if m0 == 11 else month_id(year, m0 + 1)

    active_month = next(
        (m for m in all_months if m.get("id") == active_mid),
        {"id": active_mid, "allocations": {}, "budgets": {}, "rolloverReleased": {}, "skippedBuckets": {}},
    )

    active_buckets = [b for b in all_buckets if not b.get("archived")]
    cats_sorted    = sorted(cats, key=lambda c: c.get("order", 0))

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

        rows   = []
        totals = dict(alloc=0.0, budget=0.0, rollover=0.0, spent=0.0, avail=0.0)

        for b in cat_buckets:
            alloc  = b_alloc(active_month, b["id"])
            budget = b_budget(active_month, b["id"])
            roll   = rollover_bal(b, active_month, all_months, txs)
            spent  = b_spent(active_mid, b["id"], txs)
            avail  = bucket_available(b, active_month, all_months, txs)
            status = bucket_status(alloc, spent, avail)
            skipped = bool((active_month.get("skippedBuckets") or {}).get(b["id"]))

            rows.append({
                "id":              b["id"],
                "name":            b["name"],
                "type":            b.get("type", "expense"),
                "cat_id":          b.get("catId", cid),
                "rollover":        b.get("rollover", False),
                "recurring":       b.get("recurring", False),
                "skipped":         skipped,
                "due_day":         b.get("dueDay", ""),
                "pay_freq":        b.get("payFreq", ""),
                "due_amount":      b.get("dueAmount", ""),
                "debt_account_id": b.get("debtAccountId", ""),
                "notes":           b.get("notes", "") or "",
                "target_amount":   b.get("targetAmount", ""),
                "target_date":     b.get("targetDate", ""),
                "contrib_freq":    b.get("contribFreq", ""),
                "default_budget":  b.get("defaultBudget", 0),
                "alloc":           alloc,
                "budget":          budget,
                "rollover_val":    roll,
                "spent":           spent,
                "avail":           avail,
                "status":          status,
            })

            totals["alloc"]    += alloc
            totals["budget"]   += budget
            totals["rollover"] += roll
            totals["spent"]    += spent
            totals["avail"]    += avail

        category_groups.append({
            "id":      cid,
            "name":    cat.get("name", ""),
            "color":   cat.get("color", ""),
            "buckets": rows,
            "totals":  totals,
        })

        for k in grand:
            grand[k] += totals[k]

    rts = ready_to_spend(active_month, all_months, accounts, active_buckets, txs)

    debt_accounts = [a for a in accounts if a.get("type") == "debt"]

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
        all_cats=cats_sorted,
        debt_accounts=debt_accounts,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_ENV") == "development")
