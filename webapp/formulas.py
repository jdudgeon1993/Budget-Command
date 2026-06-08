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


def month_offset(mid: str, n: int) -> str:
    """Return the month n months after (or before, if n<0) mid."""
    y, m0 = parse_month_id(mid)
    m0 += n
    while m0 > 11:
        m0 -= 12
        y += 1
    while m0 < 0:
        m0 += 12
        y -= 1
    return month_id(y, m0)


# ── Transaction helpers ───────────────────────────────────────────────────────

def is_scheduled(tx: dict) -> bool:
    """A transaction is scheduled (future-dated) if its date is after today."""
    d = _safe_date(tx.get("date"))
    return d is not None and d > date.today()


# ── Urgency helpers (Distribute ranking) ─────────────────────────────────────

_FREQ_LABELS = {
    "weekly": "Weekly", "biweekly": "Biweekly",
    "triweekly": "Triweekly", "monthly": "Monthly",
}

DEFAULT_URGENCY_HORIZON_DAYS = 21


def days_until_due(bucket: dict, today: "date | None" = None) -> int | None:
    """Days from today until this bucket's next due date, or None if it has none.

    Only `dueDay` (a fixed day-of-month) gives an actual date to count down to.
    Buckets with just a `payFreq` recur on no particular date — they get no
    due-date countdown; the urgency scorer falls back to a default horizon.
    """
    today = today or date.today()
    due_day = bucket.get("dueDay")
    if due_day is None:
        return None
    try:
        due_day = int(due_day)
    except (ValueError, TypeError):
        return None
    if not (1 <= due_day <= 31):
        return None

    import calendar
    y, m = today.year, today.month
    last_day = calendar.monthrange(y, m)[1]
    candidate = date(y, m, min(due_day, last_day))
    if candidate < today:
        m += 1
        if m > 12:
            m = 1
            y += 1
        last_day = calendar.monthrange(y, m)[1]
        candidate = date(y, m, min(due_day, last_day))
    return (candidate - today).days


def freq_label(pay_freq: str | None) -> str:
    return _FREQ_LABELS.get(pay_freq or "", "")


def urgency_score(gap: float, horizon_days: int | None) -> float:
    """Higher = more urgent. Funding gap weighted by how soon it's needed.

    Recurring spends with no fixed due date use a default horizon — they're
    not "due" on any particular day, but they do recur reliably and need a
    home eventually.
    """
    horizon = horizon_days if horizon_days and horizon_days > 0 else DEFAULT_URGENCY_HORIZON_DAYS
    return gap / horizon


def distribute_obligations(buckets: list[dict], month: dict) -> list[dict]:
    """Underfunded buckets ranked by urgency (funding gap weighted by due date).

    Each entry carries enough to both rank it and explain the ranking:
    the dollar gap between budget and current allocation, days until its
    next due date (None for buckets with no fixed due day), and its pay
    frequency label for display.
    """
    obligations = []
    for b in buckets:
        budget = b_budget(month, b["id"])
        alloc = b_alloc(month, b["id"])
        gap = round(budget - alloc, 2)
        if gap <= 0.005:
            continue
        due_in = days_until_due(b)
        obligations.append({
            "id": b["id"], "name": b["name"], "gap": gap,
            "due_in": due_in, "freq": freq_label(b.get("payFreq")),
            "score": urgency_score(gap, due_in),
        })
    obligations.sort(key=lambda o: o["score"], reverse=True)
    return obligations


# ── 3.1 Account Balance ───────────────────────────────────────────────────────

def acct_balance_as_of(account: dict, transactions: list[dict], as_of: "date") -> float:
    """Balance including only transactions on or before as_of date."""
    filtered = [t for t in transactions
                if (_safe_date(t.get("date")) or date.max) <= as_of]
    return acct_balance(account, filtered)


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


# ── 3.3 Total Cash (budget + savings) ────────────────────────────────────────

def total_cash(accounts: list[dict], transactions: list[dict]) -> float:
    return sum(
        acct_balance(a, transactions)
        for a in accounts
        if a.get("type") in ("budget", "savings")
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


# ── 3.10 Bucket Available ─────────────────────────────────────────────────────

def bucket_available(
    bucket: dict,
    month: dict,
    all_months: list[dict],
    transactions: list[dict],
) -> float:
    """Net spendable balance for this bucket.

    Vaults and savings goals accumulate contributions across all months —
    that's their purpose. Expense buckets are current-month only: unspent
    allocation returns to Ready to Assign rather than silently claiming
    the cash in future months. A bucket with explicit rollover=True also
    accumulates (for users who want envelope carry-over on a specific
    expense category). Overspending on non-accumulating buckets still
    shows as a negative balance within the month, feeding correctly into
    the RTS calculation via the cash-conservation identity.
    """
    bid = bucket["id"]
    btype = bucket.get("type", "expense")
    accumulates = btype in ("vault", "sinking", "goal") or bucket.get("rollover")
    if not accumulates:
        return b_alloc(month, bid) - b_spent(month["id"], bid, transactions)
    carried = sum(
        b_alloc(m, bid) - b_spent(m["id"], bid, transactions)
        for m in months_before(month["id"], all_months)
    )
    return carried + b_alloc(month, bid) - b_spent(month["id"], bid, transactions)


# ── 3.12 Vault Accumulated ────────────────────────────────────────────────────

def vault_accumulated(bucket_id: str, all_months: list[dict]) -> float:
    total = 0.0
    for m in all_months:
        alloc = float((m.get("allocations") or {}).get(bucket_id) or 0)
        withdrawn = float((m.get("vaultWithdrawals") or {}).get(bucket_id) or 0)
        total += alloc - withdrawn
    return total


# ── Age of Money ─────────────────────────────────────────────────────────────

def age_of_money(accounts: list[dict], transactions: list[dict], window_days: int = 30) -> int | None:
    """Days between earning money and spending it.

    Uses total cash (budget + savings) divided by the rolling daily spend rate.
    Returns None if there's no spending data. Caps at 99.
    """
    from datetime import timedelta
    today = date.today()
    cutoff = today - timedelta(days=window_days)
    budget_ids = {a["id"] for a in accounts if a.get("type") in ("budget", "savings") and not a.get("archived")}
    spending = sum(
        float(t.get("amount") or 0)
        for t in transactions
        if t.get("type") == "out"
        and t.get("accountId") in budget_ids
        and not is_scheduled(t)
        and cutoff <= (_safe_date(t.get("date")) or date.min) <= today
    )
    if spending <= 0:
        return None
    cash = total_cash(accounts, transactions)
    if cash <= 0:
        return 0
    daily = spending / window_days
    return min(99, round(cash / daily))


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
        # Negative balances (overspent envelopes) must count as negative, not
        # zero — cash conservation requires bb == rts + sum(bucket balances).
        # Clamping to zero double-penalizes overspending: once via the cash
        # already being gone, again by refusing to let the deficit offset it.
        return bucket_available(b, active_month, all_months, transactions)

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

    return bb - cur_claimed - future_claimed
