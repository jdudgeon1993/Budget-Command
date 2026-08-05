"""Cadence Supabase I/O — the exact proven queries copied from Cura's db.py.
Self-contained so this service builds from the cadence/ directory alone."""

"""
Supabase data layer — no Flask dependency.
All functions are pure I/O: take uid + token, return dicts.
"""

import os
import uuid
import threading
from datetime import date
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL         = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY    = os.environ.get("SUPABASE_ANON_KEY", "")


# Column allow-lists for moving rows between the live and quarantine tables.
# The live tables have drifted to carry extra legacy columns (e.g.
# opening_balance) that the quarantine tables don't; copying a raw SELECT *
# row across would make PostgREST reject the whole write. These are the
# columns each destination table actually accepts (retired_at is defaulted).
_RETIRED_BUCKET_COLS = frozenset({
    "id", "user_id", "cat_id", "name", "type", "rollover", "recurring",
    "due_day", "due_amount", "pay_freq", "default_budget",
    "target_amount", "target_date", "contrib_freq", "notes", "flex",
    "archived", "sort_order", "created_at",
})
_LIVE_BUCKET_COLS = _RETIRED_BUCKET_COLS  # same columns on the way back
_RETIRED_CATEGORY_COLS = frozenset({
    "id", "user_id", "name", "color", "archived", "sort_order", "created_at",
})
_LIVE_CATEGORY_COLS = _RETIRED_CATEGORY_COLS


def _shape_bucket(b: dict) -> dict:
    """Raw bcc_buckets/bcc_retired_buckets row → the app's bucket dict shape.
    Shared so retired buckets are drop-in compatible with live ones."""
    return {
        "id": b["id"], "name": b["name"], "type": b.get("type", "expense"),
        "catId": b.get("cat_id", ""),
        "archived": b.get("archived", False),
        "openingBalance": float(b.get("opening_balance") or 0),
        "defaultBudget": float(b.get("default_budget") or 0),
        "dueDay": b.get("due_day"), "payFreq": b.get("pay_freq"),
        "dueAmount": float(b.get("due_amount") or 0),
        "targetAmount": float(b.get("target_amount") or 0),
        "targetDate": b.get("target_date") or "",
        "contribFreq": b.get("contrib_freq") or "",
        "recurring": bool(b.get("recurring")),
        "flex": bool(b.get("flex")),
        "notes": b.get("notes") or "",
        "order": b.get("sort_order", 0),
        "retiredAt": b.get("retired_at") or "",
    }


def client(token: str = "") -> Client:
    c = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    if token:
        c.postgrest.auth(token)
    return c


def sign_in(email: str, password: str) -> dict:
    """Returns {access_token, refresh_token, expires_at, user_id, user_email} or raises."""
    c = client()
    resp = c.auth.sign_in_with_password({"email": email, "password": password})
    return {
        "access_token":  resp.session.access_token,
        "refresh_token": resp.session.refresh_token,
        "expires_at":    resp.session.expires_at,
        "user_id":       resp.user.id,
        "user_email":    resp.user.email,
    }


def load_all(uid: str, token: str, tx_months: int = 13) -> dict:
    """Load every table for this user and assemble the canonical data dict.

    Queries run in parallel threads to eliminate sequential latency.
    Transactions are windowed to the most recent tx_months (default 13 — current
    month + 12 prior) so the payload stays small regardless of account age.
    Reports that need full history call load_all(tx_months=0).
    """
    db = client(token)

    # Compute the earliest month_id we want transactions for
    from .formulas import current_month_id, parse_month_id, month_id as _mid
    if tx_months > 0:
        cy, cm = parse_month_id(current_month_id())
        total = cy * 12 + cm - (tx_months - 1)
        cutoff_mid = _mid(total // 12, total % 12)
    else:
        cutoff_mid = None

    results: dict = {}
    errors: list = []

    def fetch(key: str, tbl: str, extra=None):
        try:
            q = db.table(tbl).select("*").eq("user_id", uid)
            if extra:
                q = extra(q)
            results[key] = q.execute().data or []
        except Exception as e:
            errors.append((key, e))
            results[key] = []

    def fetch_txs():
        try:
            q = db.table("bcc_transactions").select("*").eq("user_id", uid)
            if cutoff_mid:
                q = q.gte("month_id", cutoff_mid)
            results["txs_raw"] = q.order("date", desc=True).execute().data or []
        except Exception as e:
            errors.append(("txs_raw", e))
            results["txs_raw"] = []

    threads = [
        threading.Thread(target=fetch, args=("accounts_raw",  "bcc_accounts")),
        threading.Thread(target=fetch, args=("cats_raw",      "bcc_categories")),
        threading.Thread(target=fetch, args=("buckets_raw",   "bcc_buckets")),
        threading.Thread(target=fetch, args=("months_raw",    "bcc_months")),
        threading.Thread(target=fetch, args=("allocs_raw",    "bcc_month_allocations")),
        threading.Thread(target=fetch, args=("budgets_raw",   "bcc_month_budgets")),
        threading.Thread(target=fetch, args=("handled_raw",   "bcc_month_handled")),
        threading.Thread(target=fetch, args=("vaultwd_raw",   "bcc_month_vault_withdrawals")),
        threading.Thread(target=fetch, args=("paychecks_raw", "bcc_paychecks")),
        threading.Thread(target=fetch, args=("rules_raw",     "bcc_allocation_rules")),
        threading.Thread(target=fetch_txs),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    accounts_raw  = results.get("accounts_raw", [])
    cats_raw      = results.get("cats_raw", [])
    buckets_raw   = results.get("buckets_raw", [])
    txs_raw       = results.get("txs_raw", [])
    months_raw    = results.get("months_raw", [])
    allocs_raw    = results.get("allocs_raw", [])
    budgets_raw   = results.get("budgets_raw", [])
    handled_raw   = results.get("handled_raw", [])
    vaultwd_raw   = results.get("vaultwd_raw", [])
    paychecks_raw = results.get("paychecks_raw", [])
    rules_raw     = results.get("rules_raw", [])

    accounts = [{
        "id": a["id"], "name": a["name"], "type": a["type"],
        "color": a.get("color", "#3a7fc1"),
        "openingBalance": float(a.get("opening_balance") or 0),
        "archived": a.get("archived", False),
    } for a in sorted(accounts_raw, key=lambda x: x.get("sort_order", 0))]

    cats = [{
        "id": c["id"], "name": c["name"],
        "color": c.get("color", ""), "order": c.get("sort_order", 0),
        "archived": bool(c.get("archived")),
    } for c in cats_raw]

    buckets = [_shape_bucket(b) for b in
               sorted(buckets_raw, key=lambda x: x.get("sort_order", 0))]

    txs = [{
        "id": t["id"], "accountId": t.get("account_id", ""),
        "monthId": t.get("month_id", ""), "type": t.get("type", "out"),
        "amount": float(t.get("amount") or 0),
        "date": t.get("date") or "", "desc": t.get("description") or "",
        "bucketId": t.get("bucket_id") or "",
        "toAccountId": t.get("to_account_id") or "",
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

    handled_by_mid: dict[str, dict] = {}
    for h in handled_raw:
        handled_by_mid.setdefault(h["month_id"], {})[h["bucket_id"]] = True

    vault_by_mid: dict[str, dict] = {}
    for v in vaultwd_raw:
        vault_by_mid.setdefault(v["month_id"], {})[v["bucket_id"]] = float(v.get("amount") or 0)

    months = [{
        "id": m["id"],
        "allocations": alloc_by_mid.get(m["id"], {}),
        "budgets": budget_by_mid.get(m["id"], {}),
        "handledBuckets": handled_by_mid.get(m["id"], {}),
        "vaultWithdrawals": vault_by_mid.get(m["id"], {}),
    } for m in months_raw]

    return {
        "accounts": accounts, "cats": cats, "buckets": buckets,
        "txs": txs, "months": months,
        "paychecks": paychecks_raw, "allocationRules": rules_raw,
    }


def upsert_alloc(uid: str, token: str, mid: str, bid: str, amount: float) -> None:
    client(token).table("bcc_month_allocations").upsert({
        "user_id": uid, "month_id": mid, "bucket_id": bid, "amount": amount,
    }, on_conflict="user_id,month_id,bucket_id").execute()


def ensure_month(uid: str, token: str, mid: str) -> None:
    c = client(token)
    existing = c.table("bcc_months").select("id").eq("id", mid).eq("user_id", uid).execute()
    if not existing.data:
        c.table("bcc_months").insert({"id": mid, "user_id": uid}).execute()


