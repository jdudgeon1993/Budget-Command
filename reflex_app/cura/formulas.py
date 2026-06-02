"""
Core formula functions, translated directly from FORMULAS.md.
All functions are pure — they take data as arguments, return a number.
No database calls here; queries happen in routes and pass data in.
"""

from datetime import date


# ── Safe coercers ─────────────────────────────────────────────────────────────

def _safe_date(v) -> "date | None":
    """Parse any date-like value to a date; return None on failure."""
    if v is None:
        return None
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v)[:10])
    except (ValueError, TypeError):
        return None


def _money(v) -> float:
    """Coerce any value to a non-negative float rounded to 2dp."""
    try:
        return round(float(v or 0), 2)
    except (ValueError, TypeError):
        return 0.0


# ── Month ID helpers ──────────────────────────────────────────────────────────

def month_id(year: int, month: int) -> str:
    """month is 0-indexed (JS convention). m_2025_0 = January 2025."""
    return f"m_{year}_{month}"


def current_month_id() -> str:
    today = date.today()
    return month_id(today.year, today.month - 1)


def parse_month_id(mid: str) -> tuple[int, int]:
    """Returns (year, month) where month is 0-indexed."""
    _, y, m = mid.split("_")
    return int(y), int(m)


def month_sort_key(mid: str) -> tuple[int, int]:
    return parse_month_id(mid)


def months_before(target_mid: str, all_months: list[dict]) -> list[dict]:
    ty, tm = parse_month_id(target_mid)
    return [
        m for m in all_months
        if month_sort_key(m["id"]) < (ty, tm)
    ]


def months_after(target_mid: str, all_months: list[dict]) -> list[dict]:
    ty, tm = parse_month_id(target_mid)
    return [
        m for m in all_months
        if month_sort_key(m["id"]) > (ty, tm)
    ]


def month_status(mid: str) -> str:
    """'past', 'present', or 'future' relative to today's calendar month."""
    cy, cm = parse_month_id(current_month_id())
    my, mm = parse_month_id(mid)
    if (my, mm) < (cy, cm):
        return "past"
    if (my, mm) > (cy, cm):
        return "future"
    return "present"


# ── Transaction helpers ───────────────────────────────────────────────────────

def is_scheduled(tx: dict) -> bool:
    """A transaction is scheduled (future-dated) if its date is after today."""
    d = _safe_date(tx.get("date"))
    return d is not None and d > date.today()


# ── 3.1 Account Balance ───────────────────────────────────────────────────────

def acct_balance(account: dict, transactions: list[dict]) -> float:
    mult = -1 if account["type"] == "debt" else 1
    acct_id = account["id"]

    # Opening balance: sum opening-type transactions if they total > 0, else use field.
    # Matches the old JS app's exact logic: openingTotal > 0 ? openingTotal : openingBalance
    opening_total = sum(
        float(t.get("amount") or 0)
        for t in transactions
        if t.get("accountId") == acct_id and t.get("type") == "opening"
    )
    balance = opening_total if opening_total > 0 else float(account.get("openingBalance") or 0)

    for t in transactions:
        if is_scheduled(t):
            continue
        if t.get("type") == "opening":
            continue

        amount = float(t.get("amount") or 0)

        if t.get("accountId") == acct_id:
            tx_type = t.get("type")
            if tx_type == "in":
                balance += mult * amount
            elif tx_type == "out":
                balance -= mult * amount
            elif tx_type == "xfr":
                balance -= mult * amount
            elif tx_type == "adjustment":
                balance += amount  # raw, no mult

        elif t.get("toAccountId") == acct_id and t.get("type") == "xfr":
            balance += mult * amount

        elif t.get("debtPaymentAccountId") == acct_id and t.get("type") == "out":
            balance -= amount  # reduces debt balance, no mult

    return balance


# ── 3.2 Budget Balance ────────────────────────────────────────────────────────

def budget_bal(accounts: list[dict], transactions: list[dict]) -> float:
    return sum(
        acct_balance(a, transactions)
        for a in accounts
        if a["type"] == "budget"
    )


# ── 3.4 / 3.5 Allocation and Budget ──────────────────────────────────────────

def b_alloc(month: dict, bucket_id: str) -> float:
    return float((month.get("allocations") or {}).get(bucket_id) or 0)


def b_budget(month: dict, bucket_id: str) -> float:
    return float((month.get("budgets") or {}).get(bucket_id) or 0)


# ── 3.6 Bucket Spent ─────────────────────────────────────────────────────────

def b_spent(month_id: str, bucket_id: str, transactions: list[dict]) -> float:
    return sum(
        float(t.get("amount") or 0)
        for t in transactions
        if t.get("monthId") == month_id
        and t.get("bucketId") == bucket_id
        and t.get("type") == "out"
        and not is_scheduled(t)
    )


# ── 3.7 Total Allocated ───────────────────────────────────────────────────────

def total_allocated(month: dict, buckets: list[dict]) -> float:
    return sum(
        b_alloc(month, b["id"])
        for b in buckets
        if not b.get("archived")
    )


# ── 3.8 Rollover Balance Raw ──────────────────────────────────────────────────

def rollover_bal_raw(
    bucket: dict,
    current_month_id: str,
    all_months: list[dict],
    transactions: list[dict],
) -> float:
    if not bucket.get("rollover"):
        return 0.0

    prior = months_before(current_month_id, all_months)
    total = 0.0
    bid = bucket["id"]

    for m in prior:
        skipped = (m.get("skippedBuckets") or {}).get(bid)
        if skipped:
            continue
        alloc = b_alloc(m, bid)
        released = float((m.get("rolloverReleased") or {}).get(bid) or 0)
        spent = b_spent(m["id"], bid, transactions)
        total += (alloc - spent) - released

    return total


# ── 3.9 Rollover Balance Net ──────────────────────────────────────────────────

def rollover_bal(
    bucket: dict,
    month: dict,
    all_months: list[dict],
    transactions: list[dict],
) -> float:
    raw = rollover_bal_raw(bucket, month["id"], all_months, transactions)
    released = float((month.get("rolloverReleased") or {}).get(bucket["id"]) or 0)
    return raw - released


# ── 3.10 Bucket Available ─────────────────────────────────────────────────────

def bucket_available(
    bucket: dict,
    month: dict,
    all_months: list[dict],
    transactions: list[dict],
) -> float:
    alloc = b_alloc(month, bucket["id"])
    roll = rollover_bal(bucket, month, all_months, transactions)
    spent = b_spent(month["id"], bucket["id"], transactions)
    return (alloc + roll) - spent


# ── 3.12 Vault Accumulated ────────────────────────────────────────────────────

def vault_accumulated(bucket_id: str, all_months: list[dict]) -> float:
    total = 0.0
    for m in all_months:
        alloc = float((m.get("allocations") or {}).get(bucket_id) or 0)
        withdrawn = float((m.get("vaultWithdrawals") or {}).get(bucket_id) or 0)
        total += alloc - withdrawn
    return total


# ── 3.14 Month Income ─────────────────────────────────────────────────────────

def month_income(month_id: str, transactions: list[dict], accounts: list[dict]) -> float:
    budget_ids = {a["id"] for a in accounts if a["type"] == "budget"}
    return sum(
        float(t.get("amount") or 0)
        for t in transactions
        if t.get("monthId") == month_id
        and t.get("type") == "in"
        and t.get("accountId") in budget_ids
        and not is_scheduled(t)
    )


# ── 9. Ready to Spend ─────────────────────────────────────────────────────────

def ready_to_spend(
    active_month: dict,
    all_months: list[dict],
    accounts: list[dict],
    buckets: list[dict],
    transactions: list[dict],
) -> float:
    mid = active_month["id"]
    status = month_status(mid)

    bb = budget_bal(accounts, transactions)
    active_buckets = [b for b in buckets if not b.get("archived")]

    def _claimed(b: dict) -> float:
        if b.get("type") == "vault":
            return vault_accumulated(b["id"], all_months)
        return max(0.0, bucket_available(b, active_month, all_months, transactions))

    if status == "past":
        return bb - sum(_claimed(b) for b in active_buckets)

    # Current or future month — full formula
    cur_claimed = sum(_claimed(b) for b in active_buckets)

    future_months = months_after(mid, all_months)

    future_claimed = sum(
        b_alloc(fm, b["id"])
        for fm in future_months
        for b in active_buckets
    )

    future_released = sum(
        sum(float(v) for v in (fm.get("rolloverReleased") or {}).values())
        for fm in future_months
    )

    return bb - cur_claimed - future_claimed + future_released
