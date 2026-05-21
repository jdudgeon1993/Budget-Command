import os
import traceback
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from supabase import create_client, Client
from dotenv import load_dotenv
from formulas import (
    current_month_id, parse_month_id, month_id,
    b_alloc, b_budget, b_spent, rollover_bal, bucket_available, ready_to_spend,
    vault_accumulated, is_scheduled, acct_balance,
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


def _date_to_month_id(date_str: str) -> str:
    from datetime import date as _date
    d = _date.fromisoformat(date_str)
    return month_id(d.year, d.month - 1)


def _find_or_create_month(data: dict, mid: str) -> dict:
    months = data.setdefault("months", [])
    month = next((m for m in months if m["id"] == mid), None)
    if month is None:
        month = {"id": mid, "allocations": {}, "budgets": {}, "rolloverReleased": {}, "skippedBuckets": {}}
        months.append(month)
    return month


def bucket_status(alloc: float, budget: float, spent: float, avail: float) -> str:
    if avail < 0:
        return "OVER"
    if alloc > 0 and spent >= alloc:
        return "PAID"
    if budget > 0 and alloc >= budget:
        return "FUNDED"
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
            if bucket["type"] == "vault":
                bucket["rollover"] = False

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
            if bucket.get("type") == "vault":
                avail = vault_accumulated(bid, all_months)
            else:
                avail = bucket_available(bucket, active_month, all_months, txs)
            result["avail"] = avail
            result["rts"] = _rts_now(data)

    return jsonify(result)


def _rts_now(data: dict) -> float:
    """RTS for the current calendar month — always used for header display."""
    all_months = data.get("months", [])
    accounts   = data.get("accounts", [])
    txs        = data.get("txs", [])
    active_buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    cur_mid    = current_month_id()
    cur_month  = next(
        (m for m in all_months if m.get("id") == cur_mid),
        {"id": cur_mid, "allocations": {}, "budgets": {}, "rolloverReleased": {}, "skippedBuckets": {}},
    )
    return ready_to_spend(cur_month, all_months, accounts, active_buckets, txs)


def _new_id(prefix: str) -> str:
    import time, random, string
    chars = string.ascii_lowercase + string.digits
    suffix = "".join(random.choices(chars, k=6))
    return f"{prefix}_{suffix}"


@app.route("/api/add-bucket", methods=["POST"])
def api_add_bucket():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body = request.get_json(silent=True) or {}
    cat_id       = body.get("cat_id", "").strip()
    new_cat_name = body.get("new_cat_name", "").strip()
    bucket_name  = body.get("bucket_name", "").strip()
    bucket_type  = body.get("bucket_type", "expense")

    if not bucket_name:
        return jsonify({"ok": False, "error": "Bucket name required"}), 400

    row_id, data = load_budget_row(session["access_token"])
    if row_id is None:
        return jsonify({"ok": False, "error": "No data row found"}), 404

    cats    = data.setdefault("cats", [])
    buckets = data.setdefault("buckets", [])

    # Create new category if requested
    if cat_id == "__new__":
        if not new_cat_name:
            return jsonify({"ok": False, "error": "Category name required"}), 400
        cat_id = _new_id("cat")
        max_order = max((c.get("order", 0) for c in cats), default=0)
        cats.append({"id": cat_id, "name": new_cat_name, "color": "", "order": max_order + 1})

    # Verify category exists
    if not any(c["id"] == cat_id for c in cats):
        return jsonify({"ok": False, "error": "Category not found"}), 400

    # Create bucket
    cat_buckets = [b for b in buckets if b.get("catId") == cat_id and not b.get("archived")]
    max_order   = max((b.get("order", 0) for b in cat_buckets), default=0)
    bucket_id   = _new_id("bkt")
    buckets.append({
        "id":            bucket_id,
        "catId":         cat_id,
        "name":          bucket_name,
        "type":          bucket_type,
        "rollover":      bucket_type in ("sinking", "goal"),
        "recurring":     False,
        "archived":      False,
        "defaultBudget": 0,
        "order":         max_order + 1,
        "notes":         None,
    })

    save_budget_row(session["access_token"], row_id, data)
    return jsonify({"ok": True, "bucket_id": bucket_id, "cat_id": cat_id})


@app.route("/api/archive-category", methods=["POST"])
def api_archive_category():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body   = request.get_json(silent=True) or {}
    cat_id = body.get("cat_id", "").strip()

    row_id, data = load_budget_row(session["access_token"])
    if row_id is None:
        return jsonify({"ok": False, "error": "No data row found"}), 404

    cat = next((c for c in data.get("cats", []) if c["id"] == cat_id), None)
    if not cat:
        return jsonify({"ok": False, "error": "Category not found"}), 404

    cat["archived"] = True
    for b in data.get("buckets", []):
        if b.get("catId") == cat_id:
            b["archived"] = True

    save_budget_row(session["access_token"], row_id, data)
    return jsonify({"ok": True})


@app.route("/api/delete-category", methods=["POST"])
def api_delete_category():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body   = request.get_json(silent=True) or {}
    cat_id = body.get("cat_id", "").strip()

    row_id, data = load_budget_row(session["access_token"])
    if row_id is None:
        return jsonify({"ok": False, "error": "No data row found"}), 404

    active_in_cat = [
        b for b in data.get("buckets", [])
        if b.get("catId") == cat_id and not b.get("archived")
    ]
    if active_in_cat:
        return jsonify({"ok": False, "error": "Category still has active buckets"}), 400

    data["cats"] = [c for c in data.get("cats", []) if c["id"] != cat_id]
    save_budget_row(session["access_token"], row_id, data)
    return jsonify({"ok": True})


@app.route("/api/reorder", methods=["POST"])
def api_reorder():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body      = request.get_json(silent=True) or {}
    kind      = body.get("kind")        # "bucket" or "cat"
    item_id   = body.get("id", "")
    direction = body.get("direction")   # "up" or "down"
    cat_id    = body.get("cat_id", "")  # needed for buckets

    row_id, data = load_budget_row(session["access_token"])
    if row_id is None:
        return jsonify({"ok": False, "error": "No data row"}), 404

    if kind == "bucket":
        items = sorted(
            [b for b in data.get("buckets", [])
             if b.get("catId") == cat_id and not b.get("archived")],
            key=lambda b: b.get("order", 0),
        )
    elif kind == "cat":
        items = sorted(data.get("cats", []), key=lambda c: c.get("order", 0))
    else:
        return jsonify({"ok": False, "error": "Unknown kind"}), 400

    idx = next((i for i, x in enumerate(items) if x["id"] == item_id), None)
    if idx is None:
        return jsonify({"ok": False, "error": "Item not found"}), 404

    swap_idx = idx - 1 if direction == "up" else idx + 1
    if swap_idx < 0 or swap_idx >= len(items):
        return jsonify({"ok": True})  # already at edge, no-op

    # Swap order values
    items[idx]["order"], items[swap_idx]["order"] = items[swap_idx]["order"], items[idx]["order"]
    save_budget_row(session["access_token"], row_id, data)
    return jsonify({"ok": True})


@app.route("/api/vault-withdraw", methods=["POST"])
def api_vault_withdraw():
    """Release vault savings back to the RTS pool.
    Drains current month's allocation first (reduces an active claim),
    then records remainder in vaultWithdrawals (bookkeeping for prior savings)."""
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body      = request.get_json(silent=True) or {}
    bucket_id = body.get("id", "").strip()
    mid       = body.get("month", "").strip()
    amount    = float(body.get("amount") or 0)

    if amount <= 0:
        return jsonify({"ok": False, "error": "Amount must be positive"}), 400

    row_id, data = load_budget_row(session["access_token"])
    if row_id is None:
        return jsonify({"ok": False, "error": "No data row found"}), 404

    bucket = next((b for b in data.get("buckets", []) if b["id"] == bucket_id), None)
    if not bucket or bucket.get("type") != "vault":
        return jsonify({"ok": False, "error": "Not a vault bucket"}), 400

    # Validate before mutating: cannot release more than what's actually saved
    current_vault_total = vault_accumulated(bucket_id, data.get("months", []))
    if amount > current_vault_total + 0.005:
        return jsonify({"ok": False, "error": f"Cannot release more than the vault balance (${current_vault_total:.2f})"}), 400

    month = _find_or_create_month(data, mid)

    # Step 1: drain current month's allocation first (this IS an active RTS claim)
    current_alloc = float((month.get("allocations") or {}).get(bucket_id) or 0)
    from_alloc    = min(amount, current_alloc)
    remainder     = amount - from_alloc

    if from_alloc > 0:
        month.setdefault("allocations", {})[bucket_id] = current_alloc - from_alloc
        existing_far = float((month.get("vaultFromAllocReleased") or {}).get(bucket_id) or 0)
        month.setdefault("vaultFromAllocReleased", {})[bucket_id] = existing_far + from_alloc

    # Step 2: record remainder against prior-month savings (bookkeeping; doesn't affect RTS
    # because prior vault savings are already free in the cash pool)
    if remainder > 0:
        existing_w = float((month.get("vaultWithdrawals") or {}).get(bucket_id) or 0)
        month.setdefault("vaultWithdrawals", {})[bucket_id] = existing_w + remainder

    save_budget_row(session["access_token"], row_id, data)

    all_months = data.get("months", [])
    new_total  = vault_accumulated(bucket_id, all_months)

    return jsonify({"ok": True, "vault_total": new_total, "alloc": current_alloc - from_alloc, "rts": _rts_now(data)})


@app.route("/api/vault-transfer", methods=["POST"])
def api_vault_transfer():
    """Move saved vault funds into another bucket's allocation for this month.
    Vault alloc goes down, destination alloc goes up — net RTS effect is zero."""
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body      = request.get_json(silent=True) or {}
    vault_id  = body.get("vault_id", "").strip()
    dest_id   = body.get("dest_id", "").strip()
    mid       = body.get("month", "").strip()
    amount    = float(body.get("amount") or 0)

    if amount <= 0:
        return jsonify({"ok": False, "error": "Amount must be positive"}), 400
    if not dest_id:
        return jsonify({"ok": False, "error": "Destination bucket required"}), 400

    row_id, data = load_budget_row(session["access_token"])
    if row_id is None:
        return jsonify({"ok": False, "error": "No data row found"}), 404

    vault_bucket = next((b for b in data.get("buckets", []) if b["id"] == vault_id), None)
    dest_bucket  = next((b for b in data.get("buckets", []) if b["id"] == dest_id), None)
    if not vault_bucket or vault_bucket.get("type") != "vault":
        return jsonify({"ok": False, "error": "Not a vault bucket"}), 400
    if not dest_bucket or dest_bucket.get("archived"):
        return jsonify({"ok": False, "error": "Destination bucket not found"}), 400

    month = _find_or_create_month(data, mid)
    allocs = month.setdefault("allocations", {})

    vault_alloc = float(allocs.get(vault_id) or 0)
    allocs[vault_id] = max(0.0, vault_alloc - amount)

    dest_alloc = float(allocs.get(dest_id) or 0)
    allocs[dest_id] = dest_alloc + amount

    # Historical record
    transfers = data.setdefault("vaultTransfers", [])
    transfers.append({
        "id":           _new_id("vtx"),
        "fromBucketId": vault_id,
        "toBucketId":   dest_id,
        "amount":       amount,
        "monthId":      mid,
        "reason":       "planned",
    })

    save_budget_row(session["access_token"], row_id, data)

    all_months      = data.get("months", [])
    new_vault_total = vault_accumulated(vault_id, all_months)
    active_month    = next((m for m in all_months if m["id"] == mid), month)
    txs             = data.get("txs", [])
    dest_avail      = bucket_available(dest_bucket, active_month, all_months, txs)

    return jsonify({
        "ok":          True,
        "vault_total": new_vault_total,
        "vault_alloc": allocs[vault_id],
        "dest_avail":  dest_avail,
        "rts":         _rts_now(data),
    })


@app.route("/api/release-rollover", methods=["POST"])
def api_release_rollover():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body      = request.get_json(silent=True) or {}
    bucket_id = body.get("id", "").strip()
    mid       = body.get("month", "").strip()
    amount    = float(body.get("amount") or 0)

    if amount <= 0:
        return jsonify({"ok": False, "error": "Amount must be positive"}), 400

    row_id, data = load_budget_row(session["access_token"])
    if row_id is None:
        return jsonify({"ok": False, "error": "No data row found"}), 404

    bucket = next((b for b in data.get("buckets", []) if b["id"] == bucket_id), None)
    if not bucket:
        return jsonify({"ok": False, "error": "Bucket not found"}), 404
    if bucket.get("type") == "vault":
        return jsonify({"ok": False, "error": "Use vault withdraw for vault buckets"}), 400

    # Validate before mutating: cap release at actual rollover balance
    all_months_pre = data.get("months", [])
    txs = data.get("txs", [])
    active_month_pre = next(
        (m for m in all_months_pre if m["id"] == mid),
        {"id": mid, "allocations": {}, "budgets": {}, "rolloverReleased": {}, "skippedBuckets": {}},
    )
    current_roll = rollover_bal(bucket, active_month_pre, all_months_pre, txs)
    if amount > current_roll + 0.005:
        return jsonify({"ok": False, "error": f"Cannot release more than the rollover balance (${current_roll:.2f})"}), 400

    month = _find_or_create_month(data, mid)
    released = month.setdefault("rolloverReleased", {})
    released[bucket_id] = float(released.get(bucket_id) or 0) + amount

    save_budget_row(session["access_token"], row_id, data)

    all_months   = data.get("months", [])
    active_month = next((m for m in all_months if m["id"] == mid), month)
    new_roll = rollover_bal(bucket, active_month, all_months, txs)
    avail    = bucket_available(bucket, active_month, all_months, txs)

    return jsonify({"ok": True, "rollover": new_roll, "avail": avail, "rts": _rts_now(data)})


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
            btype  = b.get("type", "expense")

            if btype == "vault":
                # Vaults: no transactions, balance = accumulated alloc minus withdrawals
                roll   = 0.0
                spent  = 0.0
                vault_total = vault_accumulated(b["id"], all_months)
                avail  = vault_total
            else:
                roll        = rollover_bal(b, active_month, all_months, txs)
                spent       = b_spent(active_mid, b["id"], txs)
                avail       = bucket_available(b, active_month, all_months, txs)
                vault_total = 0.0

            status  = bucket_status(alloc, budget, spent, avail)
            skipped = bool((active_month.get("skippedBuckets") or {}).get(b["id"]))
            target_amount = b.get("targetAmount") or 0

            # Progress bar
            progress_pct = 0
            if btype == "vault" and target_amount > 0:
                progress_pct = min(100, max(0, round(vault_total / target_amount * 100)))
            elif btype in ("sinking", "goal") and target_amount > 0:
                # avail = rolloverBal + alloc - spent = sinkingSaved per FORMULAS.md 3.13
                progress_pct = min(100, max(0, round(avail / target_amount * 100)))

            rows.append({
                "id":              b["id"],
                "name":            b["name"],
                "type":            btype,
                "cat_id":          b.get("catId", cid),
                "rollover":        b.get("rollover", False),
                "recurring":       b.get("recurring", False),
                "skipped":         skipped,
                "due_day":         b.get("dueDay", ""),
                "pay_freq":        b.get("payFreq", ""),
                "due_amount":      b.get("dueAmount", ""),
                "debt_account_id": b.get("debtAccountId", ""),
                "notes":           b.get("notes", "") or "",
                "target_amount":   target_amount or "",
                "target_date":     b.get("targetDate", ""),
                "contrib_freq":    b.get("contribFreq", ""),
                "default_budget":  b.get("defaultBudget", 0),
                "alloc":           alloc,
                "budget":          budget,
                "rollover_val":    roll,
                "spent":           spent,
                "avail":           avail,
                "status":          status,
                "vault_total":     vault_total,
                "progress_pct":    progress_pct,
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

    # RTS in the header always reflects TODAY's calendar month, not the viewed month.
    cur_mid_obj = next(
        (m for m in all_months if m.get("id") == current_month_id()),
        {"id": current_month_id(), "allocations": {}, "budgets": {}, "rolloverReleased": {}, "skippedBuckets": {}},
    )
    rts = ready_to_spend(cur_mid_obj, all_months, accounts, active_buckets, txs)

    debt_accounts    = [a for a in accounts if a.get("type") == "debt"]
    transfer_buckets = [
        {"id": b["id"], "name": b["name"]}
        for b in active_buckets
        if b.get("type") != "vault"
    ]

    # ── Accounts panel data ───────────────────────────────────────────────────
    accounts_display = []
    for a in accounts:
        if a.get("archived"):
            continue
        bal = acct_balance(a, txs)
        accounts_display.append({
            "id":               a["id"],
            "name":             a.get("name", ""),
            "type":             a.get("type", "budget"),
            "color":            a.get("color") or "#3a7fc1",
            "balance":          bal,
            "opening_balance":  a.get("openingBalance") or 0,
            "debt_apr":         a.get("debtAPR") or "",
            "debt_min_payment": a.get("debtMinPayment") or "",
            "credit_limit":     a.get("creditLimit") or "",
        })

    cash_accounts  = [a for a in accounts_display if a["type"] != "debt"]
    debt_accounts_display = [a for a in accounts_display if a["type"] == "debt"]
    total_cash_val = sum(a["balance"] for a in cash_accounts)
    total_debt_val = sum(a["balance"] for a in debt_accounts_display)

    vault_buckets_display = []
    for b in active_buckets:
        if b.get("type") == "vault":
            cat = next((c for c in cats if c["id"] == b.get("catId")), None)
            vault_buckets_display.append({
                "id":          b["id"],
                "name":        b.get("name", ""),
                "cat_name":    cat.get("name", "") if cat else "",
                "vault_total": vault_accumulated(b["id"], all_months),
            })
    total_vault_val = sum(v["vault_total"] for v in vault_buckets_display)

    # ── Ledger data ──────────────────────────────────────────────────────────
    acct_map   = {a["id"]: a.get("name", a["id"]) for a in accounts}
    bucket_map = {b["id"]: b.get("name", b["id"]) for b in all_buckets}

    ledger_txs = sorted(
        [t for t in txs if t.get("monthId") == active_mid],
        key=lambda t: (t.get("date") or "", t.get("id") or ""),
        reverse=True,
    )

    from datetime import date as _date, timedelta
    from itertools import groupby

    ledger_rows = []
    income_total = 0.0
    spent_total  = 0.0
    for t in ledger_txs:
        scheduled = is_scheduled(t)
        amt   = float(t.get("amount") or 0)
        ttype = t.get("type", "out")
        if not scheduled:
            if ttype == "in":
                income_total += amt
            elif ttype == "out":
                spent_total += amt
        ledger_rows.append({
            "id":          t["id"],
            "date":        t.get("date", ""),
            "desc":        t.get("desc", ""),
            "type":        ttype,
            "amount":      amt,
            "account":     acct_map.get(t.get("accountId", ""), ""),
            "to_account":  acct_map.get(t.get("toAccountId", ""), ""),
            "bucket":      bucket_map.get(t.get("bucketId", ""), ""),
            "bucket_id":   t.get("bucketId", "") or "",
            "account_id":  t.get("accountId", "") or "",
            "to_acct_id":  t.get("toAccountId", "") or "",
            "scheduled":   scheduled,
            "reconciled":  bool(t.get("reconciled")),
        })

    # Group rows by date (already sorted newest-first)
    today     = _date.today()
    yesterday = today - timedelta(days=1)

    def _date_label(date_str: str) -> str:
        try:
            d = _date.fromisoformat(date_str)
            if d == today:
                return "Today"
            if d == yesterday:
                return "Yesterday"
            return d.strftime("%A, %B %-d")
        except ValueError:
            return date_str or "—"

    ledger_groups = [
        {"date": date_str, "label": _date_label(date_str), "rows": list(rows)}
        for date_str, rows in groupby(ledger_rows, key=lambda r: r["date"])
    ]

    # Non-vault buckets eligible for expense assignment
    expense_buckets = [
        {"id": b["id"], "name": b["name"]}
        for b in active_buckets
        if b.get("type") != "vault"
    ]

    # ── Per-account transaction ledgers (all time, newest first) ─────────────
    all_txs_sorted = sorted(
        txs,
        key=lambda t: (t.get("date") or "", t.get("id") or ""),
        reverse=True,
    )
    account_ledgers = {}
    for a_disp in accounts_display:
        acct_id = a_disp["id"]
        a_txs = []
        for t in all_txs_sorted:
            if t.get("monthId") != active_mid:
                continue
            is_from     = t.get("accountId") == acct_id
            is_to       = t.get("toAccountId") == acct_id and t.get("type") == "xfr"
            is_debt_pay = t.get("debtPaymentAccountId") == acct_id and not is_from
            if not (is_from or is_to or is_debt_pay):
                continue
            ttype = t.get("type", "out")
            incoming = is_to or is_debt_pay
            a_txs.append({
                "id":        t["id"],
                "date":      t.get("date") or "",
                "desc":      t.get("desc") or "",
                "type":      ttype,
                "amount":    float(t.get("amount") or 0),
                "scheduled": is_scheduled(t),
                "incoming":  incoming,
            })
        account_ledgers[acct_id] = [
            {"date": d, "label": _date_label(d), "rows": list(rows)}
            for d, rows in groupby(a_txs, key=lambda r: r["date"])
        ]

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
        accounts=accounts,
        debt_accounts=debt_accounts,
        transfer_buckets=transfer_buckets,
        ledger_groups=ledger_groups,
        ledger_income=income_total,
        ledger_spent=spent_total,
        expense_buckets=expense_buckets,
        cash_accounts=cash_accounts,
        debt_accounts_display=debt_accounts_display,
        total_cash_val=total_cash_val,
        total_debt_val=total_debt_val,
        vault_buckets_display=vault_buckets_display,
        total_vault_val=total_vault_val,
        account_ledgers=account_ledgers,
    )


@app.route("/api/add-transaction", methods=["POST"])
def api_add_transaction():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body    = request.get_json(silent=True) or {}
    ttype   = body.get("type", "out")          # in | out | xfr
    date    = (body.get("date") or "").strip()
    desc    = (body.get("desc") or "").strip()
    amount  = float(body.get("amount") or 0)
    acct_id = (body.get("account_id") or "").strip()
    bkt_id  = (body.get("bucket_id") or "").strip()
    to_acct = (body.get("to_account_id") or "").strip()

    if not date:
        return jsonify({"ok": False, "error": "Date required"}), 400
    if not acct_id:
        return jsonify({"ok": False, "error": "Account required"}), 400
    if amount <= 0:
        return jsonify({"ok": False, "error": "Amount must be positive"}), 400
    if ttype == "xfr" and not to_acct:
        return jsonify({"ok": False, "error": "Destination account required for transfer"}), 400

    row_id, data = load_budget_row(session["access_token"])
    if row_id is None:
        return jsonify({"ok": False, "error": "No data row found"}), 404

    mid = _date_to_month_id(date)
    _find_or_create_month(data, mid)

    tx = {
        "id":          _new_id("tx"),
        "accountId":   acct_id,
        "monthId":     mid,
        "desc":        desc,
        "amount":      amount,
        "type":        ttype,
        "date":        date,
        "reconciled":  False,
        "recurring":   False,
    }
    if ttype == "out" and bkt_id:
        tx["bucketId"] = bkt_id
    if ttype == "xfr":
        tx["toAccountId"] = to_acct

    data.setdefault("txs", []).append(tx)
    save_budget_row(session["access_token"], row_id, data)
    return jsonify({"ok": True, "tx_id": tx["id"], "month_id": mid})


@app.route("/api/edit-transaction", methods=["POST"])
def api_edit_transaction():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body   = request.get_json(silent=True) or {}
    tx_id  = (body.get("id") or "").strip()
    field  = (body.get("field") or "").strip()
    value  = body.get("value")

    row_id, data = load_budget_row(session["access_token"])
    if row_id is None:
        return jsonify({"ok": False, "error": "No data row found"}), 404

    tx = next((t for t in data.get("txs", []) if t["id"] == tx_id), None)
    if not tx:
        return jsonify({"ok": False, "error": "Transaction not found"}), 404

    if field == "desc":
        tx["desc"] = str(value or "").strip()
    elif field == "amount":
        tx["amount"] = float(value or 0)
    elif field == "date":
        tx["date"] = str(value or "").strip()
        tx["monthId"] = _date_to_month_id(tx["date"])
        _find_or_create_month(data, tx["monthId"])
    elif field == "bucket_id":
        tx["bucketId"] = str(value or "") or None
    elif field == "account_id":
        tx["accountId"] = str(value or "")
    elif field == "to_account_id":
        if value:
            tx["toAccountId"] = str(value)
        else:
            tx.pop("toAccountId", None)
    else:
        return jsonify({"ok": False, "error": f"Unknown field: {field}"}), 400

    save_budget_row(session["access_token"], row_id, data)
    return jsonify({"ok": True})


@app.route("/api/delete-transaction", methods=["POST"])
def api_delete_transaction():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body  = request.get_json(silent=True) or {}
    tx_id = (body.get("id") or "").strip()

    row_id, data = load_budget_row(session["access_token"])
    if row_id is None:
        return jsonify({"ok": False, "error": "No data row found"}), 404

    before = len(data.get("txs", []))
    data["txs"] = [t for t in data.get("txs", []) if t["id"] != tx_id]
    if len(data["txs"]) == before:
        return jsonify({"ok": False, "error": "Transaction not found"}), 404

    save_budget_row(session["access_token"], row_id, data)
    return jsonify({"ok": True})


@app.route("/api/add-account", methods=["POST"])
def api_add_account():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body    = request.get_json(silent=True) or {}
    name    = (body.get("name") or "").strip()
    atype   = body.get("type", "budget")
    color   = body.get("color") or "#3a7fc1"
    opening = float(body.get("opening_balance") or 0)

    if not name:
        return jsonify({"ok": False, "error": "Account name required"}), 400

    row_id, data = load_budget_row(session["access_token"])
    if row_id is None:
        return jsonify({"ok": False, "error": "No data row found"}), 404

    acct_id = _new_id("acct")
    data.setdefault("accounts", []).append({
        "id":             acct_id,
        "name":           name,
        "type":           atype,
        "color":          color,
        "openingBalance": opening,
        "archived":       False,
    })

    save_budget_row(session["access_token"], row_id, data)
    return jsonify({"ok": True, "acct_id": acct_id})


@app.route("/api/save-account", methods=["POST"])
def api_save_account():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body    = request.get_json(silent=True) or {}
    acct_id = (body.get("id") or "").strip()
    field   = (body.get("field") or "").strip()
    value   = body.get("value")

    row_id, data = load_budget_row(session["access_token"])
    if row_id is None:
        return jsonify({"ok": False, "error": "No data row found"}), 404

    acct = next((a for a in data.get("accounts", []) if a["id"] == acct_id), None)
    if not acct:
        return jsonify({"ok": False, "error": "Account not found"}), 404

    if field == "name":
        acct["name"] = str(value or "").strip()
    elif field == "type":
        acct["type"] = str(value or "budget")
    elif field == "color":
        acct["color"] = str(value or "")
    elif field == "opening_balance":
        acct["openingBalance"] = float(value or 0)
    elif field == "debt_apr":
        acct["debtAPR"] = float(value) if value not in (None, "", "0", 0) else None
    elif field == "debt_min_payment":
        acct["debtMinPayment"] = float(value) if value not in (None, "", "0", 0) else None
    elif field == "credit_limit":
        acct["creditLimit"] = float(value) if value not in (None, "", "0", 0) else None
    elif field == "archived":
        acct["archived"] = True
    else:
        return jsonify({"ok": False, "error": f"Unknown field: {field}"}), 400

    save_budget_row(session["access_token"], row_id, data)
    return jsonify({"ok": True})


@app.route("/api/debt-payment", methods=["POST"])
def api_debt_payment():
    """Record a debt payment: 'out' tx on source account, debtPaymentAccountId set."""
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body         = request.get_json(silent=True) or {}
    debt_id      = (body.get("debt_id") or "").strip()
    from_acct_id = (body.get("from_account_id") or "").strip()
    amount       = float(body.get("amount") or 0)
    date         = (body.get("date") or "").strip()
    bucket_id    = (body.get("bucket_id") or "").strip()

    if not debt_id or not from_acct_id:
        return jsonify({"ok": False, "error": "Debt account and source account required"}), 400
    if amount <= 0:
        return jsonify({"ok": False, "error": "Amount must be positive"}), 400
    if not date:
        return jsonify({"ok": False, "error": "Date required"}), 400

    row_id, data = load_budget_row(session["access_token"])
    if row_id is None:
        return jsonify({"ok": False, "error": "No data row found"}), 404

    all_accounts = data.get("accounts", [])
    debt_acct = next((a for a in all_accounts if a["id"] == debt_id), None)
    src_acct  = next((a for a in all_accounts if a["id"] == from_acct_id), None)
    if not debt_acct or debt_acct.get("type") != "debt":
        return jsonify({"ok": False, "error": "Debt account not found"}), 400
    if not src_acct:
        return jsonify({"ok": False, "error": "Source account not found"}), 400

    mid = _date_to_month_id(date)
    _find_or_create_month(data, mid)

    tx = {
        "id":                   _new_id("tx"),
        "accountId":            from_acct_id,
        "debtPaymentAccountId": debt_id,
        "monthId":              mid,
        "desc":                 f"Payment — {debt_acct.get('name', '')}",
        "amount":               amount,
        "type":                 "out",
        "date":                 date,
        "reconciled":           False,
        "recurring":            False,
    }
    if bucket_id:
        tx["bucketId"] = bucket_id

    data.setdefault("txs", []).append(tx)
    save_budget_row(session["access_token"], row_id, data)

    txs_new      = data.get("txs", [])
    new_debt_bal = acct_balance(debt_acct, txs_new)
    new_src_bal  = acct_balance(src_acct, txs_new)

    return jsonify({"ok": True, "tx_id": tx["id"],
                    "debt_bal": new_debt_bal, "src_bal": new_src_bal, "rts": _rts_now(data)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_ENV") == "development")
