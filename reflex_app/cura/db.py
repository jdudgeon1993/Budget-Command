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
        "notes": b.get("notes") or "",
        "order": b.get("sort_order", 0),
    } for b in sorted(buckets_raw, key=lambda x: x.get("sort_order", 0))]

    txs = [{
        "id": t["id"], "accountId": t.get("account_id", ""),
        "monthId": t.get("month_id", ""), "type": t.get("type", "out"),
        "amount": float(t.get("amount") or 0),
        "date": t.get("date") or "", "desc": t.get("desc") or "",
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
        "date": tx["date"], "desc": tx["desc"],
        "bucket_id": tx.get("bucketId") or None,
        "to_account_id": tx.get("toAccountId") or None,
        "income_type": tx.get("incomeType") or None,
    }).execute()
    return tx_id


def delete_transaction(uid: str, token: str, tx_id: str) -> None:
    client(token).table("bcc_transactions").delete().eq("id", tx_id).eq("user_id", uid).execute()


def upsert_alloc(uid: str, token: str, mid: str, bid: str, amount: float) -> None:
    client(token).table("bcc_month_allocations").upsert({
        "user_id": uid, "month_id": mid, "bucket_id": bid, "amount": amount,
    }, on_conflict="user_id,month_id,bucket_id").execute()


def ensure_month(uid: str, token: str, mid: str) -> None:
    client(token).table("bcc_months").upsert(
        {"id": mid, "user_id": uid}, on_conflict="id"
    ).execute()


def upsert_bucket(uid: str, token: str, bid: str, fields: dict) -> None:
    """Patch one or more columns on a bucket row."""
    col_map = {
        "name": "name", "type": "type", "cat_id": "cat_id",
        "rollover": "rollover", "archived": "archived",
        "default_budget": "default_budget",
        "due_day": "due_day", "due_amount": "due_amount",
        "pay_freq": "pay_freq",
        "target_amount": "target_amount", "target_date": "target_date",
        "notes": "notes",
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


def is_auth_error(e: Exception) -> bool:
    keywords = ("jwt", "expired", "invalid token", "401", "unauthorized", "not authenticated")
    return any(k in str(e).lower() for k in keywords)
