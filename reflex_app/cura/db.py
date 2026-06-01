"""
Supabase data layer — no Flask dependency.
All functions are pure I/O: take uid + token, return dicts.
"""

import os
import uuid
from datetime import date
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL      = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")


def client(token: str = "") -> Client:
    c = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    if token:
        c.postgrest.auth(token)
    return c


def sign_in(email: str, password: str) -> dict:
    """Returns {access_token, user_id, user_email} or raises."""
    c = client()
    resp = c.auth.sign_in_with_password({"email": email, "password": password})
    return {
        "access_token": resp.session.access_token,
        "user_id": resp.user.id,
        "user_email": resp.user.email,
    }


def load_all(uid: str, token: str) -> dict:
    """Load every table for this user and assemble the canonical data dict."""
    db = client(token)
    eq = lambda tbl: db.table(tbl).select("*").eq("user_id", uid).execute().data or []

    accounts_raw   = eq("bcc_accounts")
    cats_raw       = eq("bcc_categories")
    buckets_raw    = eq("bcc_buckets")
    txs_raw        = eq("bcc_transactions")
    months_raw     = eq("bcc_months")
    allocs_raw     = eq("bcc_month_allocations")
    budgets_raw    = eq("bcc_month_budgets")
    rollrel_raw    = eq("bcc_month_rollover_released")
    skipped_raw    = eq("bcc_month_skipped")
    vaultwd_raw    = eq("bcc_month_vault_withdrawals")
    paychecks_raw  = eq("bcc_paychecks")
    rules_raw      = eq("bcc_allocation_rules")

    accounts = [{
        "id": a["id"], "name": a["name"], "type": a["type"],
        "color": a.get("color", "#3a7fc1"),
        "openingBalance": float(a.get("opening_balance") or 0),
        "archived": a.get("archived", False),
        "debtAPR": a.get("debt_apr"),
        "debtMinPayment": a.get("debt_min_payment"),
        "creditLimit": a.get("credit_limit"),
        "isPromo": bool(a.get("is_promo")),
        "promoEndDate": a.get("promo_end_date") or "",
    } for a in sorted(accounts_raw, key=lambda x: x.get("sort_order", 0))]

    cats = [{
        "id": c["id"], "name": c["name"],
        "color": c.get("color", ""), "order": c.get("sort_order", 0),
        "archived": bool(c.get("archived")),
    } for c in cats_raw]

    buckets = [{
        "id": b["id"], "name": b["name"], "type": b.get("type", "expense"),
        "catId": b.get("cat_id", ""),
        "rollover": b.get("rollover", False), "archived": b.get("archived", False),
        "openingBalance": float(b.get("opening_balance") or 0),
        "defaultBudget": float(b.get("default_budget") or 0),
        "dueDay": b.get("due_day"), "payFreq": b.get("pay_freq"),
        "dueAmount": float(b.get("due_amount") or 0),
        "targetAmount": float(b.get("target_amount") or 0),
        "targetDate": b.get("target_date") or "",
        "contribFreq": b.get("contrib_freq") or "",
        "recurring": bool(b.get("recurring")),
        "notes": b.get("notes") or "",
        "order": b.get("sort_order", 0),
    } for b in sorted(buckets_raw, key=lambda x: x.get("sort_order", 0))]

    txs = [{
        "id": t["id"], "accountId": t.get("account_id", ""),
        "monthId": t.get("month_id", ""), "type": t.get("type", "out"),
        "amount": float(t.get("amount") or 0),
        "date": t.get("date") or "", "desc": t.get("description") or "",
        "bucketId": t.get("bucket_id") or "",
        "toAccountId": t.get("to_account_id") or "",
        "debtPaymentAccountId": t.get("debt_payment_account_id") or "",
        "incomeType": t.get("income_type") or "paycheck",
        "reconciled": bool(t.get("reconciled")),
    } for t in txs_raw]

    # Build month objects with nested allocations/budgets/etc.
    alloc_by_mid: dict[str, dict] = {}
    for a in allocs_raw:
        alloc_by_mid.setdefault(a["month_id"], {})[a["bucket_id"]] = float(a.get("amount") or 0)

    budget_by_mid: dict[str, dict] = {}
    for b in budgets_raw:
        budget_by_mid.setdefault(b["month_id"], {})[b["bucket_id"]] = float(b.get("amount") or 0)

    rollrel_by_mid: dict[str, dict] = {}
    for r in rollrel_raw:
        rollrel_by_mid.setdefault(r["month_id"], {})[r["bucket_id"]] = float(r.get("amount") or 0)

    skipped_by_mid: dict[str, dict] = {}
    for s in skipped_raw:
        skipped_by_mid.setdefault(s["month_id"], {})[s["bucket_id"]] = bool(s.get("skipped"))

    vault_by_mid: dict[str, dict] = {}
    for v in vaultwd_raw:
        vault_by_mid.setdefault(v["month_id"], {})[v["bucket_id"]] = float(v.get("amount") or 0)

    months = [{
        "id": m["id"], "closed": bool(m.get("closed")),
        "closing_snapshot": m.get("closing_snapshot") or {},
        "allocations": alloc_by_mid.get(m["id"], {}),
        "budgets": budget_by_mid.get(m["id"], {}),
        "rolloverReleased": rollrel_by_mid.get(m["id"], {}),
        "skippedBuckets": skipped_by_mid.get(m["id"], {}),
        "vaultWithdrawals": vault_by_mid.get(m["id"], {}),
    } for m in months_raw]

    return {
        "accounts": accounts, "cats": cats, "buckets": buckets,
        "txs": txs, "months": months,
        "paychecks": paychecks_raw, "allocationRules": rules_raw,
    }


def insert_transaction(uid: str, token: str, tx: dict) -> str:
    """Insert transaction, return new ID."""
    tx_id = f"tx_{uuid.uuid4().hex[:12]}"
    client(token).table("bcc_transactions").insert({
        "id": tx_id, "user_id": uid,
        "account_id": tx["accountId"], "month_id": tx["monthId"],
        "type": tx["type"], "amount": tx["amount"],
        "date": tx["date"], "description": tx.get("desc") or "",
        "bucket_id": tx.get("bucketId") or None,
        "to_account_id": tx.get("toAccountId") or None,
        "income_type": tx.get("incomeType") or None,
        "debt_payment_account_id": tx.get("debtPaymentAccountId") or None,
    }).execute()
    return tx_id


def delete_transaction(uid: str, token: str, tx_id: str) -> None:
    client(token).table("bcc_transactions").delete().eq("id", tx_id).eq("user_id", uid).execute()


def update_transaction(uid: str, token: str, tx_id: str, fields: dict) -> None:
    client(token).table("bcc_transactions").update(fields).eq("id", tx_id).eq("user_id", uid).execute()


def upsert_alloc(uid: str, token: str, mid: str, bid: str, amount: float) -> None:
    client(token).table("bcc_month_allocations").upsert({
        "user_id": uid, "month_id": mid, "bucket_id": bid, "amount": amount,
    }, on_conflict="user_id,month_id,bucket_id").execute()


def ensure_month(uid: str, token: str, mid: str) -> None:
    c = client(token)
    existing = c.table("bcc_months").select("id").eq("id", mid).eq("user_id", uid).execute()
    if not existing.data:
        c.table("bcc_months").insert({"id": mid, "user_id": uid}).execute()


def update_bucket_order(uid: str, token: str, bid: str, sort_order: int) -> None:
    """Update only sort_order for an existing bucket (pure UPDATE, no INSERT path)."""
    client(token).table("bcc_buckets").update({"sort_order": sort_order}) \
        .eq("id", bid).eq("user_id", uid).execute()


def upsert_bucket(uid: str, token: str, bid: str, fields: dict) -> None:
    """Patch one or more columns on a bucket row."""
    col_map = {
        "name": "name", "type": "type", "cat_id": "cat_id",
        "rollover": "rollover", "archived": "archived",
        "default_budget": "default_budget",
        "due_day": "due_day", "due_amount": "due_amount",
        "pay_freq": "pay_freq",
        "target_amount": "target_amount", "target_date": "target_date",
        "contrib_freq": "contrib_freq",
        "recurring": "recurring",
        "notes": "notes",
        "sort_order": "sort_order",
    }
    payload: dict = {"id": bid, "user_id": uid}
    for k, v in fields.items():
        if k in col_map:
            payload[col_map[k]] = v
    client(token).table("bcc_buckets").upsert(
        payload, on_conflict="id"
    ).execute()


def insert_bucket(uid: str, token: str, name: str, cat_id: str, btype: str = "expense") -> str:
    bid = f"b_{uuid.uuid4().hex[:10]}"
    client(token).table("bcc_buckets").insert({
        "id": bid, "user_id": uid, "name": name,
        "cat_id": cat_id, "type": btype,
        "rollover": False, "archived": False,
        "default_budget": 0, "sort_order": 999,
    }).execute()
    return bid


def upsert_budget(uid: str, token: str, mid: str, bid: str, amount: float) -> None:
    client(token).table("bcc_month_budgets").upsert({
        "user_id": uid, "month_id": mid, "bucket_id": bid, "amount": amount,
    }, on_conflict="user_id,month_id,bucket_id").execute()


def insert_category(uid: str, token: str, name: str, color: str) -> str:
    cid = f"c_{uuid.uuid4().hex[:10]}"
    client(token).table("bcc_categories").insert({
        "id": cid, "user_id": uid, "name": name,
        "color": color, "sort_order": 999,
    }).execute()
    return cid


def upsert_vault_withdrawal(uid: str, token: str, mid: str, bid: str, amount: float) -> None:
    client(token).table("bcc_month_vault_withdrawals").upsert({
        "user_id": uid, "month_id": mid, "bucket_id": bid, "amount": amount,
    }, on_conflict="user_id,month_id,bucket_id").execute()


def insert_paycheck(uid: str, token: str, label: str, amount: float, freq: int, anchor_date: str) -> str:
    pc_id = f"pc_{uuid.uuid4().hex[:10]}"
    existing = client(token).table("bcc_paychecks").select("sort_order").eq("user_id", uid).order("sort_order", desc=True).limit(1).execute().data or []
    sort_order = (existing[0]["sort_order"] + 1) if existing else 1
    client(token).table("bcc_paychecks").insert({
        "id": pc_id, "user_id": uid, "label": label, "amount": amount,
        "freq": freq, "anchor_date": anchor_date or None, "sort_order": sort_order,
    }).execute()
    return pc_id


def delete_paycheck(uid: str, token: str, pc_id: str) -> None:
    client(token).table("bcc_paychecks").delete().eq("id", pc_id).eq("user_id", uid).execute()


def insert_alloc_rule(uid: str, token: str, name: str, rule_type: str, value_type: str, value: float, bucket_id: str) -> str:
    rule_id = f"rule_{uuid.uuid4().hex[:10]}"
    existing = client(token).table("bcc_allocation_rules").select("sort_order").eq("user_id", uid).order("sort_order", desc=True).limit(1).execute().data or []
    sort_order = (existing[0]["sort_order"] + 1) if existing else 1
    client(token).table("bcc_allocation_rules").insert({
        "id": rule_id, "user_id": uid, "name": name,
        "rule_type": rule_type, "value_type": value_type,
        "value": value, "bucket_id": bucket_id or None,
        "active": True, "sort_order": sort_order,
    }).execute()
    return rule_id


def toggle_alloc_rule(uid: str, token: str, rule_id: str) -> bool:
    res = client(token).table("bcc_allocation_rules").select("active").eq("id", rule_id).eq("user_id", uid).execute()
    if not res.data:
        raise ValueError("Rule not found")
    new_active = not res.data[0]["active"]
    client(token).table("bcc_allocation_rules").update({"active": new_active}).eq("id", rule_id).eq("user_id", uid).execute()
    return new_active


def delete_alloc_rule(uid: str, token: str, rule_id: str) -> None:
    client(token).table("bcc_allocation_rules").delete().eq("id", rule_id).eq("user_id", uid).execute()


def is_auth_error(e: Exception) -> bool:
    keywords = ("jwt", "expired", "invalid token", "401", "unauthorized", "not authenticated")
    return any(k in str(e).lower() for k in keywords)


# ── What-If Scenarios ─────────────────────────────────────────────────────────

def list_scenarios(uid: str, token: str) -> list[dict]:
    """List all What-If scenarios for this user."""
    db = client(token)
    rows = db.table("bcc_scenarios").select("*").eq("user_id", uid).order("created_at").execute().data or []
    return [
        {"id": r["id"], "name": r.get("name", "Unnamed"),
         "allocations": r.get("allocations") or {}}
        for r in rows
    ]


def save_scenario(uid: str, token: str, name: str, allocations: dict) -> str:
    """Insert a new named What-If scenario. Returns the new scenario ID."""
    db = client(token)
    sid = str(uuid.uuid4())
    db.table("bcc_scenarios").insert({
        "id": sid, "user_id": uid, "name": name, "allocations": allocations,
    }).execute()
    return sid


def update_scenario(uid: str, token: str, sid: str, name: str, allocations: dict) -> None:
    db = client(token)
    db.table("bcc_scenarios").update({"name": name, "allocations": allocations}) \
      .eq("id", sid).eq("user_id", uid).execute()


def delete_scenario(uid: str, token: str, sid: str) -> None:
    db = client(token)
    db.table("bcc_scenarios").delete().eq("id", sid).eq("user_id", uid).execute()


# ── Auth ──────────────────────────────────────────────────────────────────────

def sign_up(email: str, password: str) -> dict:
    """Register a new user. Returns {access_token, user_id, user_email} or raises."""
    c = client()
    resp = c.auth.sign_up({"email": email, "password": password})
    if not resp.session:
        raise ValueError("Check your email to confirm your account, then sign in.")
    return {
        "access_token": resp.session.access_token,
        "user_id": resp.user.id,
        "user_email": resp.user.email,
    }


# ── Accounts ──────────────────────────────────────────────────────────────────

def insert_account(uid: str, token: str, name: str, atype: str,
                   color: str, opening_balance: float = 0.0) -> str:
    aid = f"a_{uuid.uuid4().hex[:10]}"
    existing = client(token).table("bcc_accounts").select("sort_order") \
        .eq("user_id", uid).order("sort_order", desc=True).limit(1).execute().data or []
    sort_order = (existing[0]["sort_order"] + 1) if existing else 1
    client(token).table("bcc_accounts").insert({
        "id": aid, "user_id": uid, "name": name, "type": atype,
        "color": color, "opening_balance": opening_balance,
        "archived": False, "sort_order": sort_order,
    }).execute()
    return aid


def update_account(uid: str, token: str, aid: str, fields: dict) -> None:
    col_map = {
        "name": "name", "type": "type", "color": "color",
        "opening_balance": "opening_balance",
        "debt_apr": "debt_apr", "debt_min_payment": "debt_min_payment",
        "credit_limit": "credit_limit",
        "is_promo": "is_promo", "promo_end_date": "promo_end_date",
        "archived": "archived",
    }
    payload = {col_map[k]: v for k, v in fields.items() if k in col_map}
    if payload:
        client(token).table("bcc_accounts").update(payload) \
            .eq("id", aid).eq("user_id", uid).execute()


def insert_debt_payment(uid: str, token: str, debt_aid: str, from_aid: str,
                        amount: float, pay_date: str, mid: str,
                        debt_name: str, bucket_id: str = "") -> str:
    tx_id = f"tx_{uuid.uuid4().hex[:12]}"
    client(token).table("bcc_transactions").insert({
        "id": tx_id, "user_id": uid,
        "account_id": from_aid, "month_id": mid,
        "type": "out", "amount": amount,
        "date": pay_date,
        "description": f"Payment — {debt_name}",
        "bucket_id": bucket_id or None,
        "debt_payment_account_id": debt_aid,
    }).execute()
    return tx_id


# ── Categories ────────────────────────────────────────────────────────────────

def update_category(uid: str, token: str, cid: str, fields: dict) -> None:
    col_map = {"name": "name", "color": "color", "archived": "archived"}
    payload = {col_map[k]: v for k, v in fields.items() if k in col_map}
    if payload:
        client(token).table("bcc_categories").update(payload) \
            .eq("id", cid).eq("user_id", uid).execute()


def update_category_order(uid: str, token: str, cid: str, sort_order: int) -> None:
    client(token).table("bcc_categories").update({"sort_order": sort_order}) \
        .eq("id", cid).eq("user_id", uid).execute()


# ── Month workflow ────────────────────────────────────────────────────────────

def copy_month_allocs(uid: str, token: str, dst_mid: str, src_mid: str) -> None:
    """Copy allocation rows from src_mid → dst_mid, skipping already-set buckets."""
    db = client(token)
    src = db.table("bcc_month_allocations").select("*") \
        .eq("user_id", uid).eq("month_id", src_mid).execute().data or []
    if not src:
        return
    existing_bids = {
        r["bucket_id"] for r in
        (db.table("bcc_month_allocations").select("bucket_id")
           .eq("user_id", uid).eq("month_id", dst_mid).execute().data or [])
    }
    rows = [
        {"user_id": uid, "month_id": dst_mid,
         "bucket_id": r["bucket_id"], "amount": r["amount"]}
        for r in src if r["bucket_id"] not in existing_bids
    ]
    if rows:
        db.table("bcc_month_allocations").insert(rows).execute()


def close_month(uid: str, token: str, mid: str, accounts: list, txs: list) -> None:
    from datetime import date as _date
    from .formulas import acct_balance as _bal, is_scheduled as _sched
    cash = sum(_bal(a, txs) for a in accounts if a.get("type") != "debt" and not a.get("archived"))
    debt = sum(_bal(a, txs) for a in accounts if a.get("type") == "debt" and not a.get("archived"))
    income = sum(float(t.get("amount", 0)) for t in txs
                 if t.get("monthId") == mid and t.get("type") == "in" and not _sched(t))
    spent  = sum(float(t.get("amount", 0)) for t in txs
                 if t.get("monthId") == mid and t.get("type") == "out" and not _sched(t))
    snapshot = {"date": str(_date.today()), "cash": round(cash, 2),
                "net_worth": round(cash - debt, 2), "debt_total": round(debt, 2),
                "income": round(income, 2), "spent": round(spent, 2)}
    client(token).table("bcc_months").update({
        "closed": True, "closing_snapshot": snapshot,
        "closing_date": str(_date.today()),
    }).eq("id", mid).eq("user_id", uid).execute()


def reopen_month(uid: str, token: str, mid: str) -> None:
    client(token).table("bcc_months").update({"closed": False}) \
        .eq("id", mid).eq("user_id", uid).execute()


# ── Payees ────────────────────────────────────────────────────────────────────

def get_payees(uid: str, token: str) -> list:
    rows = client(token).table("bcc_transactions").select("description") \
        .eq("user_id", uid).execute().data or []
    seen, result = set(), []
    for r in rows:
        d = (r.get("description") or "").strip()
        if d and d not in seen:
            seen.add(d)
            result.append(d)
    return sorted(result, key=str.lower)

