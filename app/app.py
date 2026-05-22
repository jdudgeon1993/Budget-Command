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
    prev_mid = month_id(year - 1, 11) if m0 == 0 else month_id(year, m0 - 1)
    next_mid = month_id(year + 1, 0) if m0 == 11 else month_id(year, m0 + 1)

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

    return render_template(
        "dashboard.html",
        user_email=session.get("user_email"),
        active_mid=active_mid,
        month_display=f"{MONTH_NAMES[m0]} {year}",
        prev_mid=prev_mid, next_mid=next_mid,
        category_groups=category_groups, grand=grand, rts=rts,
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



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_ENV") == "development")
