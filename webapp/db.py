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
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")


def client(token: str = "") -> Client:
    c = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    if token:
        c.postgrest.auth(token)
    return c


def _service_client() -> Client:
    """Service-role client — bypasses RLS. Only for schema migrations."""
    key = SUPABASE_SERVICE_KEY or SUPABASE_ANON_KEY
    return create_client(SUPABASE_URL, key)


def ensure_schema() -> None:
    """
    Idempotent — ensures bcc_scenarios table + RLS policy exist.
    Called once on app startup when SUPABASE_SERVICE_KEY is set.
    """
    if not SUPABASE_SERVICE_KEY:
        return
    try:
        sc = _service_client()
        sc.rpc("exec_sql", {"sql": """
            CREATE TABLE IF NOT EXISTS bcc_scenarios (
                id              TEXT PRIMARY KEY,
                user_id         UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
                name            TEXT NOT NULL,
                allocations     JSONB NOT NULL DEFAULT '{}',
                income_override NUMERIC(12,2),
                schedule        JSONB NOT NULL DEFAULT '{}',
                sort_order      INTEGER NOT NULL DEFAULT 0,
                created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
            ALTER TABLE bcc_scenarios ENABLE ROW LEVEL SECURITY;
            DO $$ BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_policies
                WHERE tablename = 'bcc_scenarios' AND policyname = 'bcc_scenarios_user_policy'
              ) THEN
                CREATE POLICY bcc_scenarios_user_policy ON bcc_scenarios
                  FOR ALL USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
              END IF;
            END $$;
        """}).execute()
    except Exception:
        pass  # best-effort; migration SQL in schema_migrations.sql is the canonical fix


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


def refresh_session(refresh_token: str) -> dict:
    """Exchange a refresh token for a new access token. Raises on failure."""
    c = client()
    resp = c.auth.refresh_session(refresh_token)
    return {
        "access_token":  resp.session.access_token,
        "refresh_token": resp.session.refresh_token,
        "expires_at":    resp.session.expires_at,
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
        "archived": b.get("archived", False),
        "openingBalance": float(b.get("opening_balance") or 0),
        "defaultBudget": float(b.get("default_budget") or 0),
        "dueDay": b.get("due_day"), "payFreq": b.get("pay_freq"),
        "targetAmount": float(b.get("target_amount") or 0),
        "targetDate": b.get("target_date") or "",
        "contribFreq": b.get("contrib_freq") or "",
        "recurring": bool(b.get("recurring")),
        "flex": bool(b.get("flex")),
        "notes": b.get("notes") or "",
        "order": b.get("sort_order", 0),
        "debtAccountId": b.get("debt_account_id") or "",
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
        "paycheckId": t.get("paycheck_id") or "",
        "reconciled": bool(t.get("reconciled")),
        "planned": t.get("planned", True),
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
        "paycheck_id": tx.get("paycheckId") or None,
        "debt_payment_account_id": tx.get("debtPaymentAccountId") or None,
        "planned": tx.get("planned", True),
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
        from .formulas import parse_month_id
        import calendar as _cal
        y, m0 = parse_month_id(mid)
        label = f"{_cal.month_name[m0 + 1]} {y}"
        c.table("bcc_months").insert({
            "id": mid, "user_id": uid,
            "year": y, "month": m0, "label": label,
        }).execute()


def upsert_bucket(uid: str, token: str, bid: str, fields: dict) -> None:
    """Patch one or more columns on a bucket row."""
    col_map = {
        "name": "name", "type": "type", "cat_id": "cat_id",
        "archived": "archived",
        "default_budget": "default_budget",
        "due_day": "due_day",
        "pay_freq": "pay_freq",
        "target_amount": "target_amount", "target_date": "target_date",
        "contrib_freq": "contrib_freq",
        "recurring": "recurring",
        "flex": "flex",
        "notes": "notes",
        "sort_order": "sort_order",
        "debt_account_id": "debt_account_id",
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
        "archived": False,
        "default_budget": 0, "sort_order": 999,
    }).execute()
    return bid


def toggle_handled(uid: str, token: str, mid: str, bid: str, currently_handled: bool) -> None:
    """Insert or delete a handled row for (month, bucket)."""
    tbl = client(token).table("bcc_month_handled")
    if currently_handled:
        tbl.delete().eq("user_id", uid).eq("month_id", mid).eq("bucket_id", bid).execute()
    else:
        tbl.upsert({"user_id": uid, "month_id": mid, "bucket_id": bid},
                   on_conflict="user_id,month_id,bucket_id").execute()


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


def update_paycheck(uid: str, token: str, pc_id: str, label: str, amount: float, freq: int, anchor_date: str) -> None:
    client(token).table("bcc_paychecks").update({
        "label": label, "amount": amount, "freq": freq,
        "anchor_date": anchor_date or None,
    }).eq("id", pc_id).eq("user_id", uid).execute()


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


def update_alloc_rule(uid: str, token: str, rule_id: str, name: str, rule_type: str,
                      value_type: str, value: float, bucket_id: str) -> None:
    client(token).table("bcc_allocation_rules").update({
        "name": name, "rule_type": rule_type,
        "value_type": value_type, "value": value,
        "bucket_id": bucket_id or None,
    }).eq("id", rule_id).eq("user_id", uid).execute()


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
    db.table("bcc_scenarios").update({
        "name": name, "allocations": allocations, "updated_at": "now()",
    }).eq("id", sid).eq("user_id", uid).execute()


def delete_scenario(uid: str, token: str, sid: str) -> None:
    db = client(token)
    db.table("bcc_scenarios").delete().eq("id", sid).eq("user_id", uid).execute()


def vault_transfer(uid: str, token: str, mid: str, from_bid: str, to_bid: str,
                   amount: float, new_from_alloc: float, new_to_alloc: float) -> None:
    """Reduce vault alloc, increase destination bucket alloc, record transfer."""
    import uuid as _uuid
    db = client(token)
    db.table("bcc_month_allocations").upsert({
        "user_id": uid, "month_id": mid, "bucket_id": from_bid, "amount": new_from_alloc,
    }, on_conflict="user_id,month_id,bucket_id").execute()
    db.table("bcc_month_allocations").upsert({
        "user_id": uid, "month_id": mid, "bucket_id": to_bid, "amount": new_to_alloc,
    }, on_conflict="user_id,month_id,bucket_id").execute()
    try:
        db.table("bcc_vault_transfers").insert({
            "id": f"vt_{_uuid.uuid4().hex[:10]}", "user_id": uid,
            "from_bucket_id": from_bid, "to_bucket_id": to_bid,
            "amount": amount, "month_id": mid, "reason": "planned",
        }).execute()
    except Exception:
        pass  # bcc_vault_transfers may not exist in all deploys


def vault_release_to_pool(uid: str, token: str, mid: str, bid: str,
                          amount: float, current_alloc: float) -> None:
    """Release vault savings back to RTS pool."""
    db = client(token)
    # Drain current month alloc first
    from_alloc = min(amount, current_alloc)
    remaining = round(amount - from_alloc, 2)
    new_alloc = round(current_alloc - from_alloc, 2)
    db.table("bcc_month_allocations").upsert({
        "user_id": uid, "month_id": mid, "bucket_id": bid, "amount": new_alloc,
    }, on_conflict="user_id,month_id,bucket_id").execute()
    # Any remaining comes from prior-month savings → record as vault withdrawal
    if remaining > 0:
        existing = db.table("bcc_month_vault_withdrawals").select("amount") \
            .eq("user_id", uid).eq("month_id", mid).eq("bucket_id", bid).execute().data or []
        existing_wd = float(existing[0]["amount"]) if existing else 0.0
        db.table("bcc_month_vault_withdrawals").upsert({
            "user_id": uid, "month_id": mid, "bucket_id": bid,
            "amount": round(existing_wd + remaining, 2),
        }, on_conflict="user_id,month_id,bucket_id").execute()


def log_vault_release(uid: str, token: str, mid: str, bid: str,
                      amount: float, reason: str, is_planned: bool) -> None:
    """Log a vault release reason for reporting. Best-effort — table may not exist."""
    import uuid as _uuid
    try:
        client(token).table("bcc_vault_release_log").insert({
            "id": f"vrl_{_uuid.uuid4().hex[:10]}",
            "user_id": uid,
            "month_id": mid,
            "bucket_id": bid,
            "amount": amount,
            "reason": reason,
            "is_planned": is_planned,
            "created_at": __import__("datetime").datetime.utcnow().isoformat(),
        }).execute()
    except Exception:
        pass  # table may not exist yet; migration in schema_migrations.sql


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

