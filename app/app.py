import os
import traceback
import collections
import time as _time
from datetime import date, timedelta
import calendar as _cal
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

# ── Coach AI rate limit state (15 RPM, 1500 RPD) ─────────────────────────────
_coach_rpm_times = collections.deque()  # timestamps of recent requests
_coach_rpd_count = 0
_coach_rpd_date = None

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

SUPABASE_URL     = os.environ["SUPABASE_URL"]
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


# ── Supabase helpers ──────────────────────────────────────────────────────────

def _db(access_token: str | None = None) -> Client:
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    if access_token:
        client.postgrest.auth(access_token)
    return client


def _uid() -> str:
    return session.get("user_id", "")


def _tok() -> str:
    return session.get("access_token", "")


def logged_in() -> bool:
    return "access_token" in session and "user_id" in session


# ── Data loader: relational tables → canonical dict ───────────────────────────

def _load(uid: str, token: str) -> dict:
    """Assemble the full data dict from relational tables.
    Returns the same structure the rest of the app (formulas, routes) expects."""
    db = _db(token)

    accounts_raw   = db.table("bcc_accounts").select("*").eq("user_id", uid).execute().data or []
    cats_raw       = db.table("bcc_categories").select("*").eq("user_id", uid).execute().data or []
    buckets_raw    = db.table("bcc_buckets").select("*").eq("user_id", uid).execute().data or []
    txs_raw        = db.table("bcc_transactions").select("*").eq("user_id", uid).execute().data or []
    months_raw     = db.table("bcc_months").select("*").eq("user_id", uid).execute().data or []
    allocs_raw     = db.table("bcc_month_allocations").select("*").eq("user_id", uid).execute().data or []
    budgets_raw    = db.table("bcc_month_budgets").select("*").eq("user_id", uid).execute().data or []
    rollrel_raw    = db.table("bcc_month_rollover_released").select("*").eq("user_id", uid).execute().data or []
    skipped_raw    = db.table("bcc_month_skipped").select("*").eq("user_id", uid).execute().data or []
    vaultwd_raw    = db.table("bcc_month_vault_withdrawals").select("*").eq("user_id", uid).execute().data or []
    paychecks_raw  = db.table("bcc_paychecks").select("*").eq("user_id", uid).execute().data or []
    rules_raw      = db.table("bcc_allocation_rules").select("*").eq("user_id", uid).execute().data or []
    vtransfers_raw = db.table("bcc_vault_transfers").select("*").eq("user_id", uid).execute().data or []

    # Accounts (snake_case → camelCase for formulas)
    accounts = [{
        "id": a["id"], "name": a["name"], "type": a["type"],
        "color": a["color"], "openingBalance": float(a.get("opening_balance") or 0),
        "archived": a.get("archived", False),
        "debtAPR": a.get("debt_apr"), "debtMinPayment": a.get("debt_min_payment"),
        "creditLimit": a.get("credit_limit"),
    } for a in sorted(accounts_raw, key=lambda x: x.get("sort_order", 0))]

    # Categories
    cats = [{
        "id": c["id"], "name": c["name"], "color": c.get("color", ""),
        "order": c.get("sort_order", 0), "archived": c.get("archived", False),
    } for c in sorted(cats_raw, key=lambda x: x.get("sort_order", 0))]

    # Buckets
    buckets = [{
        "id": b["id"], "catId": b.get("cat_id") or "",
        "name": b["name"], "type": b.get("type", "expense"),
        "rollover": b.get("rollover", False), "recurring": b.get("recurring", False),
        "archived": b.get("archived", False),
        "defaultBudget": float(b.get("default_budget") or 0),
        "order": b.get("sort_order", 0), "notes": b.get("notes"),
        "dueDay": b.get("due_day"), "payFreq": b.get("pay_freq"),
        "dueAmount": b.get("due_amount"), "debtAccountId": b.get("debt_account_id"),
        "targetAmount": b.get("target_amount"), "targetDate": b.get("target_date"),
        "contribFreq": b.get("contrib_freq"),
    } for b in sorted(buckets_raw, key=lambda x: x.get("sort_order", 0))]

    # Transactions
    txs = [{
        "id": t["id"], "accountId": t.get("account_id") or "",
        "monthId": t.get("month_id") or "",
        "desc": t.get("description") or "",
        "amount": float(t.get("amount") or 0),
        "type": t.get("type", "out"),
        "date": str(t.get("date") or ""),
        "reconciled": t.get("reconciled", False),
        "recurring": t.get("recurring", False),
        "bucketId": t.get("bucket_id"),
        "toAccountId": t.get("to_account_id"),
        "incomeType": t.get("income_type"),
        "debtPaymentAccountId": t.get("debt_payment_account_id"),
    } for t in txs_raw]

    # Build month sub-dicts indexed by month_id
    alloc_by_mid   = {}
    for r in allocs_raw:
        alloc_by_mid.setdefault(r["month_id"], {})[r["bucket_id"]] = float(r["amount"])

    budget_by_mid  = {}
    for r in budgets_raw:
        budget_by_mid.setdefault(r["month_id"], {})[r["bucket_id"]] = float(r["amount"])

    rollrel_by_mid = {}
    for r in rollrel_raw:
        rollrel_by_mid.setdefault(r["month_id"], {})[r["bucket_id"]] = float(r["amount"])

    skipped_by_mid = {}
    for r in skipped_raw:
        skipped_by_mid.setdefault(r["month_id"], {})[r["bucket_id"]] = True

    vaultwd_by_mid = {}
    for r in vaultwd_raw:
        vaultwd_by_mid.setdefault(r["month_id"], {})[r["bucket_id"]] = float(r["amount"])

    months = [{
        "id": m["id"], "year": m["year"], "month": m["month"], "label": m["label"],
        "allocations":      alloc_by_mid.get(m["id"], {}),
        "budgets":          budget_by_mid.get(m["id"], {}),
        "rolloverReleased": rollrel_by_mid.get(m["id"], {}),
        "skippedBuckets":   skipped_by_mid.get(m["id"], {}),
        "vaultWithdrawals": vaultwd_by_mid.get(m["id"], {}),
    } for m in months_raw]

    # Paychecks
    paychecks = [{
        "id": p["id"], "label": p["label"], "amount": float(p.get("amount") or 0),
        "freq": p.get("freq", 14), "anchorDate": p.get("anchor_date") or "",
    } for p in sorted(paychecks_raw, key=lambda x: x.get("sort_order", 0))]

    # Allocation rules
    alloc_rules = [{
        "id": r["id"], "name": r["name"],
        "ruleType": r.get("rule_type", "internal"),
        "type": r.get("value_type", "fixed"),
        "value": float(r.get("value") or 0),
        "bucketId": r.get("bucket_id"), "active": r.get("active", True),
    } for r in sorted(rules_raw, key=lambda x: x.get("sort_order", 0))]

    # Vault transfers
    vault_transfers = [{
        "id": v["id"], "fromBucketId": v["from_bucket_id"],
        "toBucketId": v["to_bucket_id"], "amount": float(v["amount"]),
        "monthId": v["month_id"], "reason": v.get("reason", ""),
    } for v in vtransfers_raw]

    return {
        "accounts": accounts, "cats": cats, "buckets": buckets,
        "txs": txs, "months": months, "paychecks": paychecks,
        "allocationRules": alloc_rules, "vaultTransfers": vault_transfers,
    }


# ── Targeted save helpers ─────────────────────────────────────────────────────

def _ensure_month(uid: str, token: str, mid: str) -> None:
    year, m0 = parse_month_id(mid)
    _db(token).table("bcc_months").upsert({
        "id": mid, "user_id": uid, "year": year, "month": m0,
        "label": f"{MONTH_NAMES[m0]} {year}",
    }, on_conflict="id,user_id").execute()


def _upsert_alloc(uid: str, token: str, mid: str, bid: str, amount: float) -> None:
    _db(token).table("bcc_month_allocations").upsert(
        {"user_id": uid, "month_id": mid, "bucket_id": bid, "amount": amount},
        on_conflict="user_id,month_id,bucket_id",
    ).execute()


def _upsert_budget(uid: str, token: str, mid: str, bid: str, amount: float) -> None:
    _db(token).table("bcc_month_budgets").upsert(
        {"user_id": uid, "month_id": mid, "bucket_id": bid, "amount": amount},
        on_conflict="user_id,month_id,bucket_id",
    ).execute()


def _upsert_rollover_released(uid: str, token: str, mid: str, bid: str, amount: float) -> None:
    _db(token).table("bcc_month_rollover_released").upsert(
        {"user_id": uid, "month_id": mid, "bucket_id": bid, "amount": amount},
        on_conflict="user_id,month_id,bucket_id",
    ).execute()


def _set_skipped(uid: str, token: str, mid: str, bid: str, skipped: bool) -> None:
    db = _db(token)
    if skipped:
        db.table("bcc_month_skipped").upsert(
            {"user_id": uid, "month_id": mid, "bucket_id": bid},
            on_conflict="user_id,month_id,bucket_id",
        ).execute()
    else:
        db.table("bcc_month_skipped").delete().eq("user_id", uid).eq("month_id", mid).eq("bucket_id", bid).execute()


def _upsert_vault_withdrawal(uid: str, token: str, mid: str, bid: str, amount: float) -> None:
    _db(token).table("bcc_month_vault_withdrawals").upsert(
        {"user_id": uid, "month_id": mid, "bucket_id": bid, "amount": amount},
        on_conflict="user_id,month_id,bucket_id",
    ).execute()


def _save_account(uid: str, token: str, acct: dict) -> None:
    _db(token).table("bcc_accounts").update({
        "name": acct.get("name"), "type": acct.get("type", "budget"),
        "color": acct.get("color", "#3a7fc1"),
        "opening_balance": float(acct.get("openingBalance") or 0),
        "debt_apr": acct.get("debtAPR"),
        "debt_min_payment": acct.get("debtMinPayment"),
        "credit_limit": acct.get("creditLimit"),
        "archived": acct.get("archived", False),
    }).eq("id", acct["id"]).eq("user_id", uid).execute()


def _insert_account(uid: str, token: str, acct: dict) -> None:
    existing = (_db(token).table("bcc_accounts")
                .select("sort_order").eq("user_id", uid)
                .order("sort_order", desc=True).limit(1).execute().data or [])
    sort_order = (existing[0]["sort_order"] + 1) if existing else 1
    _db(token).table("bcc_accounts").insert({
        "id": acct["id"], "user_id": uid,
        "name": acct["name"], "type": acct.get("type", "budget"),
        "color": acct.get("color", "#3a7fc1"),
        "opening_balance": float(acct.get("openingBalance") or 0),
        "archived": False, "sort_order": sort_order,
    }).execute()


def _save_bucket(uid: str, token: str, b: dict) -> None:
    _db(token).table("bcc_buckets").update({
        "name": b.get("name"), "type": b.get("type", "expense"),
        "cat_id": b.get("catId") or None,
        "rollover": b.get("rollover", False),
        "recurring": b.get("recurring", False),
        "archived": b.get("archived", False),
        "due_day": str(b["dueDay"]) if b.get("dueDay") is not None else None,
        "pay_freq": b.get("payFreq"), "due_amount": b.get("dueAmount"),
        "debt_account_id": b.get("debtAccountId"),
        "target_amount": b.get("targetAmount"), "target_date": b.get("targetDate"),
        "contrib_freq": b.get("contribFreq"),
        "default_budget": float(b.get("defaultBudget") or 0),
        "notes": b.get("notes"),
    }).eq("id", b["id"]).eq("user_id", uid).execute()


def _insert_bucket(uid: str, token: str, b: dict) -> None:
    cat_id = b.get("catId") or None
    existing = (_db(token).table("bcc_buckets")
                .select("sort_order").eq("user_id", uid).eq("cat_id", cat_id)
                .order("sort_order", desc=True).limit(1).execute().data or [])
    sort_order = (existing[0]["sort_order"] + 1) if existing else 1
    _db(token).table("bcc_buckets").insert({
        "id": b["id"], "user_id": uid, "cat_id": cat_id,
        "name": b["name"], "type": b.get("type", "expense"),
        "rollover": b.get("rollover", False),
        "recurring": b.get("recurring", False),
        "archived": False,
        "default_budget": float(b.get("defaultBudget") or 0),
        "sort_order": sort_order,
    }).execute()


def _insert_category(uid: str, token: str, cat: dict) -> None:
    existing = (_db(token).table("bcc_categories")
                .select("sort_order").eq("user_id", uid)
                .order("sort_order", desc=True).limit(1).execute().data or [])
    sort_order = (existing[0]["sort_order"] + 1) if existing else 1
    _db(token).table("bcc_categories").insert({
        "id": cat["id"], "user_id": uid,
        "name": cat["name"], "color": cat.get("color", ""),
        "archived": False, "sort_order": sort_order,
    }).execute()


def _save_category(uid: str, token: str, cat: dict) -> None:
    _db(token).table("bcc_categories").update({
        "name": cat.get("name", ""),
        "archived": cat.get("archived", False),
    }).eq("id", cat["id"]).eq("user_id", uid).execute()


def _insert_tx(uid: str, token: str, tx: dict) -> None:
    _db(token).table("bcc_transactions").insert({
        "id": tx["id"], "user_id": uid,
        "date": tx["date"], "description": tx.get("desc"),
        "type": tx.get("type", "out"), "amount": float(tx["amount"]),
        "month_id": tx["monthId"],
        "bucket_id": tx.get("bucketId"),
        "account_id": tx.get("accountId"),
        "to_account_id": tx.get("toAccountId"),
        "debt_payment_account_id": tx.get("debtPaymentAccountId"),
        "income_type": tx.get("incomeType"),
        "reconciled": tx.get("reconciled", False),
        "recurring": tx.get("recurring", False),
    }).execute()


def _save_tx(uid: str, token: str, tx: dict) -> None:
    _db(token).table("bcc_transactions").update({
        "date": tx.get("date"),
        "description": tx.get("desc"),
        "amount": float(tx.get("amount") or 0),
        "month_id": tx.get("monthId"),
        "bucket_id": tx.get("bucketId"),
        "account_id": tx.get("accountId"),
        "to_account_id": tx.get("toAccountId"),
        "income_type": tx.get("incomeType"),
    }).eq("id", tx["id"]).eq("user_id", uid).execute()


def _delete_tx(uid: str, token: str, tx_id: str) -> bool:
    res = _db(token).table("bcc_transactions").delete().eq("id", tx_id).eq("user_id", uid).execute()
    return bool(res.data)


# ── Utility helpers ───────────────────────────────────────────────────────────

def _date_to_month_id(date_str: str) -> str:
    from datetime import date as _date
    d = _date.fromisoformat(date_str)
    return month_id(d.year, d.month - 1)


def _find_or_create_month(data: dict, mid: str) -> dict:
    """Return (or create in-memory) the month dict for mid."""
    months = data.setdefault("months", [])
    m = next((m for m in months if m["id"] == mid), None)
    if m is None:
        m = {"id": mid, "allocations": {}, "budgets": {}, "rolloverReleased": {},
             "skippedBuckets": {}, "vaultWithdrawals": {}}
        months.append(m)
    return m


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


def _due_info(due_day, active_mid: str, status: str) -> dict:
    """Return {label, urgency} for a bucket's due date display.
    urgency: 'overdue' | 'today' | 'soon' (≤7d) | 'upcoming' (≤14d) | 'far' | ''
    label:   e.g. 'OVERDUE 3D' | 'DUE TODAY' | 'DUE 5D' | '' (empty when already paid/funded)
    """
    from datetime import date as _date
    if not due_day or status in ("PAID", "FUNDED", "OVER"):
        return {"label": "", "urgency": ""}

    today = _date.today()
    year, month_0 = parse_month_id(active_mid)
    month = month_0 + 1  # 1-indexed

    # Resolve due day
    raw = str(due_day).strip().lower()
    if raw == "eom":
        import calendar
        day = calendar.monthrange(year, month)[1]
    else:
        try:
            day = int(raw)
        except ValueError:
            return {"label": "", "urgency": ""}

    import calendar as _cal
    last_day = _cal.monthrange(year, month)[1]
    day = min(day, last_day)

    try:
        due_date = _date(year, month, day)
    except ValueError:
        return {"label": "", "urgency": ""}

    delta = (due_date - today).days

    if delta < 0:
        urgency = "overdue"
        label   = f"OVERDUE {abs(delta)}D" if abs(delta) != 1 else "OVERDUE 1D"
    elif delta == 0:
        urgency = "today"
        label   = "DUE TODAY"
    elif delta <= 7:
        urgency = "soon"
        label   = f"DUE {delta}D"
    elif delta <= 14:
        urgency = "upcoming"
        label   = f"DUE {delta}D"
    else:
        urgency = "far"
        label   = f"DUE {delta}D"

    return {"label": label, "urgency": urgency}


def _new_id(prefix: str) -> str:
    import random, string
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"{prefix}_{suffix}"


# ── Live state (unchanged — formulas work on the same dict) ───────────────────

def _rts_now(data: dict) -> float:
    all_months     = data.get("months", [])
    accounts       = data.get("accounts", [])
    txs            = data.get("txs", [])
    active_buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    cur_mid        = current_month_id()
    cur_month      = next(
        (m for m in all_months if m.get("id") == cur_mid),
        {"id": cur_mid, "allocations": {}, "budgets": {}, "rolloverReleased": {},
         "skippedBuckets": {}, "vaultWithdrawals": {}},
    )
    return ready_to_spend(cur_month, all_months, accounts, active_buckets, txs)


def _live_state(data: dict, active_mid: str) -> dict:
    all_months     = data.get("months", [])
    accounts       = data.get("accounts", [])
    txs            = data.get("txs", [])
    cats           = data.get("cats", [])
    active_buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    active_month   = next(
        (m for m in all_months if m.get("id") == active_mid),
        {"id": active_mid, "allocations": {}, "budgets": {}, "rolloverReleased": {},
         "skippedBuckets": {}, "vaultWithdrawals": {}},
    )

    bucket_avails, bucket_allocs, bucket_rollover = {}, {}, {}
    bucket_spent, vault_totals, bucket_statuses   = {}, {}, {}
    bucket_due = {}  # {bid: {label, urgency}}

    for b in active_buckets:
        bid    = b["id"]
        alloc  = float((active_month.get("allocations") or {}).get(bid, 0))
        budget = float((active_month.get("budgets") or {}).get(bid, 0))
        bucket_allocs[bid] = alloc
        if b.get("type") == "vault":
            total = vault_accumulated(bid, all_months)
            vault_totals[bid]    = total
            bucket_avails[bid]   = total
            bucket_statuses[bid] = ""
            bucket_due[bid]      = {"label": "", "urgency": ""}
        else:
            avail = bucket_available(b, active_month, all_months, txs)
            spent = sum(
                t.get("amount", 0) for t in txs
                if t.get("bucketId") == bid and t.get("type") == "out"
                and t.get("monthId") == active_mid and not is_scheduled(t)
            )
            roll = rollover_bal(b, active_month, all_months, txs)
            bucket_avails[bid]   = avail
            bucket_rollover[bid] = roll
            bucket_spent[bid]    = spent
            status = bucket_status(alloc, budget, spent, avail)
            bucket_statuses[bid] = status
            bucket_due[bid]      = _due_info(b.get("dueDay"), active_mid, status)

    cat_totals = {}
    grand = dict(alloc=0.0, budget=0.0, rollover=0.0, spent=0.0, avail=0.0)
    for cat in cats:
        if cat.get("archived"):
            continue
        cid = cat["id"]
        cat_buckets = [b for b in active_buckets if b.get("catId") == cid]
        if not cat_buckets:
            continue
        t = dict(alloc=0.0, budget=0.0, rollover=0.0, spent=0.0, avail=0.0)
        for b in cat_buckets:
            bid = b["id"]
            t["alloc"]  += float((active_month.get("allocations") or {}).get(bid, 0))
            t["budget"] += float((active_month.get("budgets") or {}).get(bid, 0))
            t["avail"]  += bucket_avails.get(bid, 0)
            if b.get("type") != "vault":
                t["rollover"] += bucket_rollover.get(bid, 0)
                t["spent"]    += bucket_spent.get(bid, 0)
        cat_totals[cid] = t
        for k in grand:
            grand[k] += t[k]

    ledger_income = sum(
        float(t.get("amount", 0)) for t in txs
        if t.get("monthId") == active_mid and t.get("type") == "in" and not is_scheduled(t)
    )
    ledger_out = sum(
        float(t.get("amount", 0)) for t in txs
        if t.get("monthId") == active_mid and t.get("type") == "out" and not is_scheduled(t)
    )

    return {
        "rts":              _rts_now(data),
        "bucket_avails":    bucket_avails,
        "bucket_allocs":    bucket_allocs,
        "bucket_rollover":  bucket_rollover,
        "bucket_spent":     bucket_spent,
        "vault_totals":     vault_totals,
        "bucket_statuses":  bucket_statuses,
        "bucket_due":       bucket_due,
        "cat_totals":       cat_totals,
        "grand_totals":     grand,
        "ledger_totals":    {"income": ledger_income, "spent": ledger_out},
        "account_balances": {a["id"]: acct_balance(a, txs) for a in accounts if not a.get("archived")},
    }


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    if not logged_in():
        return redirect(url_for("login"))
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        try:
            sb   = _db()
            resp = sb.auth.sign_in_with_password({"email": email, "password": password})
            session["access_token"] = resp.session.access_token
            session["user_id"]      = resp.user.id
            session["user_email"]   = resp.user.email
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


# ── API: state ────────────────────────────────────────────────────────────────

@app.route("/api/state")
def api_state():
    if not logged_in():
        return jsonify({"ok": False}), 401
    active_mid = request.args.get("month") or current_month_id()
    data = _load(_uid(), _tok())
    return jsonify({"ok": True, **_live_state(data, active_mid)})


# ── API: fragment helpers ─────────────────────────────────────────────────────

def _bucket_row_ctx(b: dict, active_month: dict, all_months: list, txs: list, active_mid: str) -> dict:
    btype = b.get("type", "expense")
    alloc  = float((active_month.get("allocations") or {}).get(b["id"], 0))
    budget = float((active_month.get("budgets") or {}).get(b["id"], 0))

    if btype == "vault":
        vault_total = vault_accumulated(b["id"], all_months)
        roll, spent, avail = 0.0, 0.0, vault_total
    else:
        vault_total = 0.0
        roll  = rollover_bal(b, active_month, all_months, txs)
        spent = sum(t.get("amount", 0) for t in txs
                    if t.get("bucketId") == b["id"] and t.get("type") == "out"
                    and t.get("monthId") == active_mid and not is_scheduled(t))
        avail = bucket_available(b, active_month, all_months, txs)

    target_amount = b.get("targetAmount") or 0
    progress_pct  = 0
    if btype == "vault" and target_amount > 0:
        progress_pct = min(100, max(0, round(vault_total / target_amount * 100)))
    elif btype in ("sinking", "goal") and target_amount > 0:
        progress_pct = min(100, max(0, round(avail / target_amount * 100)))

    skipped = bool((active_month.get("skippedBuckets") or {}).get(b["id"]))
    status  = bucket_status(alloc, budget, spent, avail)
    due     = _due_info(b.get("dueDay"), active_mid, status)

    return {
        "id": b["id"], "name": b.get("name", ""), "type": btype,
        "cat_id": b.get("catId", ""), "rollover": b.get("rollover", False),
        "recurring": b.get("recurring", False), "skipped": skipped,
        "due_day": b.get("dueDay", "") or "", "pay_freq": b.get("payFreq", "") or "",
        "due_amount": b.get("dueAmount", "") or "", "debt_account_id": b.get("debtAccountId", "") or "",
        "notes": b.get("notes", "") or "", "target_amount": target_amount,
        "target_date": b.get("targetDate", "") or "", "contrib_freq": b.get("contribFreq", "") or "",
        "default_budget": b.get("defaultBudget", 0),
        "alloc": alloc, "budget": budget, "rollover_val": roll, "spent": spent,
        "avail": avail, "status": status, "vault_total": vault_total,
        "progress_pct": progress_pct,
        "due_label": due["label"], "due_urgency": due["urgency"],
    }


@app.route("/api/fragment/bucket", methods=["POST"])
def api_fragment_bucket():
    if not logged_in():
        return jsonify({"ok": False}), 401
    body      = request.get_json(silent=True) or {}
    bucket_id = (body.get("bucket_id") or "").strip()
    active_mid = (body.get("active_mid") or "").strip() or current_month_id()

    data = _load(_uid(), _tok())
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bucket_id), None)
    if not bucket:
        return jsonify({"ok": False, "error": "Bucket not found"}), 404

    all_months     = data.get("months", [])
    txs            = data.get("txs", [])
    active_buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    cats_sorted    = sorted(data.get("cats", []), key=lambda c: c.get("order", 0))
    active_month   = next(
        (m for m in all_months if m.get("id") == active_mid),
        {"id": active_mid, "allocations": {}, "budgets": {}, "rolloverReleased": {},
         "skippedBuckets": {}, "vaultWithdrawals": {}},
    )

    b_ctx = _bucket_row_ctx(bucket, active_month, all_months, txs, active_mid)
    debt_accounts    = [a for a in data.get("accounts", []) if a.get("type") == "debt" and not a.get("archived")]
    transfer_buckets = [{"id": b["id"], "name": b.get("name", "")} for b in active_buckets if b.get("type") != "vault"]

    html = render_template("_frag_bucket.html",
        b=b_ctx, group_id=bucket.get("catId", ""), active_mid=active_mid,
        all_cats=cats_sorted, debt_accounts=debt_accounts, transfer_buckets=transfer_buckets)
    return jsonify({"ok": True, "html": html})


@app.route("/api/fragment/account", methods=["POST"])
def api_fragment_account():
    if not logged_in():
        return jsonify({"ok": False}), 401
    body      = request.get_json(silent=True) or {}
    acct_id   = (body.get("acct_id") or "").strip()
    active_mid = (body.get("active_mid") or "").strip() or current_month_id()

    data    = _load(_uid(), _tok())
    accounts = data.get("accounts", [])
    acct = next((a for a in accounts if a["id"] == acct_id), None)
    if not acct:
        return jsonify({"ok": False, "error": "Account not found"}), 404

    txs = data.get("txs", [])
    bal = acct_balance(acct, txs)

    from datetime import date as _date, timedelta
    from itertools import groupby as _groupby

    today     = _date.today()
    yesterday = today - timedelta(days=1)

    def _date_label(ds):
        try:
            d = _date.fromisoformat(ds)
            if d == today:     return "Today"
            if d == yesterday: return "Yesterday"
            return d.strftime("%A, %B %-d")
        except Exception:
            return ds or "—"

    a_ctx = {
        "id": acct["id"], "name": acct.get("name", ""), "type": acct.get("type", "budget"),
        "color": acct.get("color") or "#3a7fc1", "balance": bal,
        "opening_balance": acct.get("openingBalance") or 0,
        "debt_apr": acct.get("debtAPR") if acct.get("debtAPR") is not None else "",
        "debt_min_payment": acct.get("debtMinPayment") if acct.get("debtMinPayment") is not None else "",
        "credit_limit": acct.get("creditLimit") if acct.get("creditLimit") is not None else "",
    }

    a_txs = sorted(
        [t for t in txs if t.get("monthId") == active_mid
         and (t.get("accountId") == acct_id
              or (t.get("toAccountId") == acct_id and t.get("type") == "xfr")
              or (t.get("debtPaymentAccountId") == acct_id))],
        key=lambda t: (t.get("date") or "", t.get("id") or ""),
        reverse=True,
    )
    ledger = [
        {"date": d, "label": _date_label(d), "rows": [
            {"id": t["id"], "date": t.get("date",""), "desc": t.get("desc",""),
             "type": t.get("type","out"), "amount": float(t.get("amount",0)),
             "scheduled": is_scheduled(t),
             "incoming": t.get("toAccountId") == acct_id
                         or (t.get("debtPaymentAccountId") == acct_id and t.get("accountId") != acct_id)}
            for t in rows
        ]}
        for d, rows in _groupby(a_txs, key=lambda t: t.get("date",""))
    ]

    active_buckets  = [b for b in data.get("buckets", []) if not b.get("archived")]
    cash_accounts   = [a for a in accounts if not a.get("archived") and a.get("type") != "debt"]
    expense_buckets = [{"id": b["id"], "name": b["name"]} for b in active_buckets if b.get("type") != "vault"]

    html = render_template("_frag_account.html",
        a=a_ctx, active_mid=active_mid,
        account_ledgers={acct_id: ledger},
        cash_accounts=cash_accounts,
        expense_buckets=expense_buckets)
    return jsonify({"ok": True, "html": html})


# ── API: bucket save ──────────────────────────────────────────────────────────

@app.route("/api/save", methods=["POST"])
def api_save():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body  = request.get_json(silent=True) or {}
    field = body.get("field", "")
    bid   = body.get("id", "")
    value = body.get("value")
    mid   = body.get("month", "")
    uid, tok = _uid(), _tok()

    data   = _load(uid, tok)
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bid), None)

    if field == "cat_name":
        cat = next((c for c in data.get("cats", []) if c["id"] == bid), None)
        if cat:
            cat["name"] = str(value or "").strip()
            _save_category(uid, tok, cat)

    elif field == "bucket_name":
        if bucket:
            bucket["name"] = str(value or "").strip()
            _save_bucket(uid, tok, bucket)

    elif field == "bucket_target":
        _ensure_month(uid, tok, mid)
        month = _find_or_create_month(data, mid)
        amount = float(value or 0)
        month.setdefault("budgets", {})[bid] = amount
        _upsert_budget(uid, tok, mid, bid, amount)

    elif field == "bucket_alloc":
        _ensure_month(uid, tok, mid)
        month = _find_or_create_month(data, mid)
        amount = float(value or 0)
        month.setdefault("allocations", {})[bid] = amount
        _upsert_alloc(uid, tok, mid, bid, amount)

    elif field == "bucket_type":
        if bucket:
            bucket["type"] = str(value or "expense")
            if bucket["type"] == "vault":
                bucket["rollover"] = False
            _save_bucket(uid, tok, bucket)

    elif field == "bucket_cat":
        if bucket:
            bucket["catId"] = str(value or "")
            _save_bucket(uid, tok, bucket)

    elif field == "bucket_rollover":
        if bucket:
            bucket["rollover"] = bool(value)
            _save_bucket(uid, tok, bucket)

    elif field == "bucket_recurring":
        if bucket:
            bucket["recurring"] = bool(value)
            _save_bucket(uid, tok, bucket)

    elif field == "bucket_due_day":
        if bucket:
            v = str(value or "").strip()
            bucket["dueDay"] = int(v) if v.isdigit() else (v if v == "eom" else None)
            _save_bucket(uid, tok, bucket)

    elif field == "bucket_pay_freq":
        if bucket:
            bucket["payFreq"] = str(value) if value else None
            _save_bucket(uid, tok, bucket)

    elif field == "bucket_due_amount":
        if bucket:
            bucket["dueAmount"] = float(value) if value not in (None, "", 0) else None
            _save_bucket(uid, tok, bucket)

    elif field == "bucket_debt_account":
        if bucket:
            bucket["debtAccountId"] = str(value) if value else None
            _save_bucket(uid, tok, bucket)

    elif field == "bucket_notes":
        if bucket:
            bucket["notes"] = str(value or "").strip() or None
            _save_bucket(uid, tok, bucket)

    elif field == "bucket_target_amount":
        if bucket:
            bucket["targetAmount"] = float(value) if value not in (None, "") else None
            _save_bucket(uid, tok, bucket)

    elif field == "bucket_target_date":
        if bucket:
            bucket["targetDate"] = str(value) if value else None
            _save_bucket(uid, tok, bucket)

    elif field == "bucket_contrib_freq":
        if bucket:
            bucket["contribFreq"] = str(value) if value else None
            _save_bucket(uid, tok, bucket)

    elif field == "bucket_default_budget":
        if bucket:
            bucket["defaultBudget"] = float(value or 0)
            _save_bucket(uid, tok, bucket)

    elif field == "bucket_skip":
        _ensure_month(uid, tok, mid)
        month = _find_or_create_month(data, mid)
        skipped = bool(value)
        month.setdefault("skippedBuckets", {})[bid] = skipped
        _set_skipped(uid, tok, mid, bid, skipped)

    elif field == "bucket_archive":
        if bucket:
            bucket["archived"] = True
            _save_bucket(uid, tok, bucket)

    else:
        return jsonify({"ok": False, "error": f"Unknown field: {field}"}), 400

    result = {"ok": True}
    live_fields = {"bucket_alloc", "bucket_target", "bucket_archive",
                   "bucket_skip", "bucket_rollover", "bucket_type"}
    if field in live_fields:
        result.update(_live_state(data, mid or current_month_id()))
    return jsonify(result)


# ── API: add bucket ───────────────────────────────────────────────────────────

@app.route("/api/add-bucket", methods=["POST"])
def api_add_bucket():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    body         = request.get_json(silent=True) or {}
    cat_id       = body.get("cat_id", "").strip()
    new_cat_name = body.get("new_cat_name", "").strip()
    bucket_name  = body.get("bucket_name", "").strip()
    bucket_type  = body.get("bucket_type", "expense")
    active_mid   = (body.get("active_mid") or "").strip() or current_month_id()
    uid, tok     = _uid(), _tok()

    if not bucket_name:
        return jsonify({"ok": False, "error": "Bucket name required"}), 400

    data = _load(uid, tok)

    # Create new category if requested
    is_new_cat = (cat_id == "__new__")
    if is_new_cat:
        if not new_cat_name:
            return jsonify({"ok": False, "error": "Category name required"}), 400
        cat_id = _new_id("cat")
        new_cat = {"id": cat_id, "name": new_cat_name, "color": "", "order": 0, "archived": False}
        data.setdefault("cats", []).append(new_cat)
        _insert_category(uid, tok, new_cat)

    if not any(c["id"] == cat_id for c in data.get("cats", [])):
        return jsonify({"ok": False, "error": "Category not found"}), 400

    bucket_id = _new_id("bkt")
    new_bucket = {
        "id": bucket_id, "catId": cat_id, "name": bucket_name,
        "type": bucket_type, "rollover": bucket_type in ("sinking", "goal"),
        "recurring": False, "archived": False, "defaultBudget": 0, "order": 0, "notes": None,
    }
    data.setdefault("buckets", []).append(new_bucket)
    _insert_bucket(uid, tok, new_bucket)

    cat_name = next((c.get("name", "") for c in data.get("cats", []) if c["id"] == cat_id), "")
    return jsonify({
        "ok": True, "bucket_id": bucket_id, "cat_id": cat_id,
        "cat_name": cat_name, "bucket_name": bucket_name, "bucket_type": bucket_type,
        "is_new_cat": is_new_cat,
        **_live_state(data, active_mid),
    })


# ── API: archive / delete category ───────────────────────────────────────────

@app.route("/api/archive-category", methods=["POST"])
def api_archive_category():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body       = request.get_json(silent=True) or {}
    cat_id     = body.get("cat_id", "").strip()
    active_mid = (body.get("active_mid") or "").strip() or current_month_id()
    uid, tok   = _uid(), _tok()

    data = _load(uid, tok)
    cat  = next((c for c in data.get("cats", []) if c["id"] == cat_id), None)
    if not cat:
        return jsonify({"ok": False, "error": "Category not found"}), 404

    cat["archived"] = True
    _save_category(uid, tok, cat)
    for b in data.get("buckets", []):
        if b.get("catId") == cat_id:
            b["archived"] = True
            _save_bucket(uid, tok, b)

    return jsonify({"ok": True, **_live_state(data, active_mid)})


@app.route("/api/delete-category", methods=["POST"])
def api_delete_category():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body     = request.get_json(silent=True) or {}
    cat_id   = body.get("cat_id", "").strip()
    uid, tok = _uid(), _tok()

    data = _load(uid, tok)
    active_in_cat = [b for b in data.get("buckets", []) if b.get("catId") == cat_id and not b.get("archived")]
    if active_in_cat:
        return jsonify({"ok": False, "error": "Category still has active buckets"}), 400

    _db(tok).table("bcc_categories").delete().eq("id", cat_id).eq("user_id", uid).execute()
    return jsonify({"ok": True})


# ── API: reorder ──────────────────────────────────────────────────────────────

@app.route("/api/reorder", methods=["POST"])
def api_reorder():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body      = request.get_json(silent=True) or {}
    kind      = body.get("kind")
    item_id   = body.get("id", "")
    direction = body.get("direction")
    cat_id    = body.get("cat_id", "")
    uid, tok  = _uid(), _tok()

    data = _load(uid, tok)

    if kind == "bucket":
        items = sorted(
            [b for b in data.get("buckets", []) if b.get("catId") == cat_id and not b.get("archived")],
            key=lambda b: b.get("order", 0),
        )
        table = "bcc_buckets"
    elif kind == "cat":
        items = sorted(data.get("cats", []), key=lambda c: c.get("order", 0))
        table = "bcc_categories"
    else:
        return jsonify({"ok": False, "error": "Unknown kind"}), 400

    idx = next((i for i, x in enumerate(items) if x["id"] == item_id), None)
    if idx is None:
        return jsonify({"ok": False, "error": "Item not found"}), 404

    swap_idx = idx - 1 if direction == "up" else idx + 1
    if swap_idx < 0 or swap_idx >= len(items):
        return jsonify({"ok": True})

    items[idx]["order"], items[swap_idx]["order"] = items[swap_idx]["order"], items[idx]["order"]
    db = _db(tok)
    db.table(table).update({"sort_order": items[idx]["order"]}).eq("id", items[idx]["id"]).eq("user_id", uid).execute()
    db.table(table).update({"sort_order": items[swap_idx]["order"]}).eq("id", items[swap_idx]["id"]).eq("user_id", uid).execute()
    return jsonify({"ok": True})


# ── API: vault withdraw / transfer ────────────────────────────────────────────

@app.route("/api/vault-withdraw", methods=["POST"])
def api_vault_withdraw():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body      = request.get_json(silent=True) or {}
    bucket_id = body.get("id", "").strip()
    mid       = body.get("month", "").strip()
    amount    = float(body.get("amount") or 0)
    uid, tok  = _uid(), _tok()

    if amount <= 0:
        return jsonify({"ok": False, "error": "Amount must be positive"}), 400

    data   = _load(uid, tok)
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bucket_id), None)
    if not bucket or bucket.get("type") != "vault":
        return jsonify({"ok": False, "error": "Not a vault bucket"}), 400

    current_vault_total = vault_accumulated(bucket_id, data.get("months", []))
    if amount > current_vault_total + 0.005:
        return jsonify({"ok": False, "error": f"Cannot release more than ${current_vault_total:.2f}"}), 400

    _ensure_month(uid, tok, mid)
    month = _find_or_create_month(data, mid)

    current_alloc = float((month.get("allocations") or {}).get(bucket_id) or 0)
    from_alloc    = min(amount, current_alloc)
    remainder     = amount - from_alloc

    # Reduce current alloc (already reflected in vault_accumulated)
    if from_alloc > 0:
        new_alloc = current_alloc - from_alloc
        month.setdefault("allocations", {})[bucket_id] = new_alloc
        _upsert_alloc(uid, tok, mid, bucket_id, new_alloc)

    # Record prior-month savings withdrawal
    if remainder > 0:
        existing_w = float((month.get("vaultWithdrawals") or {}).get(bucket_id) or 0)
        new_w = existing_w + remainder
        month.setdefault("vaultWithdrawals", {})[bucket_id] = new_w
        _upsert_vault_withdrawal(uid, tok, mid, bucket_id, new_w)

    return jsonify({"ok": True, "vault_total": vault_accumulated(bucket_id, data.get("months", [])),
                    "alloc": current_alloc - from_alloc, **_live_state(data, mid)})


@app.route("/api/vault-transfer", methods=["POST"])
def api_vault_transfer():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body     = request.get_json(silent=True) or {}
    vault_id = body.get("vault_id", "").strip()
    dest_id  = body.get("dest_id", "").strip()
    mid      = body.get("month", "").strip()
    amount   = float(body.get("amount") or 0)
    uid, tok = _uid(), _tok()

    if amount <= 0:
        return jsonify({"ok": False, "error": "Amount must be positive"}), 400
    if not dest_id:
        return jsonify({"ok": False, "error": "Destination bucket required"}), 400

    data          = _load(uid, tok)
    vault_bucket  = next((b for b in data.get("buckets", []) if b["id"] == vault_id), None)
    dest_bucket   = next((b for b in data.get("buckets", []) if b["id"] == dest_id), None)
    if not vault_bucket or vault_bucket.get("type") != "vault":
        return jsonify({"ok": False, "error": "Not a vault bucket"}), 400
    if not dest_bucket or dest_bucket.get("archived"):
        return jsonify({"ok": False, "error": "Destination bucket not found"}), 400
    if dest_bucket.get("type") == "vault":
        return jsonify({"ok": False, "error": "Cannot transfer to another vault"}), 400

    _ensure_month(uid, tok, mid)
    month = _find_or_create_month(data, mid)
    allocs = month.setdefault("allocations", {})

    vault_alloc = float(allocs.get(vault_id) or 0)
    allocs[vault_id] = max(0.0, vault_alloc - amount)
    _upsert_alloc(uid, tok, mid, vault_id, allocs[vault_id])

    dest_alloc = float(allocs.get(dest_id) or 0)
    allocs[dest_id] = dest_alloc + amount
    _upsert_alloc(uid, tok, mid, dest_id, allocs[dest_id])

    xfr_id = _new_id("vtx")
    _db(tok).table("bcc_vault_transfers").insert({
        "id": xfr_id, "user_id": uid,
        "from_bucket_id": vault_id, "to_bucket_id": dest_id,
        "amount": amount, "month_id": mid, "reason": "planned",
    }).execute()

    all_months   = data.get("months", [])
    active_month = next((m for m in all_months if m["id"] == mid), month)
    return jsonify({
        "ok": True,
        "vault_total": vault_accumulated(vault_id, all_months),
        "vault_alloc": allocs[vault_id],
        "dest_avail":  bucket_available(dest_bucket, active_month, all_months, data.get("txs", [])),
        **_live_state(data, mid),
    })


# ── API: release rollover (kept but not surfaced in UI) ───────────────────────

@app.route("/api/release-rollover", methods=["POST"])
def api_release_rollover():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body      = request.get_json(silent=True) or {}
    bucket_id = body.get("id", "").strip()
    mid       = body.get("month", "").strip()
    amount    = float(body.get("amount") or 0)
    uid, tok  = _uid(), _tok()

    if amount <= 0:
        return jsonify({"ok": False, "error": "Amount must be positive"}), 400

    data   = _load(uid, tok)
    bucket = next((b for b in data.get("buckets", []) if b["id"] == bucket_id), None)
    if not bucket:
        return jsonify({"ok": False, "error": "Bucket not found"}), 404
    if bucket.get("type") == "vault":
        return jsonify({"ok": False, "error": "Use vault withdraw for vault buckets"}), 400

    all_months = data.get("months", [])
    txs        = data.get("txs", [])
    active_month_obj = next(
        (m for m in all_months if m["id"] == mid),
        {"id": mid, "allocations": {}, "budgets": {}, "rolloverReleased": {},
         "skippedBuckets": {}, "vaultWithdrawals": {}},
    )
    current_roll = rollover_bal(bucket, active_month_obj, all_months, txs)
    if amount > current_roll + 0.005:
        return jsonify({"ok": False, "error": f"Cannot release more than ${current_roll:.2f}"}), 400

    _ensure_month(uid, tok, mid)
    month = _find_or_create_month(data, mid)
    existing = float((month.get("rolloverReleased") or {}).get(bucket_id) or 0)
    new_val  = existing + amount
    month.setdefault("rolloverReleased", {})[bucket_id] = new_val
    _upsert_rollover_released(uid, tok, mid, bucket_id, new_val)

    active_month = next((m for m in data.get("months", []) if m["id"] == mid), month)
    return jsonify({
        "ok": True,
        "rollover": rollover_bal(bucket, active_month, data.get("months", []), txs),
        "avail":    bucket_available(bucket, active_month, data.get("months", []), txs),
        **_live_state(data, mid),
    })


# ── API: copy last month's allocations to active month ───────────────────────

@app.route("/api/copy-month-allocs", methods=["POST"])
def api_copy_month_allocs():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body      = request.get_json(silent=True) or {}
    target_mid = (body.get("target_mid") or "").strip()
    if not target_mid:
        return jsonify({"ok": False, "error": "Missing target_mid"}), 400

    uid, tok = _uid(), _tok()
    data = _load(uid, tok)
    all_months = data.get("months", [])
    buckets    = [b for b in data.get("buckets", []) if not b.get("archived")]

    # Find the most recent month before target
    from formulas import months_before
    prior = sorted(months_before(target_mid, all_months), key=lambda m: m["id"], reverse=True)
    if not prior:
        return jsonify({"ok": False, "error": "No prior month found to copy from"}), 404

    source_month = prior[0]
    source_allocs = source_month.get("allocations") or {}

    _ensure_month(uid, tok, target_mid)
    copied = 0
    for b in buckets:
        bid = b["id"]
        amt = float(source_allocs.get(bid) or 0)
        if amt > 0:
            _upsert_alloc(uid, tok, target_mid, bid, amt)
            copied += 1

    # Reload and return
    data = _load(uid, tok)
    return jsonify({"ok": True, "copied": copied, **_live_state(data, target_mid)})


# ── Month nav helpers ──────────────────────────────────────────────────────────

def _mid_label(mid: str) -> str:
    yr, m0 = parse_month_id(mid)
    return f"{MONTH_NAMES[m0]} {yr}"

def _month_sort_key(mid: str) -> tuple:
    return parse_month_id(mid)

def _get_open_mid(S: dict) -> str:
    """The 'open' month: current calendar month if not closed, else latest unclosed."""
    all_months = S.get("months") or []
    cur_mid = current_month_id()
    cur_data = next((m for m in all_months if m["id"] == cur_mid), {})
    if not cur_data.get("closed"):
        return cur_mid
    # Current month was closed — find latest unclosed month
    unclosed = [m for m in all_months if not m.get("closed")]
    if unclosed:
        return sorted(unclosed, key=lambda m: _month_sort_key(m["id"]))[-1]["id"]
    return cur_mid

def _build_available_months(S: dict) -> list[dict]:
    """Months for the nav dropdown: all history + current + next 2."""
    today = date.today()
    all_months = S.get("months") or []
    known = {m["id"]: m for m in all_months}
    cur_mid = current_month_id()
    open_mid = _get_open_mid(S)

    # Always include current + next 2
    required: set[str] = set()
    for delta in range(3):
        mo = today.month + delta
        yr = today.year
        while mo > 12:
            mo -= 12; yr += 1
        required.add(month_id(yr, mo - 1))

    all_mids = required | set(known.keys())
    result = []
    for mid in sorted(all_mids, key=_month_sort_key, reverse=True):
        yr, m0 = parse_month_id(mid)
        m_data = known.get(mid, {})
        closed = bool(m_data.get("closed"))
        is_future = _month_sort_key(mid) > _month_sort_key(cur_mid)
        is_past   = _month_sort_key(mid) < _month_sort_key(cur_mid)
        result.append({
            "id": mid,
            "label": _mid_label(mid),
            "closed": closed,
            "is_future": is_future,
            "is_past": is_past,
            "is_open": mid == open_mid and not closed,
        })
    return result

def _get_month_status(active_mid: str, available: list[dict]) -> str:
    m = next((m for m in available if m["id"] == active_mid), None)
    if not m:
        # Unknown month — treat as future or past by date comparison
        return "future" if _month_sort_key(active_mid) > _month_sort_key(current_month_id()) else "open"
    if m["is_open"]:
        return "open"
    if m["closed"]:
        return "closed"
    if m["is_future"]:
        return "future"
    return "open"  # past, non-closed months remain editable

def _show_close_btn(active_mid: str, S: dict) -> bool:
    """Show Close Month button on the open month when ≤2 days until EOM (or past)."""
    open_mid = _get_open_mid(S)
    if active_mid != open_mid:
        return False
    today = date.today()
    yr, m0 = parse_month_id(active_mid)
    cal_month = m0 + 1
    days_in_month = _cal.monthrange(yr, cal_month)[1]
    month_end = date(yr, cal_month, days_in_month)
    return (month_end - today).days <= 2


# ── Dashboard ─────────────────────────────────────────────────────────────────

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
    S = _load(_uid(), _tok())

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
        active_mid = current_month_id()

    year, m0 = parse_month_id(active_mid)

    available_months = _build_available_months(S)
    open_mid         = _get_open_mid(S)
    month_status     = _get_month_status(active_mid, available_months)
    show_close_btn   = _show_close_btn(active_mid, S)

    active_month = next(
        (m for m in all_months if m.get("id") == active_mid),
        {"id": active_mid, "allocations": {}, "budgets": {}, "rolloverReleased": {},
         "skippedBuckets": {}, "vaultWithdrawals": {}},
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
                roll, spent, vault_total = 0.0, 0.0, vault_accumulated(b["id"], all_months)
                avail = vault_total
            else:
                roll        = rollover_bal(b, active_month, all_months, txs)
                spent       = b_spent(active_mid, b["id"], txs)
                avail       = bucket_available(b, active_month, all_months, txs)
                vault_total = 0.0

            status  = bucket_status(alloc, budget, spent, avail)
            skipped = bool((active_month.get("skippedBuckets") or {}).get(b["id"]))
            target_amount = b.get("targetAmount") or 0
            progress_pct = 0
            if btype == "vault" and target_amount > 0:
                progress_pct = min(100, max(0, round(vault_total / target_amount * 100)))
            elif btype in ("sinking", "goal") and target_amount > 0:
                progress_pct = min(100, max(0, round(avail / target_amount * 100)))
            due = _due_info(b.get("dueDay"), active_mid, status)

            rows.append({
                "id": b["id"], "name": b["name"], "type": btype,
                "cat_id": b.get("catId", cid), "rollover": b.get("rollover", False),
                "recurring": b.get("recurring", False), "skipped": skipped,
                "due_day": b.get("dueDay") or "", "pay_freq": b.get("payFreq") or "",
                "due_amount": b.get("dueAmount") or "", "debt_account_id": b.get("debtAccountId") or "",
                "notes": b.get("notes") or "", "target_amount": target_amount,
                "target_date": b.get("targetDate") or "", "contrib_freq": b.get("contribFreq") or "",
                "default_budget": b.get("defaultBudget", 0),
                "alloc": alloc, "budget": budget, "rollover_val": roll, "spent": spent,
                "avail": avail, "status": status, "vault_total": vault_total,
                "progress_pct": progress_pct,
                "due_label": due["label"], "due_urgency": due["urgency"],
            })
            totals["alloc"]    += alloc
            totals["budget"]   += budget
            totals["rollover"] += roll
            totals["spent"]    += spent
            totals["avail"]    += avail

        category_groups.append({
            "id": cid, "name": cat.get("name", ""),
            "color": cat.get("color", ""), "buckets": rows, "totals": totals,
        })
        for k in grand:
            grand[k] += totals[k]

    cur_mid_obj = next(
        (m for m in all_months if m.get("id") == current_month_id()),
        {"id": current_month_id(), "allocations": {}, "budgets": {}, "rolloverReleased": {},
         "skippedBuckets": {}, "vaultWithdrawals": {}},
    )
    rts = ready_to_spend(cur_mid_obj, all_months, accounts, active_buckets, txs)

    debt_accounts    = [a for a in accounts if a.get("type") == "debt"]
    transfer_buckets = [{"id": b["id"], "name": b["name"]} for b in active_buckets if b.get("type") != "vault"]

    # Accounts panel
    accounts_display = []
    for a in accounts:
        if a.get("archived"):
            continue
        bal = acct_balance(a, txs)
        accounts_display.append({
            "id": a["id"], "name": a.get("name", ""), "type": a.get("type", "budget"),
            "color": a.get("color") or "#3a7fc1", "balance": bal,
            "opening_balance": a.get("openingBalance") or 0,
            "debt_apr": a.get("debtAPR") if a.get("debtAPR") is not None else "",
            "debt_min_payment": a.get("debtMinPayment") if a.get("debtMinPayment") is not None else "",
            "credit_limit": a.get("creditLimit") if a.get("creditLimit") is not None else "",
        })

    cash_accounts         = [a for a in accounts_display if a["type"] != "debt"]
    debt_accounts_display = [a for a in accounts_display if a["type"] == "debt"]
    total_cash_val = sum(a["balance"] for a in cash_accounts)
    total_debt_val = sum(a["balance"] for a in debt_accounts_display)

    vault_buckets_display = []
    for b in active_buckets:
        if b.get("type") == "vault":
            cat = next((c for c in cats if c["id"] == b.get("catId")), None)
            vault_buckets_display.append({
                "id": b["id"], "name": b.get("name", ""),
                "cat_name": cat.get("name", "") if cat else "",
                "vault_total": vault_accumulated(b["id"], all_months),
            })
    total_vault_val = sum(v["vault_total"] for v in vault_buckets_display)

    # Ledger
    from datetime import date as _date, timedelta
    from itertools import groupby

    acct_map   = {a["id"]: a.get("name", a["id"]) for a in accounts}
    bucket_map = {b["id"]: b.get("name", b["id"]) for b in all_buckets}

    ledger_txs = sorted(
        [t for t in txs if t.get("monthId") == active_mid],
        key=lambda t: (t.get("date") or "", t.get("id") or ""),
        reverse=True,
    )

    today     = _date.today()
    yesterday = today - timedelta(days=1)

    def _date_label(date_str: str) -> str:
        try:
            d = _date.fromisoformat(date_str)
            if d == today:     return "Today"
            if d == yesterday: return "Yesterday"
            return d.strftime("%A, %B %-d")
        except ValueError:
            return date_str or "—"

    ledger_rows  = []
    income_total = 0.0
    spent_total  = 0.0
    for t in ledger_txs:
        scheduled = is_scheduled(t)
        amt   = float(t.get("amount") or 0)
        ttype = t.get("type", "out")
        if not scheduled:
            if ttype == "in":   income_total += amt
            elif ttype == "out": spent_total  += amt
        ledger_rows.append({
            "id": t["id"], "date": t.get("date", ""), "desc": t.get("desc", ""),
            "type": ttype, "amount": amt,
            "account":    acct_map.get(t.get("accountId", ""), ""),
            "to_account": acct_map.get(t.get("toAccountId", ""), ""),
            "bucket":     bucket_map.get(t.get("bucketId", ""), ""),
            "bucket_id":  t.get("bucketId", "") or "",
            "account_id": t.get("accountId", "") or "",
            "to_acct_id": t.get("toAccountId", "") or "",
            "scheduled":  scheduled,
            "reconciled": bool(t.get("reconciled")),
            "income_type": t.get("incomeType", "paycheck") if ttype == "in" else "",
        })

    ledger_groups = [
        {"date": date_str, "label": _date_label(date_str), "rows": list(rows)}
        for date_str, rows in groupby(ledger_rows, key=lambda r: r["date"])
    ]

    expense_buckets = [{"id": b["id"], "name": b["name"]} for b in active_buckets if b.get("type") != "vault"]
    rule_buckets    = [{"id": b["id"], "name": b["name"], "type": b.get("type", "expense")} for b in active_buckets]

    # Settings data
    paychecks        = S.get("paychecks") or []
    allocation_rules = S.get("allocationRules") or []
    internal_rules   = [r for r in allocation_rules if r.get("ruleType", "internal") == "internal"]
    external_rules   = [r for r in allocation_rules if r.get("ruleType") == "external"]
    bucket_map_display = {b["id"]: b.get("name", "") for b in active_buckets}

    # Per-account ledgers
    all_txs_sorted = sorted(txs, key=lambda t: (t.get("date") or "", t.get("id") or ""), reverse=True)
    account_ledgers = {}
    for a_disp in accounts_display:
        acct_id = a_disp["id"]
        a_txs   = []
        for t in all_txs_sorted:
            if t.get("monthId") != active_mid:
                continue
            is_from     = t.get("accountId") == acct_id
            is_to       = t.get("toAccountId") == acct_id and t.get("type") == "xfr"
            is_debt_pay = t.get("debtPaymentAccountId") == acct_id and not is_from
            if not (is_from or is_to or is_debt_pay):
                continue
            incoming = is_to or is_debt_pay
            a_txs.append({
                "id": t["id"], "date": t.get("date") or "", "desc": t.get("desc") or "",
                "type": t.get("type", "out"), "amount": float(t.get("amount") or 0),
                "scheduled": is_scheduled(t), "incoming": incoming,
            })
        account_ledgers[acct_id] = [
            {"date": d, "label": _date_label(d), "rows": list(rows)}
            for d, rows in groupby(a_txs, key=lambda r: r["date"])
        ]

    aom = _age_of_money(S)

    return render_template(
        "dashboard.html",
        user_email=session.get("user_email"),
        active_mid=active_mid,
        month_display=f"{MONTH_NAMES[m0]} {year}",
        available_months=available_months, open_mid=open_mid,
        month_status=month_status, show_close_btn=show_close_btn,
        category_groups=category_groups, grand=grand, rts=rts, aom=aom,
        all_cats=cats_sorted, accounts=accounts,
        debt_accounts=debt_accounts, transfer_buckets=transfer_buckets,
        ledger_groups=ledger_groups, ledger_income=income_total, ledger_spent=spent_total,
        expense_buckets=expense_buckets, rule_buckets=rule_buckets,
        cash_accounts=cash_accounts, debt_accounts_display=debt_accounts_display,
        total_cash_val=total_cash_val, total_debt_val=total_debt_val,
        vault_buckets_display=vault_buckets_display, total_vault_val=total_vault_val,
        account_ledgers=account_ledgers,
        paychecks=paychecks, allocation_rules=allocation_rules,
        internal_rules=internal_rules, external_rules=external_rules,
        bucket_map_display=bucket_map_display,
    )


# ── API: transactions ─────────────────────────────────────────────────────────

@app.route("/api/add-transaction", methods=["POST"])
def api_add_transaction():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body        = request.get_json(silent=True) or {}
    ttype       = body.get("type", "out")
    date        = (body.get("date") or "").strip()
    desc        = (body.get("desc") or "").strip()
    amount      = float(body.get("amount") or 0)
    acct_id     = (body.get("account_id") or "").strip()
    bkt_id      = (body.get("bucket_id") or "").strip()
    to_acct     = (body.get("to_account_id") or "").strip()
    income_type = (body.get("income_type") or "paycheck") if ttype == "in" else None
    uid, tok    = _uid(), _tok()

    if not date:   return jsonify({"ok": False, "error": "Date required"}), 400
    if not acct_id: return jsonify({"ok": False, "error": "Account required"}), 400
    if amount <= 0: return jsonify({"ok": False, "error": "Amount must be positive"}), 400
    if ttype == "xfr" and not to_acct:
        return jsonify({"ok": False, "error": "Destination account required for transfer"}), 400

    data = _load(uid, tok)
    mid  = _date_to_month_id(date)
    _ensure_month(uid, tok, mid)
    _find_or_create_month(data, mid)

    tx = {
        "id": _new_id("tx"), "accountId": acct_id, "monthId": mid,
        "desc": desc, "amount": amount, "type": ttype, "date": date,
        "reconciled": False, "recurring": False,
    }
    if ttype == "out" and bkt_id:   tx["bucketId"]    = bkt_id
    if ttype == "xfr":              tx["toAccountId"] = to_acct
    if ttype == "in" and income_type: tx["incomeType"] = income_type

    data.setdefault("txs", []).append(tx)
    _insert_tx(uid, tok, tx)

    active_mid   = (body.get("active_mid") or "").strip() or mid
    accounts_list = data.get("accounts", [])
    acct_name    = next((a.get("name","") for a in accounts_list if a["id"] == acct_id), "")
    to_acct_name = next((a.get("name","") for a in accounts_list if a["id"] == to_acct), "") if to_acct else ""
    bkt_name     = next((b.get("name","") for b in data.get("buckets",[]) if b["id"] == bkt_id), "") if bkt_id else ""

    return jsonify({
        "ok": True, "tx_id": tx["id"], "month_id": mid,
        "tx": {"id": tx["id"], "type": ttype, "date": date, "desc": desc, "amount": amount,
               "account": acct_name, "to_account": to_acct_name,
               "bucket_id": bkt_id, "bucket_name": bkt_name, "income_type": income_type or ""},
        **_live_state(data, active_mid),
    })


@app.route("/api/edit-transaction", methods=["POST"])
def api_edit_transaction():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body     = request.get_json(silent=True) or {}
    tx_id    = (body.get("id") or "").strip()
    field    = (body.get("field") or "").strip()
    value    = body.get("value")
    uid, tok = _uid(), _tok()

    data = _load(uid, tok)
    tx   = next((t for t in data.get("txs", []) if t["id"] == tx_id), None)
    if not tx:
        return jsonify({"ok": False, "error": "Transaction not found"}), 404

    if field == "desc":
        tx["desc"] = str(value or "").strip()
    elif field == "amount":
        tx["amount"] = float(value or 0)
    elif field == "date":
        tx["date"]    = str(value or "").strip()
        tx["monthId"] = _date_to_month_id(tx["date"])
        _ensure_month(uid, tok, tx["monthId"])
        _find_or_create_month(data, tx["monthId"])
    elif field == "bucket_id":
        tx["bucketId"] = str(value or "") or None
    elif field == "account_id":
        tx["accountId"] = str(value or "")
    elif field == "to_account_id":
        tx["toAccountId"] = str(value) if value else None
    elif field == "income_type":
        if tx.get("type") == "in":
            tx["incomeType"] = str(value or "paycheck")
    else:
        return jsonify({"ok": False, "error": f"Unknown field: {field}"}), 400

    _save_tx(uid, tok, tx)
    active_mid = (body.get("active_mid") or "").strip() or tx.get("monthId") or current_month_id()
    return jsonify({"ok": True, **_live_state(data, active_mid)})


@app.route("/api/delete-transaction", methods=["POST"])
def api_delete_transaction():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body       = request.get_json(silent=True) or {}
    tx_id      = (body.get("id") or "").strip()
    active_mid = (body.get("active_mid") or "").strip() or current_month_id()
    uid, tok   = _uid(), _tok()

    data = _load(uid, tok)
    if not _delete_tx(uid, tok, tx_id):
        return jsonify({"ok": False, "error": "Transaction not found"}), 404
    data["txs"] = [t for t in data.get("txs", []) if t["id"] != tx_id]
    return jsonify({"ok": True, **_live_state(data, active_mid)})


# ── API: payees ───────────────────────────────────────────────────────────────

@app.route("/api/payees")
def api_payees():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    uid, tok = _uid(), _tok()
    txs = _db(tok).table("bcc_transactions").select("*").eq("user_id", uid).execute().data or []
    counts: dict[str, int] = {}
    for t in txs:
        name = (t.get("desc") or "").strip()
        if name:
            counts[name] = counts.get(name, 0) + 1
    payees = sorted([{"name": k, "count": v} for k, v in counts.items()], key=lambda x: -x["count"])
    return jsonify({"payees": payees[:50]})


# ── API: paychecks ────────────────────────────────────────────────────────────

@app.route("/api/add-paycheck", methods=["POST"])
def api_add_paycheck():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body   = request.get_json(silent=True) or {}
    label  = (body.get("label") or "").strip()
    amount = float(body.get("amount") or 0)
    freq   = int(body.get("freq") or 14)
    anchor = (body.get("anchor_date") or "").strip()
    uid, tok = _uid(), _tok()

    if not label:   return jsonify({"ok": False, "error": "Label required"}), 400
    if amount <= 0: return jsonify({"ok": False, "error": "Amount required"}), 400

    pc_id = _new_id("pc")
    existing = (_db(tok).table("bcc_paychecks")
                .select("sort_order").eq("user_id", uid)
                .order("sort_order", desc=True).limit(1).execute().data or [])
    sort_order = (existing[0]["sort_order"] + 1) if existing else 1
    _db(tok).table("bcc_paychecks").insert({
        "id": pc_id, "user_id": uid, "label": label, "amount": amount,
        "freq": freq, "anchor_date": anchor or None, "sort_order": sort_order,
    }).execute()

    freq_labels = {7: "Weekly", 14: "Biweekly", 15: "Semi-monthly", 30: "Monthly"}
    return jsonify({"ok": True, "id": pc_id, "paycheck": {
        "id": pc_id, "label": label, "amount": amount,
        "freq_label": freq_labels.get(freq, f"{freq}d"), "anchor": anchor or "—",
    }})


@app.route("/api/delete-paycheck", methods=["POST"])
def api_delete_paycheck():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body   = request.get_json(silent=True) or {}
    pc_id  = (body.get("id") or "").strip()
    uid, tok = _uid(), _tok()

    res = _db(tok).table("bcc_paychecks").delete().eq("id", pc_id).eq("user_id", uid).execute()
    if not res.data:
        return jsonify({"ok": False, "error": "Not found"}), 404
    return jsonify({"ok": True})


# ── API: allocation rules ─────────────────────────────────────────────────────

@app.route("/api/add-rule", methods=["POST"])
def api_add_rule():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body       = request.get_json(silent=True) or {}
    name       = (body.get("name") or "").strip()
    rule_type  = body.get("rule_type", "internal")
    value_type = body.get("value_type", "fixed")
    value      = float(body.get("value") or 0)
    bucket_id  = (body.get("bucket_id") or "").strip()
    uid, tok   = _uid(), _tok()

    if not name:   return jsonify({"ok": False, "error": "Name required"}), 400
    if value <= 0: return jsonify({"ok": False, "error": "Amount required"}), 400
    if rule_type == "internal" and not bucket_id:
        return jsonify({"ok": False, "error": "Bucket required for internal rule"}), 400

    rule_id = _new_id("rule")
    existing = (_db(tok).table("bcc_allocation_rules")
                .select("sort_order").eq("user_id", uid)
                .order("sort_order", desc=True).limit(1).execute().data or [])
    sort_order = (existing[0]["sort_order"] + 1) if existing else 1
    _db(tok).table("bcc_allocation_rules").insert({
        "id": rule_id, "user_id": uid, "name": name,
        "rule_type": rule_type, "value_type": value_type,
        "value": value, "bucket_id": bucket_id if rule_type == "internal" else None,
        "active": True, "sort_order": sort_order,
    }).execute()

    data = _load(uid, tok)
    bucket_name = next((b.get("name","") for b in data.get("buckets",[]) if b["id"] == bucket_id), "") if bucket_id else ""
    return jsonify({"ok": True, "id": rule_id, "rule": {
        "id": rule_id, "name": name, "rule_type": rule_type,
        "value_type": value_type, "value": value, "bucket_name": bucket_name,
    }})


@app.route("/api/toggle-rule", methods=["POST"])
def api_toggle_rule():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body    = request.get_json(silent=True) or {}
    rule_id = (body.get("id") or "").strip()
    uid, tok = _uid(), _tok()

    res = _db(tok).table("bcc_allocation_rules").select("active").eq("id", rule_id).eq("user_id", uid).execute()
    if not res.data:
        return jsonify({"ok": False, "error": "Not found"}), 404
    new_active = not res.data[0]["active"]
    _db(tok).table("bcc_allocation_rules").update({"active": new_active}).eq("id", rule_id).eq("user_id", uid).execute()
    return jsonify({"ok": True, "active": new_active})


@app.route("/api/delete-rule", methods=["POST"])
def api_delete_rule():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body    = request.get_json(silent=True) or {}
    rule_id = (body.get("id") or "").strip()
    uid, tok = _uid(), _tok()

    _db(tok).table("bcc_allocation_rules").delete().eq("id", rule_id).eq("user_id", uid).execute()
    return jsonify({"ok": True})


# ── API: payday ───────────────────────────────────────────────────────────────

@app.route("/api/payday-suggestions", methods=["POST"])
def api_payday_suggestions():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body   = request.get_json(silent=True) or {}
    amount = float(body.get("amount") or 0)

    data  = _load(_uid(), _tok())
    rules = [r for r in (data.get("allocationRules") or []) if r.get("active")]
    bmap  = {b["id"]: b.get("name", b["id"]) for b in data.get("buckets", []) if not b.get("archived")}

    internal, external = [], []
    for rule in rules:
        computed = round(amount * rule["value"] / 100, 2) if rule["type"] == "pct" else float(rule["value"])
        item = {"id": rule["id"], "name": rule["name"], "type": rule["type"],
                "value": rule["value"], "computed": computed}
        if rule.get("ruleType") == "external":
            external.append(item)
        else:
            bid = rule.get("bucketId", "")
            item["bucket_id"]   = bid
            item["bucket_name"] = bmap.get(bid, "")
            internal.append(item)

    return jsonify({"ok": True, "internal": internal, "external": external})


@app.route("/api/apply-payday", methods=["POST"])
def api_apply_payday():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body        = request.get_json(silent=True) or {}
    mid         = (body.get("month") or "").strip()
    allocations = body.get("allocations", [])
    uid, tok    = _uid(), _tok()

    data = _load(uid, tok)
    _ensure_month(uid, tok, mid)
    month = _find_or_create_month(data, mid)

    for item in allocations:
        bid = (item.get("bucket_id") or "").strip()
        amt = float(item.get("amount") or 0)
        if bid and amt > 0:
            current = float((month.get("allocations") or {}).get(bid) or 0)
            new_val = current + amt
            month.setdefault("allocations", {})[bid] = new_val
            _upsert_alloc(uid, tok, mid, bid, new_val)

    return jsonify({"ok": True, **_live_state(data, mid or current_month_id())})


# ── API: accounts ─────────────────────────────────────────────────────────────

@app.route("/api/add-account", methods=["POST"])
def api_add_account():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body       = request.get_json(silent=True) or {}
    name       = (body.get("name") or "").strip()
    atype      = body.get("type", "budget")
    color      = body.get("color") or "#3a7fc1"
    opening    = float(body.get("opening_balance") or 0)
    active_mid = (body.get("active_mid") or "").strip() or current_month_id()
    uid, tok   = _uid(), _tok()

    if not name:
        return jsonify({"ok": False, "error": "Account name required"}), 400

    acct_id  = _new_id("acct")
    new_acct = {"id": acct_id, "name": name, "type": atype, "color": color,
                "openingBalance": opening, "archived": False}
    _insert_account(uid, tok, new_acct)

    data = _load(uid, tok)
    return jsonify({
        "ok": True, "acct_id": acct_id,
        "account": {"id": acct_id, "name": name, "type": atype, "color": color, "balance": opening},
        **_live_state(data, active_mid),
    })


@app.route("/api/save-account", methods=["POST"])
def api_save_account():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body       = request.get_json(silent=True) or {}
    acct_id    = (body.get("id") or "").strip()
    field      = (body.get("field") or "").strip()
    value      = body.get("value")
    active_mid = (body.get("active_mid") or "").strip() or current_month_id()
    uid, tok   = _uid(), _tok()

    data = _load(uid, tok)
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

    _save_account(uid, tok, acct)
    return jsonify({"ok": True, **_live_state(data, active_mid)})


# ── API: debt payment ─────────────────────────────────────────────────────────

@app.route("/api/debt-payment", methods=["POST"])
def api_debt_payment():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body         = request.get_json(silent=True) or {}
    debt_id      = (body.get("debt_id") or "").strip()
    from_acct_id = (body.get("from_account_id") or "").strip()
    amount       = float(body.get("amount") or 0)
    date         = (body.get("date") or "").strip()
    bucket_id    = (body.get("bucket_id") or "").strip()
    active_mid   = (body.get("active_mid") or "").strip()
    uid, tok     = _uid(), _tok()

    if not debt_id or not from_acct_id:
        return jsonify({"ok": False, "error": "Debt account and source account required"}), 400
    if amount <= 0:
        return jsonify({"ok": False, "error": "Amount must be positive"}), 400
    if not date:
        return jsonify({"ok": False, "error": "Date required"}), 400

    data = _load(uid, tok)
    debt_acct = next((a for a in data.get("accounts", []) if a["id"] == debt_id), None)
    src_acct  = next((a for a in data.get("accounts", []) if a["id"] == from_acct_id), None)
    if not debt_acct or debt_acct.get("type") != "debt":
        return jsonify({"ok": False, "error": "Debt account not found"}), 400
    if not src_acct:
        return jsonify({"ok": False, "error": "Source account not found"}), 400

    mid = _date_to_month_id(date)
    _ensure_month(uid, tok, mid)
    _find_or_create_month(data, mid)

    tx = {
        "id": _new_id("tx"), "accountId": from_acct_id,
        "debtPaymentAccountId": debt_id, "monthId": mid,
        "desc": f"Payment — {debt_acct.get('name', '')}",
        "amount": amount, "type": "out", "date": date,
        "reconciled": False, "recurring": False,
    }
    if bucket_id:
        tx["bucketId"] = bucket_id

    data.setdefault("txs", []).append(tx)
    _insert_tx(uid, tok, tx)

    txs_new      = data.get("txs", [])
    new_debt_bal = acct_balance(debt_acct, txs_new)
    new_src_bal  = acct_balance(src_acct, txs_new)
    view_mid     = active_mid or mid

    return jsonify({"ok": True, "tx_id": tx["id"],
                    "debt_bal": new_debt_bal, "src_bal": new_src_bal,
                    **_live_state(data, view_mid)})



# ── API: reports ─────────────────────────────────────────────────────────────

@app.route("/api/reports")
def api_reports():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    active_mid = request.args.get("month") or current_month_id()
    uid, tok   = _uid(), _tok()
    data       = _load(uid, tok)

    year, m0   = parse_month_id(active_mid)
    month_label = f"{MONTH_NAMES[m0]} {year}"

    all_months     = data.get("months", [])
    txs            = data.get("txs", [])
    cats           = data.get("cats", [])
    all_buckets    = data.get("buckets", [])

    active_month = next(
        (m for m in all_months if m.get("id") == active_mid),
        {"id": active_mid, "allocations": {}, "budgets": {}, "rolloverReleased": {},
         "skippedBuckets": {}, "vaultWithdrawals": {}},
    )

    # ── Summary ──────────────────────────────────────────────────────────────
    income_total = sum(
        float(t.get("amount", 0)) for t in txs
        if t.get("monthId") == active_mid and t.get("type") == "in" and not is_scheduled(t)
    )
    spent_total = sum(
        float(t.get("amount", 0)) for t in txs
        if t.get("monthId") == active_mid and t.get("type") == "out" and not is_scheduled(t)
    )
    allocated_total = sum(
        float(v) for v in (active_month.get("allocations") or {}).values()
    )
    rts = _rts_now(data)

    # ── Category breakdown ────────────────────────────────────────────────────
    cat_breakdown = []
    for cat in cats:
        if cat.get("archived"):
            continue
        cid = cat["id"]
        cat_buckets = [
            b for b in all_buckets
            if b.get("catId") == cid and not b.get("archived")
        ]
        if not cat_buckets:
            continue

        bucket_rows = []
        cat_alloc  = 0.0
        cat_spent  = 0.0
        cat_budget = 0.0

        for b in cat_buckets:
            bid    = b["id"]
            btype  = b.get("type", "expense")
            alloc  = float((active_month.get("allocations") or {}).get(bid, 0))
            budget = float((active_month.get("budgets") or {}).get(bid, 0))

            if btype == "vault":
                b_spent_val = 0.0
                avail       = vault_accumulated(bid, all_months)
                status      = ""
            else:
                b_spent_val = sum(
                    float(t.get("amount", 0)) for t in txs
                    if t.get("bucketId") == bid and t.get("type") == "out"
                    and t.get("monthId") == active_mid and not is_scheduled(t)
                )
                avail  = bucket_available(b, active_month, all_months, txs)
                status = bucket_status(alloc, budget, b_spent_val, avail)

            cat_alloc  += alloc
            cat_spent  += b_spent_val
            cat_budget += budget

            bucket_rows.append({
                "name":      b["name"],
                "allocated": alloc,
                "spent":     b_spent_val,
                "avail":     avail,
                "status":    status,
            })

        pct = round(cat_spent / cat_alloc * 100) if cat_alloc > 0 else 0
        cat_breakdown.append({
            "id":        cid,
            "name":      cat["name"],
            "color":     cat.get("color") or "",
            "allocated": cat_alloc,
            "spent":     cat_spent,
            "budget":    cat_budget,
            "pct_spent": pct,
            "over":      cat_spent > cat_alloc,
            "buckets":   bucket_rows,
        })

    # ── Monthly trends: last 12 months ────────────────────────────────────────
    cur_year, cur_m0 = parse_month_id(current_month_id())
    months_seq = []
    for i in range(11, -1, -1):
        total_m = cur_m0 - i
        y = cur_year + total_m // 12
        m = total_m % 12
        if m < 0:
            m += 12
            y -= 1
        months_seq.append(month_id(y, m))

    monthly_trends = []
    for mid_t in months_seq:
        y_t, m0_t = parse_month_id(mid_t)
        short_year = str(y_t)[2:]
        label      = f"{MONTH_NAMES[m0_t][:3]} {short_year}"

        month_obj  = next((m for m in all_months if m.get("id") == mid_t), None)
        t_income   = sum(
            float(t.get("amount", 0)) for t in txs
            if t.get("monthId") == mid_t and t.get("type") == "in" and not is_scheduled(t)
        )
        t_spent    = sum(
            float(t.get("amount", 0)) for t in txs
            if t.get("monthId") == mid_t and t.get("type") == "out" and not is_scheduled(t)
        )
        t_alloc    = sum(
            float(v) for v in ((month_obj.get("allocations") or {}) if month_obj else {}).values()
        )
        monthly_trends.append({
            "mid":       mid_t,
            "label":     label,
            "income":    t_income,
            "spent":     t_spent,
            "allocated": t_alloc,
        })

    # ── Cash flow: group non-scheduled txs by ISO week within active_mid ─────
    from datetime import date as _date, timedelta as _timedelta
    _year_a, _m0_a = parse_month_id(active_mid)
    _month_a = _m0_a + 1
    import calendar as _cal
    _first_day = _date(_year_a, _month_a, 1)
    _last_day_n = _cal.monthrange(_year_a, _month_a)[1]
    _last_day = _date(_year_a, _month_a, _last_day_n)

    # Build week buckets (Monday-anchored) covering the whole month
    _week_start = _first_day - _timedelta(days=_first_day.weekday())  # Monday on or before 1st
    _weeks = []
    while _week_start <= _last_day:
        _week_end = _week_start + _timedelta(days=6)
        _label_start = max(_week_start, _first_day)
        _label_end = min(_week_end, _last_day)
        _label = f"{MONTH_NAMES[_m0_a][:3]} {_label_start.day}–{_label_end.day}"
        _weeks.append({"start": _week_start, "end": _week_end, "label": _label, "income": 0.0, "spending": 0.0})
        _week_start += _timedelta(days=7)

    for t in txs:
        if t.get("monthId") != active_mid or is_scheduled(t):
            continue
        try:
            _td = _date.fromisoformat(t.get("date") or "")
        except Exception:
            continue
        for _w in _weeks:
            if _w["start"] <= _td <= _w["end"]:
                if t.get("type") == "in":
                    _w["income"] += float(t.get("amount", 0))
                elif t.get("type") == "out":
                    _w["spending"] += float(t.get("amount", 0))
                break

    cash_flow = [{"week": w["label"], "income": round(w["income"], 2), "spending": round(w["spending"], 2)} for w in _weeks]

    # ── YTD: Jan through active_mid ─────────────────────────────────────────
    _ytd_months = []
    for _mi in range(0, _m0_a + 1):
        _ytd_mid = month_id(_year_a, _mi)
        _ytd_inc = sum(float(t.get("amount", 0)) for t in txs if t.get("monthId") == _ytd_mid and t.get("type") == "in" and not is_scheduled(t))
        _ytd_out = sum(float(t.get("amount", 0)) for t in txs if t.get("monthId") == _ytd_mid and t.get("type") == "out" and not is_scheduled(t))
        _ytd_months.append({"label": MONTH_NAMES[_mi][:3], "income": round(_ytd_inc, 2), "spending": round(_ytd_out, 2)})

    _ytd_income_total = sum(m["income"] for m in _ytd_months)
    _ytd_spending_total = sum(m["spending"] for m in _ytd_months)
    _ytd_savings = _ytd_income_total - _ytd_spending_total
    _ytd_rate = round(_ytd_savings / _ytd_income_total * 100, 1) if _ytd_income_total > 0 else 0.0

    # ── YTD allocations ────────────────────────────────────────────────────
    _ytd_alloc_total = 0.0
    for _mi in range(0, _m0_a + 1):
        _ytd_mid = month_id(_year_a, _mi)
        _mo = next((m for m in all_months if m.get("id") == _ytd_mid), None)
        if _mo:
            _ytd_alloc_total += sum(float(v) for v in (_mo.get("allocations") or {}).values())

    ytd = {
        "income": round(_ytd_income_total, 2),
        "spending": round(_ytd_spending_total, 2),
        "allocated": round(_ytd_alloc_total, 2),
        "savings": round(_ytd_savings, 2),
        "savings_rate": _ytd_rate,
        "months": _ytd_months,
    }

    # ── Income sources: this month, non-scheduled, type==in ─────────────────
    _inc_txs = [t for t in txs if t.get("monthId") == active_mid and t.get("type") == "in" and not is_scheduled(t)]
    _src_map = {}
    for t in _inc_txs:
        _key = (t.get("desc") or "").strip().lower() or "(unnamed)"
        _src_map.setdefault(_key, {"name": (t.get("desc") or "").strip() or "(unnamed)", "total": 0.0, "count": 0})
        _src_map[_key]["total"] += float(t.get("amount", 0))
        _src_map[_key]["count"] += 1
    _src_list = sorted(_src_map.values(), key=lambda x: x["total"], reverse=True)
    _src_grand = sum(s["total"] for s in _src_list)
    income_sources = [{"name": s["name"], "total": round(s["total"], 2), "count": s["count"],
                       "pct": round(s["total"] / _src_grand * 100) if _src_grand > 0 else 0} for s in _src_list]

    # ── Net worth: current snapshot + 12-month history ───────────────────────
    accounts = data.get("accounts", [])
    _budget_total = sum(acct_balance(a, txs) for a in accounts if a.get("type") in ("budget", "savings") and not a.get("archived"))
    _savings_total = 0.0  # already included in budget accounts above; we'll keep separate for display
    _debt_total = sum(acct_balance(a, txs) for a in accounts if a.get("type") == "debt" and not a.get("archived"))

    # Recompute split: budget vs savings
    _budget_bal = sum(acct_balance(a, txs) for a in accounts if a.get("type") == "budget" and not a.get("archived"))
    _savings_bal = sum(acct_balance(a, txs) for a in accounts if a.get("type") == "savings" and not a.get("archived"))
    _debt_bal = _debt_total  # typically negative or positive depending on convention
    _net_cur = _budget_bal + _savings_bal + _debt_bal

    # Monthly net worth history: last 12 months
    _nw_history = []
    _cur_y, _cur_m = parse_month_id(current_month_id())
    for _i in range(11, -1, -1):
        _total_m = _cur_m - _i
        _hy = _cur_y + _total_m // 12
        _hm = _total_m % 12
        if _hm < 0:
            _hm += 12
            _hy -= 1
        import calendar as _cal2
        _last_of_month = _date(_hy, _hm + 1, _cal2.monthrange(_hy, _hm + 1)[1])
        _h_label = f"{MONTH_NAMES[_hm][:3]} {str(_hy)[2:]}"

        def _bal_at(acct, cutoff):
            ob = float(acct.get("openingBalance") or 0)
            for tx in txs:
                try:
                    td = _date.fromisoformat(tx.get("date") or "")
                except Exception:
                    continue
                if td > cutoff:
                    continue
                if tx.get("accountId") == acct["id"]:
                    if tx.get("type") == "in":
                        ob += float(tx.get("amount", 0))
                    elif tx.get("type") in ("out", "xfr"):
                        ob -= float(tx.get("amount", 0))
                elif tx.get("toAccountId") == acct["id"] and tx.get("type") == "xfr":
                    ob += float(tx.get("amount", 0))
                elif tx.get("debtPaymentAccountId") == acct["id"]:
                    ob += float(tx.get("amount", 0))
            return ob

        _h_net = sum(_bal_at(a, _last_of_month) for a in accounts if not a.get("archived"))
        _nw_history.append({"label": _h_label, "net": round(_h_net, 2)})

    net_worth = {
        "budget_total": round(_budget_bal, 2),
        "savings_total": round(_savings_bal, 2),
        "debt_total": round(_debt_bal, 2),
        "net": round(_net_cur, 2),
        "history": _nw_history,
    }

    return jsonify({
        "ok":                 True,
        "active_mid":         active_mid,
        "month_label":        month_label,
        "summary": {
            "income":    income_total,
            "allocated": allocated_total,
            "spent":     spent_total,
            "rts":       rts,
        },
        "category_breakdown": cat_breakdown,
        "monthly_trends":     monthly_trends,
        "cash_flow":          cash_flow,
        "ytd":                ytd,
        "income_sources":     income_sources,
        "net_worth":          net_worth,
    })


# ── API: export CSV ───────────────────────────────────────────────────────────

@app.route("/api/export-csv")
def api_export_csv():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    import io, csv as _csv
    active_mid = request.args.get("month") or current_month_id()
    uid, tok   = _uid(), _tok()
    data       = _load(uid, tok)
    year, m0   = parse_month_id(active_mid)

    txs      = data.get("txs", [])
    accounts = {a["id"]: a["name"] for a in data.get("accounts", [])}
    buckets  = {b["id"]: b["name"] for b in data.get("buckets", [])}

    month_txs = [
        t for t in txs
        if t.get("monthId") == active_mid and not is_scheduled(t)
    ]
    month_txs.sort(key=lambda t: t.get("date") or "")

    buf = io.StringIO()
    writer = _csv.writer(buf)
    writer.writerow(["Date", "Description", "Amount", "Type", "Account", "Bucket"])
    for t in month_txs:
        writer.writerow([
            t.get("date") or "",
            t.get("desc") or "",
            t.get("amount", 0),
            t.get("type", ""),
            accounts.get(t.get("accountId") or "", ""),
            buckets.get(t.get("bucketId") or "", ""),
        ])

    filename = f"budget_{year}_{m0 + 1:02d}.csv"
    from flask import Response
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )


# ── Forecast helpers ─────────────────────────────────────────────────────────

def _gen_pay_dates(anchor_str: str, freq: int, from_date: date, to_date: date) -> list:
    """Generate all pay dates from from_date to to_date inclusive."""
    if not anchor_str:
        return []
    anchor = date.fromisoformat(anchor_str)
    dates = []

    if freq == 15:  # semi-monthly: always 1st and 15th
        y, m = from_date.year, from_date.month
        while date(y, m, 1) <= to_date:
            for day in (1, 15):
                d = date(y, m, day)
                if from_date <= d <= to_date:
                    dates.append(d)
            if m == 12:
                y, m = y + 1, 1
            else:
                m += 1
    elif freq == 30:  # monthly: same day-of-month as anchor
        day = anchor.day
        y, m = from_date.year, from_date.month
        while True:
            last = _cal.monthrange(y, m)[1]
            d = date(y, m, min(day, last))
            if d > to_date:
                break
            if d >= from_date:
                dates.append(d)
            if m == 12:
                y, m = y + 1, 1
            else:
                m += 1
    else:  # 7 (weekly) or 14 (biweekly): walk from anchor
        # Fast-forward anchor to the first pay date on or after from_date.
        # Using integer math avoids iterating through potentially years of history.
        delta_days = (from_date - anchor).days
        if delta_days > 0:
            steps = (delta_days + freq - 1) // freq  # ceiling division
            d = anchor + timedelta(days=steps * freq)
        else:
            # anchor is on or after from_date — walk backward once if needed
            d = anchor
            while d >= from_date:
                d -= timedelta(days=freq)
            d += timedelta(days=freq)
        while d <= to_date:
            dates.append(d)
            d += timedelta(days=freq)

    return sorted(dates)


def _bill_dates_in_range(due_day, pay_freq, from_date: date, to_date: date) -> list:
    """Generate all dates a recurring bill falls due, from from_date to to_date."""
    if not due_day:
        return []

    raw = str(due_day).strip().lower()
    dates = []

    if pay_freq in ('weekly', 'biweekly', 'triweekly'):
        freq_days = {'weekly': 7, 'biweekly': 14, 'triweekly': 21}.get(pay_freq, 30)
        try:
            anchor_day = int(raw)
        except ValueError:
            anchor_day = 1
        d = date(from_date.year, from_date.month, min(anchor_day, _cal.monthrange(from_date.year, from_date.month)[1]))
        while d < from_date:
            d += timedelta(days=freq_days)
        while d <= to_date:
            dates.append(d)
            d += timedelta(days=freq_days)
        return dates

    # Monthly (default): once per month on due_day
    y, m = from_date.year, from_date.month
    while True:
        if raw == 'eom':
            day = _cal.monthrange(y, m)[1]
        else:
            try:
                day = int(raw)
            except ValueError:
                break
        last = _cal.monthrange(y, m)[1]
        d = date(y, m, min(day, last))
        if d > to_date:
            break
        if d >= from_date:
            dates.append(d)
        if m == 12:
            y, m = y + 1, 1
        else:
            m += 1

    return sorted(dates)


def _freq_only_dates_in_range(pay_freq: str, from_date: date, to_date: date) -> list:
    """Occurrence dates for expenses with a frequency but no specific due day
    (e.g. groceries $400/week, dining $300/month). Anchors to from_date."""
    if pay_freq == 'monthly':
        # One occurrence per calendar month covered by the period
        dates, y, m = [], from_date.year, from_date.month
        while True:
            d = from_date if (y == from_date.year and m == from_date.month) else date(y, m, 1)
            if d > to_date:
                break
            dates.append(d)
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        return dates
    freq_days = {'weekly': 7, 'biweekly': 14, 'triweekly': 21}.get(pay_freq)
    if not freq_days:
        return []
    dates, d = [], from_date
    while d <= to_date:
        dates.append(d)
        d += timedelta(days=freq_days)
    return dates


_FC_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
_FC_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _fc_date_label(d: date) -> str:
    return f"{_FC_DAYS[d.weekday()]}, {_FC_MONTHS[d.month-1]} {d.day}"


def _fc_range_label(s: date, e: date) -> str:
    if s == e:
        return _fc_date_label(s)
    s_str = f"{_FC_MONTHS[s.month-1]} {s.day}"
    e_str = f"{_FC_MONTHS[e.month-1]} {e.day}"
    if s.year != e.year:
        return f"{s_str}, {s.year} – {e_str}, {e.year}"
    return f"{s_str} – {e_str}"


def _mid_for_date(d: date) -> str:
    return f"m_{d.year}_{d.month - 1}"


def _age_of_money(data: dict):
    """14-day avg balance divided by 90-day avg daily spend. Returns int or None."""
    accounts = data.get("accounts", [])
    txs      = data.get("txs", [])
    today_d  = date.today()
    ago90    = today_d - timedelta(days=90)

    current_cash = sum(acct_balance(a, txs) for a in accounts
                       if a.get("type") != "debt" and not a.get("archived"))

    # Net transaction impact per date (positive = in, negative = out)
    tx_net_by_date: dict = {}
    for t in txs:
        try:
            t_date = date.fromisoformat(t.get("date", ""))
        except (ValueError, TypeError):
            continue
        amount = float(t.get("amount", 0))
        sign = 1 if t.get("type") == "in" else -1
        tx_net_by_date[t_date] = tx_net_by_date.get(t_date, 0.0) + sign * amount

    # Reconstruct end-of-day balances for past 14 days by walking backward from today
    daily_balances = []
    cumulative_undo = 0.0
    for i in range(14):  # 0 = today, 13 = 13 days ago → 14 data points = 14-day avg
        if i > 0:
            cumulative_undo += tx_net_by_date.get(today_d - timedelta(days=i - 1), 0.0)
        daily_balances.append(current_cash - cumulative_undo)

    avg_14 = sum(daily_balances) / len(daily_balances)

    spent_90 = sum(
        float(t.get("amount", 0)) for t in txs
        if t.get("type") == "out"
        and not is_scheduled(t)
        and str(ago90) <= t.get("date", "") <= str(today_d)
    )
    avg_daily_90 = spent_90 / 90.0
    if avg_daily_90 < 0.01:
        return None
    return round(avg_14 / avg_daily_90)


# ── API: forecast ─────────────────────────────────────────────────────────────

@app.route("/api/forecast")
def api_forecast():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    months_param      = request.args.get('months', '3')
    balance_param     = request.args.get('balance')
    skip_today_income = request.args.get('skip_today_income', '0') == '1'

    try:
        n_months = int(months_param)
    except ValueError:
        n_months = 3

    uid, tok = _uid(), _tok()
    data     = _load(uid, tok)

    accounts    = data.get("accounts", [])
    txs         = data.get("txs", [])
    paychecks   = data.get("paychecks", [])
    alloc_rules = data.get("allocationRules", [])
    buckets     = data.get("buckets", [])

    # Starting balance: sum of all non-archived, non-debt accounts
    budget_bal = sum(
        acct_balance(a, txs)
        for a in accounts
        if a.get("type") != "debt" and not a.get("archived")
    )

    # Override with custom balance if provided
    if balance_param is not None:
        try:
            budget_bal = float(balance_param)
        except ValueError:
            pass

    # Build account_balances list for frontend chip selector
    account_balances = [
        {"id": a["id"], "name": a["name"], "type": a["type"],
         "balance": round(acct_balance(a, txs), 2)}
        for a in accounts
        if a.get("type") != "debt" and not a.get("archived")
    ]

    today = date.today()

    # Determine end date
    if n_months == 0:
        end_date = date(today.year, 12, 31)
    else:
        y = today.year + (today.month - 1 + n_months) // 12
        m = (today.month - 1 + n_months) % 12 + 1
        end_date = date(y, m, _cal.monthrange(y, m)[1])

    # ── Build pay_events: date → [paycheck dicts] ──────────────────────────
    external_rules  = [r for r in alloc_rules if r.get("ruleType") == "external" and r.get("active", True)]
    internal_rules  = [r for r in alloc_rules if r.get("ruleType") != "external" and r.get("active", True) and r.get("bucketId")]
    bucket_name_map = {b["id"]: b["name"] for b in buckets}
    bucket_type_map = {b["id"]: b.get("type", "expense") for b in buckets}

    pay_events: dict = {}  # date → list of paycheck hit dicts
    for pc in paychecks:
        if not pc.get("anchorDate"):
            continue
        for pd in _gen_pay_dates(pc["anchorDate"], pc["freq"], today, end_date):
            if pd not in pay_events:
                pay_events[pd] = []
            transfers = []
            for rule in external_rules:
                amt = float(pc["amount"])
                computed = round(amt * rule["value"] / 100, 2) if rule.get("type") == "pct" else float(rule["value"])
                transfers.append({"name": rule["name"], "amount": computed})
            # Build internal allocation events
            alloc_events = []
            for rule in internal_rules:
                pc_amount = float(pc["amount"])
                if rule.get("type") == "pct":
                    computed = round(pc_amount * rule["value"] / 100, 2)
                else:
                    computed = float(rule["value"])
                bid = rule["bucketId"]
                bucket_name = bucket_name_map.get(bid, rule.get("name", ""))
                is_vault = bucket_type_map.get(bid, "expense") == "vault"
                alloc_events.append({"bucket": bucket_name, "bucket_id": bid, "amount": computed, "is_vault": is_vault})
            pay_events[pd].append({
                "label":        pc["label"],
                "amount":       float(pc["amount"]),
                "transfers":    transfers,
                "alloc_events": alloc_events,
            })

    all_pay_dates = sorted(pay_events.keys())

    # ── Build period boundaries ─────────────────────────────────────────────
    # period = (start, end, is_gap)
    # Gap = today → day before first paycheck (skipped if today is a payday)
    periods_meta = []
    if not all_pay_dates:
        periods_meta.append((today, end_date, True))
    else:
        if all_pay_dates[0] > today:
            periods_meta.append((today, all_pay_dates[0] - timedelta(days=1), True))
        for i, pd in enumerate(all_pay_dates):
            if i + 1 < len(all_pay_dates):
                pe = all_pay_dates[i + 1] - timedelta(days=1)
            else:
                pe = end_date
            periods_meta.append((pd, pe, False))

    # ── Monthly allocation data for funded status ───────────────────────────
    months_list      = data.get("months", [])
    monthly_allocs   = {m.get("id", ""): m.get("allocations", {}) for m in months_list}
    monthly_budgets  = {m.get("id", ""): m.get("budgets", {}) for m in months_list}

    # Current month bucket statuses (for PAID detection in gap period)
    today_mid = _mid_for_date(today)
    live_now  = _live_state(data, today_mid)
    cur_statuses = live_now.get("bucket_statuses", {})

    # defaultBudget fallback per bucket — used as "funded" signal for future months
    bucket_default_budget = {
        b["id"]: float(b.get("defaultBudget") or b.get("dueAmount") or 0)
        for b in buckets
    }

    def _bill_funded(bucket_id: str, bill_date: date) -> bool:
        mid    = _mid_for_date(bill_date)
        budget = float(monthly_budgets.get(mid, {}).get(bucket_id, 0))
        alloc  = float(monthly_allocs.get(mid, {}).get(bucket_id, 0))
        if budget > 0:
            return alloc >= budget
        if alloc > 0:
            # Money allocated but no budget target set — treat as funded
            return True
        # No real data (future month) — funded if bucket has a default budget
        return bucket_default_budget.get(bucket_id, 0) > 0

    def _bill_paid(bucket_id: str, bill_date: date) -> bool:
        # Only skip if the bill was actually spent (recorded transaction)
        return (_mid_for_date(bill_date) == today_mid
                and cur_statuses.get(bucket_id, "") == "PAID")

    # ── Recurring bills: dated (have dueDay) and freq-only (payFreq, no dueDay)
    # No "recurring" flag required — if a bucket has a due day or frequency + amount,
    # it belongs in the forecast. The user set it up; the intent is clear.
    dated_bills = [
        b for b in buckets
        if not b.get("archived")
        and b.get("dueDay") is not None
        and (b.get("dueAmount") or b.get("defaultBudget"))
    ]
    freq_bills = [
        b for b in buckets
        if not b.get("archived")
        and b.get("dueDay") is None
        and b.get("payFreq") in ('weekly', 'biweekly', 'triweekly', 'monthly')
        and (b.get("dueAmount") or b.get("defaultBudget"))
    ]

    def _bill_amount(b: dict) -> float:
        return float(b.get("dueAmount") or b.get("defaultBudget") or 0)

    # ── Running cumulative totals per transfer rule across all periods ───────
    rule_cumulative: dict = {}   # rule_name → running cumulative total

    # ── Build period results ────────────────────────────────────────────────
    running_balance = budget_bal
    period_results  = []

    for period_idx, (ps, pe, is_gap) in enumerate(periods_meta):
        period_start_balance = running_balance

        is_first_paycheck_today = (period_idx == 0 and not is_gap and ps == today)
        skip_income = is_first_paycheck_today and skip_today_income

        # ── Income, external transfers, internal allocation events ──────────
        income_events   = []
        transfer_events = []  # external rules → deduct from balance
        alloc_events    = []  # internal rules → also deduct from balance

        if not is_gap and ps in pay_events:
            for pc_hit in pay_events[ps]:
                if not skip_income:
                    running_balance += pc_hit["amount"]
                    income_events.append({"label": pc_hit["label"], "amount": pc_hit["amount"]})

                    # External transfers
                    for xfr in pc_hit["transfers"]:
                        running_balance -= xfr["amount"]
                        rule_cumulative[xfr["name"]] = round(
                            rule_cumulative.get(xfr["name"], 0) + xfr["amount"], 2)
                        transfer_events.append({
                            "name":       xfr["name"],
                            "amount":     xfr["amount"],
                            "cumulative": rule_cumulative[xfr["name"]],
                        })

                    # Internal allocation rules — only vault buckets move cash
                    for ae in pc_hit.get("alloc_events", []):
                        if ae.get("is_vault"):
                            running_balance -= ae["amount"]
                        rule_cumulative[ae["bucket"]] = round(
                            rule_cumulative.get(ae["bucket"], 0) + ae["amount"], 2)
                        alloc_events.append({
                            "bucket":     ae["bucket"],
                            "amount":     ae["amount"],
                            "cumulative": rule_cumulative[ae["bucket"]],
                            "is_vault":   ae.get("is_vault", False),
                        })

        # Record balance after income/transfers (before bills)
        balance_after_transfers = running_balance

        # ── Collect bills for this period ───────────────────────────────────
        funded_by_day:   dict = {}
        unfunded_by_day: dict = {}

        def _add_bill(b: dict, bd: date, overdue: bool = False) -> None:
            if _bill_paid(b["id"], bd):
                return
            amt = _bill_amount(b)
            display_date = today if (overdue and is_gap) else bd
            funded = _bill_funded(b["id"], bd)
            row = {"name": b["name"], "amount": amt, "overdue": overdue}
            if funded:
                funded_by_day.setdefault(display_date, []).append(row)
            else:
                unfunded_by_day.setdefault(display_date, []).append(row)

        # Dated bills — in gap period also scan back to start of month for overdue
        overdue_start = date(today.year, today.month, 1) if is_gap else ps
        for b in dated_bills:
            if _bill_amount(b) <= 0:
                continue
            for bd in _bill_dates_in_range(b["dueDay"], b.get("payFreq"), overdue_start, pe):
                _add_bill(b, bd, overdue=is_gap and bd < today)

        # Frequency-only bills (groceries, gas, etc.) — always anchor to period start
        for b in freq_bills:
            if _bill_amount(b) <= 0:
                continue
            for bd in _freq_only_dates_in_range(b["payFreq"], ps, pe):
                _add_bill(b, bd)

        # Process funded days (green section)
        funded_days = []
        for d in sorted(funded_by_day.keys()):
            for bill in funded_by_day[d]:
                running_balance -= bill["amount"]
            funded_days.append({
                "date":        str(d),
                "label":       _fc_date_label(d),
                "events":      funded_by_day[d],
                "run_balance": round(running_balance, 2),
            })

        # Process unfunded days (red section)
        unfunded_days = []
        for d in sorted(unfunded_by_day.keys()):
            for bill in unfunded_by_day[d]:
                running_balance -= bill["amount"]
            unfunded_days.append({
                "date":        str(d),
                "label":       _fc_date_label(d),
                "events":      unfunded_by_day[d],
                "run_balance": round(running_balance, 2),
            })

        period_income       = sum(e["amount"] for e in income_events)
        period_transfers    = sum(e["amount"] for e in transfer_events)
        period_vault_allocs = sum(e["amount"] for e in alloc_events if e.get("is_vault"))
        period_cleared      = sum(b["amount"] for d in funded_days  for b in d["events"])
        period_unfunded     = sum(b["amount"] for d in unfunded_days for b in d["events"])
        # Net = income minus cash moves and unfunded obligations only.
        # Funded clearings are real outflows but already handled — excluded from the pressure signal.
        period_net          = period_income - period_transfers - period_vault_allocs - period_unfunded

        if is_gap or skip_income:
            label = "Pre-Paycheck Gap"
            ptype = "gap"
        else:
            labels = list({e["label"] for e in income_events}) or ["Paycheck"]
            label  = " + ".join(labels)
            ptype  = "paycheck"

        period_results.append({
            "type":                   ptype,
            "label":                  label,
            "date_range":             _fc_range_label(ps, pe),
            "start":                  str(ps),
            "end":                    str(pe),
            "start_balance":          round(period_start_balance, 2),
            "balance_after_transfers": round(balance_after_transfers, 2),
            "income_events":          income_events,
            "transfer_events":        transfer_events,
            "alloc_events":           alloc_events,
            "funded_days":            funded_days,
            "unfunded_days":          unfunded_days,
            "period_income":          round(period_income, 2),
            "period_transfers":       round(period_transfers + period_vault_allocs, 2),
            "period_cleared":         round(period_cleared, 2),
            "period_unfunded":        round(period_unfunded, 2),
            "period_net":             round(period_net, 2),
            "end_balance":            round(running_balance, 2),
            "shortfall":              running_balance < 0,
            "can_toggle_paid":        is_first_paycheck_today,
        })

    # Per-period forward minimum: safe_to_spend[i] = min(end_balance[i], end_balance[i+1], ...)
    end_balances = [p["end_balance"] for p in period_results]
    running_min  = float("inf")
    fwd_mins     = [0.0] * len(period_results)
    for i in range(len(period_results) - 1, -1, -1):
        running_min = min(running_min, end_balances[i])
        fwd_mins[i] = running_min
    for i, p in enumerate(period_results):
        p["safe_to_spend"] = round(fwd_mins[i], 2)

    safe_to_spend = fwd_mins[0] if fwd_mins else budget_bal

    return jsonify({
        "ok":               True,
        "start_balance":    round(budget_bal, 2),
        "safe_to_spend":    round(safe_to_spend, 2),
        "months":           months_param,
        "periods":          period_results,
        "account_balances": account_balances,
    })


# ── API: Coach AI ─────────────────────────────────────────────────────────────

@app.route("/api/coach", methods=["POST"])
def api_coach():
    global _coach_rpm_times, _coach_rpd_count, _coach_rpd_date

    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    # Accept key from request body (client-stored) or fall back to server env var
    _body_pre = request.get_json(silent=True) or {}
    api_key = (
        (_body_pre.get('api_key') or '').strip()
        or os.environ.get('GEMINI_API_KEY')
        or os.environ.get('GOOGLE_API_KEY')
    )
    if not api_key:
        return jsonify({'error': 'No Coach AI key found. Go to More → Setup → Coach AI to add one.'}), 200

    # Rate limiting: 15 RPM, 1500 RPD
    now = _time.time()
    today = _time.strftime('%Y-%m-%d')

    # RPD reset
    if _coach_rpd_date != today:
        _coach_rpd_date = today
        _coach_rpd_count = 0

    # RPM: keep only last 60s
    while _coach_rpm_times and now - _coach_rpm_times[0] > 60:
        _coach_rpm_times.popleft()

    if _coach_rpd_count >= 1500:
        return jsonify({'error': 'Daily limit reached. Try again tomorrow.'}), 200
    if len(_coach_rpm_times) >= 15:
        return jsonify({'error': 'Too many requests. Wait a moment and try again.'}), 200

    _coach_rpm_times.append(now)
    _coach_rpd_count += 1

    body = _body_pre
    user_msg = (body.get('message') or '').strip()
    history = body.get('history') or []
    if not user_msg:
        return jsonify({'error': 'No message.'}), 200

    uid, tok = _uid(), _tok()
    data = _load(uid, tok)

    all_months     = data.get("months", [])
    accounts       = data.get("accounts", [])
    txs            = data.get("txs", [])
    active_buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    cur_mid        = current_month_id()
    cur_month      = next(
        (m for m in all_months if m.get("id") == cur_mid),
        {"id": cur_mid, "allocations": {}, "budgets": {}, "rolloverReleased": {},
         "skippedBuckets": {}, "vaultWithdrawals": {}},
    )

    rts_val = ready_to_spend(cur_month, all_months, accounts, active_buckets, txs)
    aom_val = _age_of_money(data)

    acct_lines = []
    total_cash = 0.0
    for a in accounts:
        if a.get("archived"):
            continue
        bal = acct_balance(a, txs)
        if a.get("type") != "debt":
            total_cash += bal
        acct_lines.append(f"  {a.get('name','?')}: ${bal:,.2f} ({a.get('type','?')})")

    over_budget = []
    top_spending = []
    for b in active_buckets:
        if b.get("type") == "vault":
            continue
        bid    = b["id"]
        spent  = b_spent(cur_mid, bid, txs)
        budget = b_budget(cur_month, bid)
        if budget > 0 and spent > budget:
            over_budget.append((b.get("name","?"), spent - budget, spent, budget))
        if spent > 0:
            top_spending.append((b.get("name","?"), spent))

    over_budget.sort(key=lambda x: -x[1])
    top_spending.sort(key=lambda x: -x[1])

    over_lines = "\n".join(
        f"  {name}: spent ${spent:,.2f} / budget ${budget:,.2f} (over by ${over:,.2f})"
        for name, over, spent, budget in over_budget[:5]
    ) or "  None"
    spend_lines = "\n".join(
        f"  {name}: ${spent:,.2f}" for name, spent in top_spending[:5]
    ) or "  None"

    aom_str = f"{aom_val} days" if aom_val is not None else "unknown"

    ctx = f"""You are a friendly, concise personal finance coach inside the Budget Command app.

Current budget snapshot ({cur_mid}):
- Ready to Spend (RTS): ${rts_val:,.2f}
- Age of Money: {aom_str}
- Total cash on hand: ${total_cash:,.2f}

Account balances:
{chr(10).join(acct_lines) or '  No accounts'}

Top 5 over-budget buckets this month:
{over_lines}

Top 5 buckets by spending this month:
{spend_lines}

Give practical, specific advice based on these numbers. Be brief and conversational. Do not fabricate numbers not shown above."""

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    # Build conversation contents
    contents = []
    for h in history[-10:]:  # last 10 turns
        role = 'user' if h.get('role') == 'user' else 'model'
        contents.append(types.Content(role=role, parts=[types.Part(text=h.get('content', ''))]))
    contents.append(types.Content(role='user', parts=[types.Part(text=user_msg)]))

    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=ctx,
                max_output_tokens=512,
                temperature=0.7,
            )
        )
        reply = response.text or 'No response.'
    except Exception as e:
        return jsonify({'error': 'Coach unavailable: ' + str(e)[:80]}), 200

    return jsonify({'reply': reply})


# ── API: bill calendar ────────────────────────────────────────────────────────

@app.route("/api/bill-calendar")
def api_bill_calendar():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401

    uid, tok = _uid(), _tok()
    data = _load(uid, tok)
    active_buckets = [b for b in data.get("buckets", []) if not b.get("archived")]
    all_months = data.get("months", [])
    txs = data.get("txs", [])

    today = date.today()
    cur_mid = current_month_id()
    next_month = date(today.year + (today.month // 12), (today.month % 12) + 1, 1)
    next_mid = month_id(next_month.year, next_month.month - 1)

    def _bill_paid_in_month(b: dict, mid: str) -> bool:
        m = next((m for m in all_months if m.get("id") == mid), None)
        if not m:
            return False
        status = (m.get("budgets") or {}).get(b["id"])
        return status == "PAID"

    def _days_in_month(yr: int, mo: int) -> int:
        import calendar as _cal
        return _cal.monthrange(yr, mo)[1]

    bills = []
    for b in active_buckets:
        if b.get("type") in ("vault",):
            continue
        due_day = b.get("dueDay")
        amount = float(b.get("dueAmount") or b.get("defaultBudget") or 0)
        if not due_day or not amount:
            continue

        for mid in [cur_mid, next_mid]:
            yr, m0 = parse_month_id(mid)
            cal_month = m0 + 1  # 1-based

            if due_day == "eom":
                day_num = _days_in_month(yr, cal_month)
            else:
                try:
                    day_num = min(int(due_day), _days_in_month(yr, cal_month))
                except (ValueError, TypeError):
                    continue

            try:
                due_date = date(yr, cal_month, day_num)
            except ValueError:
                continue

            is_paid = _bill_paid_in_month(b, mid)
            is_past = due_date < today
            is_today = due_date == today

            if is_past and mid != cur_mid:
                continue  # skip past bills in next month (shouldn't happen)

            bills.append({
                "bucket_id":  b["id"],
                "name":       b.get("name", ""),
                "amount":     amount,
                "due_date":   due_date.isoformat(),
                "due_day":    day_num,
                "month_id":   mid,
                "paid":       is_paid,
                "past":       is_past,
                "today":      is_today,
            })

    bills.sort(key=lambda x: x["due_date"])
    return jsonify({"ok": True, "bills": bills})


# ── API: close / reopen month ─────────────────────────────────────────────────

@app.route("/api/close-month", methods=["POST"])
def api_close_month():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body = request.get_json(silent=True) or {}
    mid  = (body.get("mid") or "").strip()
    if not mid:
        return jsonify({"ok": False, "error": "Missing mid"}), 400
    uid, tok = _uid(), _tok()
    _ensure_month(uid, tok, mid)
    _db(tok).table("bcc_months").update({"closed": True}).eq("id", mid).eq("user_id", uid).execute()
    return jsonify({"ok": True})


@app.route("/api/reopen-month", methods=["POST"])
def api_reopen_month():
    if not logged_in():
        return jsonify({"ok": False, "error": "Not logged in"}), 401
    body = request.get_json(silent=True) or {}
    mid  = (body.get("mid") or "").strip()
    if not mid:
        return jsonify({"ok": False, "error": "Missing mid"}), 400
    uid, tok = _uid(), _tok()
    _db(tok).table("bcc_months").update({"closed": False}).eq("id", mid).eq("user_id", uid).execute()
    return jsonify({"ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_ENV") == "development")
