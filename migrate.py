"""
Phase 10 Migration: bcc_budget_state blob → relational tables.

Reads all rows from bcc_budget_state, parses the JSON data blob for each user,
and upserts into the new relational tables. Idempotent — safe to run multiple times.
"""

import json
import os
import sys

from dotenv import load_dotenv
from supabase import create_client, Client

# ─── ENV SETUP ────────────────────────────────────────────────────────────────

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "app", ".env"))

SUPABASE_URL = os.environ.get("SUPABASE_URL")
if not SUPABASE_URL:
    print("ERROR: SUPABASE_URL not set in app/.env", file=sys.stderr)
    sys.exit(1)

SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
if SUPABASE_KEY:
    print("Using service role key (RLS bypassed for migration).")
else:
    SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY")
    if SUPABASE_KEY:
        print(
            "WARNING: SUPABASE_SERVICE_ROLE_KEY not found. "
            "Falling back to SUPABASE_ANON_KEY — RLS will be enforced. "
            "Migration may fail if the authenticated user does not own all rows.",
            file=sys.stderr,
        )
    else:
        print(
            "ERROR: Neither SUPABASE_SERVICE_ROLE_KEY nor SUPABASE_ANON_KEY is set.",
            file=sys.stderr,
        )
        sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def _str(val) -> str | None:
    """Coerce a value to string, returning None for falsy non-zero values."""
    if val is None:
        return None
    return str(val)


def upsert(table: str, rows: list[dict]) -> int:
    """Upsert a list of rows into the given table. Returns count inserted."""
    if not rows:
        return 0
    supabase.table(table).upsert(rows).execute()
    return len(rows)


# ─── PER-ENTITY MAPPERS ───────────────────────────────────────────────────────

def map_accounts(blob: dict, user_id: str) -> list[dict]:
    rows = []
    for a in blob.get("accounts", []):
        rows.append({
            "id":               a["id"],
            "user_id":          user_id,
            "name":             a.get("name", ""),
            "type":             a.get("type", "budget"),
            "color":            a.get("color", "#3a7fc1"),
            "opening_balance":  a.get("openingBalance", 0),
            "debt_apr":         a.get("debtAPR"),
            "debt_min_payment": a.get("debtMinPayment"),
            "credit_limit":     a.get("creditLimit"),
            "archived":         bool(a.get("archived", False)),
            "sort_order":       a.get("order", 0) or 0,
        })
    return rows


def map_categories(blob: dict, user_id: str) -> list[dict]:
    rows = []
    for c in blob.get("cats", []):
        rows.append({
            "id":         c["id"],
            "user_id":    user_id,
            "name":       c.get("name", ""),
            "color":      c.get("color", ""),
            "archived":   bool(c.get("archived", False)),
            "sort_order": c.get("order", 0) or 0,
        })
    return rows


def map_buckets(blob: dict, user_id: str) -> list[dict]:
    rows = []
    for b in blob.get("buckets", []):
        due_day = b.get("dueDay")
        rows.append({
            "id":               b["id"],
            "user_id":          user_id,
            "cat_id":           b.get("catId"),
            "name":             b.get("name", ""),
            "type":             b.get("type", "expense"),
            "rollover":         bool(b.get("rollover", False)),
            "recurring":        bool(b.get("recurring", False)),
            "due_day":          _str(due_day) if due_day is not None else None,
            "due_amount":       b.get("dueAmount"),
            "pay_freq":         b.get("payFreq"),
            "debt_account_id":  b.get("debtAccountId"),
            "target_amount":    b.get("targetAmount"),
            "target_date":      _str(b.get("targetDate")) if b.get("targetDate") is not None else None,
            "contrib_freq":     b.get("contribFreq"),
            "default_budget":   b.get("defaultBudget", 0) or 0,
            "notes":            b.get("notes"),
            "archived":         bool(b.get("archived", False)),
            "sort_order":       b.get("order", 0) or 0,
        })
    return rows


def map_transactions(blob: dict, user_id: str) -> list[dict]:
    rows = []
    for t in blob.get("txs", []):
        rows.append({
            "id":                       t["id"],
            "user_id":                  user_id,
            "date":                     t["date"],
            "description":              t.get("desc"),
            "type":                     t.get("type", "out"),
            "amount":                   t.get("amount", 0),
            "month_id":                 t["monthId"],
            "bucket_id":                t.get("bucketId"),
            "account_id":               t.get("accountId"),
            "to_account_id":            t.get("toAccountId"),
            "debt_payment_account_id":  t.get("debtPaymentAccountId"),
            "income_type":              t.get("incomeType"),
            "reconciled":               bool(t.get("reconciled", False)),
            "recurring":                bool(t.get("recurring", False)),
        })
    return rows


def map_months(blob: dict, user_id: str) -> list[dict]:
    rows = []
    for m in blob.get("months", []):
        rows.append({
            "id":      m["id"],
            "user_id": user_id,
            "year":    m["year"],
            "month":   m["month"],
            "label":   m["label"],
        })
    return rows


def map_month_allocations(blob: dict, user_id: str) -> list[dict]:
    rows = []
    for m in blob.get("months", []):
        month_id = m["id"]
        for bucket_id, amount in (m.get("allocations") or {}).items():
            rows.append({
                "user_id":   user_id,
                "month_id":  month_id,
                "bucket_id": bucket_id,
                "amount":    amount or 0,
            })
    return rows


def map_month_budgets(blob: dict, user_id: str) -> list[dict]:
    rows = []
    for m in blob.get("months", []):
        month_id = m["id"]
        for bucket_id, amount in (m.get("budgets") or {}).items():
            rows.append({
                "user_id":   user_id,
                "month_id":  month_id,
                "bucket_id": bucket_id,
                "amount":    amount or 0,
            })
    return rows


def map_month_rollover_released(blob: dict, user_id: str) -> list[dict]:
    rows = []
    for m in blob.get("months", []):
        month_id = m["id"]
        for bucket_id, amount in (m.get("rolloverReleased") or {}).items():
            rows.append({
                "user_id":   user_id,
                "month_id":  month_id,
                "bucket_id": bucket_id,
                "amount":    amount or 0,
            })
    return rows


def map_month_skipped(blob: dict, user_id: str) -> list[dict]:
    rows = []
    for m in blob.get("months", []):
        month_id = m["id"]
        for bucket_id, val in (m.get("skippedBuckets") or {}).items():
            if val:
                rows.append({
                    "user_id":   user_id,
                    "month_id":  month_id,
                    "bucket_id": bucket_id,
                })
    return rows


def map_month_vault_withdrawals(blob: dict, user_id: str) -> list[dict]:
    rows = []
    for m in blob.get("months", []):
        month_id = m["id"]
        for bucket_id, amount in (m.get("vaultWithdrawals") or {}).items():
            rows.append({
                "user_id":   user_id,
                "month_id":  month_id,
                "bucket_id": bucket_id,
                "amount":    amount or 0,
            })
    return rows


def map_paychecks(blob: dict, user_id: str) -> list[dict]:
    rows = []
    for p in blob.get("paychecks", []):
        rows.append({
            "id":          p["id"],
            "user_id":     user_id,
            "label":       p.get("label", ""),
            "amount":      p.get("amount", 0),
            "freq":        p.get("freq", 14),
            "anchor_date": p.get("anchorDate"),
            "sort_order":  p.get("sortOrder", 0) or 0,
        })
    return rows


def map_allocation_rules(blob: dict, user_id: str) -> list[dict]:
    rows = []
    for r in blob.get("allocationRules", []):
        rows.append({
            "id":         r["id"],
            "user_id":    user_id,
            "name":       r.get("name", ""),
            "rule_type":  r.get("ruleType", "internal"),
            "value_type": r.get("type", "fixed"),   # blob "type" → value_type column
            "value":      r.get("value", 0),
            "bucket_id":  r.get("bucketId"),
            "active":     bool(r.get("active", True)),
            "sort_order": r.get("sortOrder", 0) or 0,
        })
    return rows


def map_vault_transfers(blob: dict, user_id: str) -> list[dict]:
    rows = []
    for v in blob.get("vaultTransfers", []):
        rows.append({
            "id":             v["id"],
            "user_id":        user_id,
            "from_bucket_id": v["fromBucketId"],
            "to_bucket_id":   v["toBucketId"],
            "amount":         v["amount"],
            "month_id":       v["monthId"],
            "reason":         v.get("reason"),
        })
    return rows


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def migrate_user(user_id: str, blob: dict) -> dict:
    """Migrate a single user's blob. Returns a dict of table→count."""
    counts = {}

    counts["bcc_accounts"]               = upsert("bcc_accounts",               map_accounts(blob, user_id))
    counts["bcc_categories"]             = upsert("bcc_categories",             map_categories(blob, user_id))
    counts["bcc_buckets"]                = upsert("bcc_buckets",                map_buckets(blob, user_id))
    counts["bcc_transactions"]           = upsert("bcc_transactions",           map_transactions(blob, user_id))
    counts["bcc_months"]                 = upsert("bcc_months",                 map_months(blob, user_id))
    counts["bcc_month_allocations"]      = upsert("bcc_month_allocations",      map_month_allocations(blob, user_id))
    counts["bcc_month_budgets"]          = upsert("bcc_month_budgets",          map_month_budgets(blob, user_id))
    counts["bcc_month_rollover_released"]= upsert("bcc_month_rollover_released",map_month_rollover_released(blob, user_id))
    counts["bcc_month_skipped"]          = upsert("bcc_month_skipped",          map_month_skipped(blob, user_id))
    counts["bcc_month_vault_withdrawals"]= upsert("bcc_month_vault_withdrawals",map_month_vault_withdrawals(blob, user_id))
    counts["bcc_paychecks"]              = upsert("bcc_paychecks",              map_paychecks(blob, user_id))
    counts["bcc_allocation_rules"]       = upsert("bcc_allocation_rules",       map_allocation_rules(blob, user_id))
    counts["bcc_vault_transfers"]        = upsert("bcc_vault_transfers",        map_vault_transfers(blob, user_id))

    return counts


def main():
    print("Fetching rows from bcc_budget_state...")
    response = supabase.table("bcc_budget_state").select("user_id, data").execute()
    state_rows = response.data or []
    print(f"Found {len(state_rows)} user(s) to migrate.\n")

    totals: dict[str, int] = {}
    migrated_users = 0

    for row in state_rows:
        user_id = row["user_id"]
        raw_data = row.get("data")

        print(f"Migrating user {user_id}...")

        if raw_data is None:
            print(f"  WARNING: No data blob for user {user_id}, skipping.")
            continue

        if isinstance(raw_data, str):
            try:
                blob = json.loads(raw_data)
            except json.JSONDecodeError as exc:
                print(f"  ERROR: Failed to parse JSON for user {user_id}: {exc}", file=sys.stderr)
                continue
        else:
            blob = raw_data  # already a dict (Supabase may auto-parse jsonb)

        try:
            counts = migrate_user(user_id, blob)
        except Exception as exc:  # noqa: BLE001
            print(f"  ERROR during migration for user {user_id}: {exc}", file=sys.stderr)
            continue

        for table, count in counts.items():
            totals[table] = totals.get(table, 0) + count
            if count:
                print(f"  {table}: {count} row(s) upserted")

        migrated_users += 1

    print("\n── Migration Summary ─────────────────────────────────────────")
    print(f"Users processed: {migrated_users} / {len(state_rows)}")
    print("Rows upserted per table:")
    for table, count in sorted(totals.items()):
        print(f"  {table}: {count}")
    print("\nMigration complete. Verify your data before dropping bcc_budget_state.")


if __name__ == "__main__":
    main()
