"""
Forecast calculation — pure Python, no Reflex dependencies.
Ported from app/app.py forecast endpoint.
"""

import calendar as _cal
from datetime import date, timedelta
from .formulas import (acct_balance as _acct_balance, is_scheduled as _is_scheduled,
                       b_alloc, b_spent, bucket_available)


# ── Timeline helpers ──────────────────────────────────────────────────────────

def ym_key(year: int, month: int) -> str:
    """Canonical month key used by wi_timeline: '2026-9'."""
    return f"{year}-{month}"


def ym_int(key) -> float:
    """Convert 'YYYY-M' key (or None) to a sortable integer for comparison."""
    if not key:
        return float("-inf")
    try:
        parts = str(key).split("-")
        return int(parts[0]) * 12 + int(parts[1])
    except (IndexError, ValueError):
        return float("-inf")


def get_timeline_rule(timeline: dict, bid: str, year: int, month: int):
    """Return the applicable timeline rule for bucket *bid* in (year, month), or None."""
    rules = timeline.get(bid, [])
    if not rules:
        return None
    cur = year * 12 + month
    applicable = None
    for r in sorted(rules, key=lambda r: ym_int(r.get("from"))):
        if ym_int(r.get("from")) <= cur:
            applicable = r
        else:
            break
    return applicable


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mid(d: date) -> str:
    return f"m_{d.year}_{d.month - 1}"


def _fmt(v: float) -> str:
    if v < 0:
        return f"-${abs(v):,.2f}"
    return f"${v:,.2f}"


def _date_label(d: date) -> str:
    today = date.today()
    if d == today:
        return "Today"
    if d == today + timedelta(days=1):
        return "Tomorrow"
    return d.strftime("%a, %b %-d")


def _natural_monthly_income(paychecks: list, ref_date: date) -> float:
    """Sum of paycheck amounts that land in ref_date's calendar month."""
    y, m = ref_date.year, ref_date.month
    m_start = date(y, m, 1)
    m_end   = date(y, m, _cal.monthrange(y, m)[1])
    total = 0.0
    for pc in paychecks:
        anchor = pc.get("anchor_date") or pc.get("anchorDate")
        if not anchor:
            continue
        for _ in _gen_pay_dates(anchor, int(pc.get("freq", 14)), m_start, m_end):
            total += float(pc.get("amount") or 0)
    return total


def _income_scale(income_override: float, nat_monthly: float) -> float:
    """Scale factor to apply to each paycheck amount when override is set."""
    if income_override > 0 and nat_monthly > 0:
        return income_override / nat_monthly
    return 1.0


def _range_label(s: date, e: date) -> str:
    if s.year == e.year:
        return f"{s.strftime('%b %-d')} – {e.strftime('%b %-d')}"
    return f"{s.strftime('%b %-d, %Y')} – {e.strftime('%b %-d, %Y')}"


# ── Math expression evaluator for What-If overrides ──────────────────────────

def _apply_expr(base: float, expr: str) -> float:
    """Apply a math expression to a base value. Supports: +N, -N, *N, /N, =N, or N."""
    if not expr or not str(expr).strip():
        return base
    s = str(expr).strip().replace(",", "").replace("$", "")
    try:
        if s.startswith("+"):
            return max(0.0, base + float(s[1:]))
        elif s.startswith("-") and len(s) > 1 and s[1:].replace(".", "").isdigit():
            return max(0.0, base - float(s[1:]))
        elif s.startswith("*"):
            return max(0.0, base * float(s[1:]))
        elif s.startswith("/"):
            divisor = float(s[1:])
            return max(0.0, base / divisor) if divisor != 0 else base
        elif s.startswith("="):
            return max(0.0, float(s[1:]))
        else:
            return max(0.0, float(s))
    except (ValueError, TypeError):
        return base


# ── Date generators ───────────────────────────────────────────────────────────

def _gen_pay_dates(anchor_str: str, freq: int, from_date: date, to_date: date) -> list[date]:
    if not anchor_str:
        return []
    anchor = date.fromisoformat(anchor_str)
    dates: list[date] = []

    if freq == 15:  # semi-monthly: 1st and 15th
        y, m = from_date.year, from_date.month
        while date(y, m, 1) <= to_date:
            for day in (1, 15):
                d = date(y, m, day)
                if from_date <= d <= to_date:
                    dates.append(d)
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)

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
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)

    else:  # 7 (weekly) or 14 (biweekly)
        delta = (from_date - anchor).days
        if delta > 0:
            steps = (delta + freq - 1) // freq
            d = anchor + timedelta(days=steps * freq)
        else:
            d = anchor
            while d >= from_date:
                d -= timedelta(days=freq)
            d += timedelta(days=freq)
        while d <= to_date:
            dates.append(d)
            d += timedelta(days=freq)

    return sorted(dates)


def _bill_dates(due_day, pay_freq, from_date: date, to_date: date) -> list[date]:
    if due_day is None:
        return []
    raw = str(due_day).strip().lower()
    dates: list[date] = []

    if pay_freq in ("weekly", "biweekly", "triweekly"):
        freq_days = {"weekly": 7, "biweekly": 14, "triweekly": 21}[pay_freq]
        try:
            anchor_day = int(raw)
        except ValueError:
            anchor_day = 1
        d = date(from_date.year, from_date.month,
                 min(anchor_day, _cal.monthrange(from_date.year, from_date.month)[1]))
        while d < from_date:
            d += timedelta(days=freq_days)
        while d <= to_date:
            dates.append(d)
            d += timedelta(days=freq_days)
        return dates

    y, m = from_date.year, from_date.month
    while True:
        last = _cal.monthrange(y, m)[1]
        day = last if raw == "eom" else int(raw) if raw.isdigit() else None
        if day is None:
            break
        d = date(y, m, min(day, last))
        if d > to_date:
            break
        if d >= from_date:
            dates.append(d)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return sorted(dates)


def _sts_class(val: float) -> str:
    """Semantic CSS class for a balance/STS value — resolves to theme color vars."""
    if val > 0:  return "c-green"
    if val == 0: return "c-amber"
    return "c-red"


def _freq_only_dates(pay_freq: str, from_date: date, to_date: date) -> list[date]:
    if pay_freq == "monthly":
        dates, y, m = [], from_date.year, from_date.month
        while True:
            d = from_date if (y == from_date.year and m == from_date.month) else date(y, m, 1)
            if d > to_date:
                break
            dates.append(d)
            y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        return dates
    freq_days = {"weekly": 7, "biweekly": 14, "triweekly": 21}.get(pay_freq)
    if not freq_days:
        return []
    dates, d = [], from_date
    while d <= to_date:
        dates.append(d)
        d += timedelta(days=freq_days)
    return dates


# ── Main forecast calculation ─────────────────────────────────────────────────

def compute_forecast(data: dict, n_months: int = 3, account_id: str = "",
                     income_override: float = 0.0,
                     bucket_overrides: dict = None,
                     rule_overrides: dict = None,
                     off_buckets: list = None,
                     schedule: dict = None,
                     due_day_overrides: dict = None,
                     timeline: dict = None,
                     skipped_pay_dates: list = None,
                     no_accrue_dates: list = None,
                     phantom_monthly: list = None,
                     paycheck_overrides: dict = None) -> dict:
    """
    Returns {
        start_balance, safe_to_spend, total_income, total_unfunded,
        shortfall_count, periods: [period_dict, ...]
    }

    bucket_overrides: {bid: float_or_expr_str} — override bill amount per bucket
    rule_overrides:   {rule_id: float} — override rule values
    off_buckets:      [bid, ...] — buckets to exclude from forecast
    """
    today = date.today()
    bucket_overrides  = bucket_overrides or {}
    rule_overrides    = rule_overrides or {}
    paycheck_overrides = paycheck_overrides or {}
    off_set           = set(off_buckets or [])
    schedule          = schedule or {}
    due_day_overrides = due_day_overrides or {}
    skipped_set       = set(str(d) for d in (skipped_pay_dates or []))
    no_accrue_set     = set(str(d) for d in (no_accrue_dates or []))

    accounts   = data.get("accounts", [])
    buckets    = data.get("buckets", [])
    txs        = data.get("txs", [])
    months_raw = data.get("months", [])
    paychecks  = data.get("paychecks", [])
    rules_raw  = data.get("allocationRules", [])

    # ── Starting balance — use canonical formula (skips scheduled/future txs) ──
    budget_accounts = [a for a in accounts if a.get("type") == "budget" and not a.get("archived")]
    if account_id:
        start_accounts = [a for a in budget_accounts if a["id"] == account_id]
    else:
        start_accounts = budget_accounts
    start_balance = sum(_acct_balance(a, txs) for a in start_accounts)

    # ── End date ──────────────────────────────────────────────────────────────
    y = today.year + (today.month - 1 + n_months) // 12
    m = (today.month - 1 + n_months) % 12 + 1
    end_date = date(y, m, _cal.monthrange(y, m)[1])

    # ── Pay events ────────────────────────────────────────────────────────────
    external_rules = [r for r in rules_raw if r.get("rule_type") == "external" and r.get("active", True)]
    internal_rules = [r for r in rules_raw if r.get("rule_type") != "external" and r.get("active", True) and (r.get("bucket_id") or r.get("bucketId"))]
    bname = {b["id"]: b["name"] for b in buckets}
    btype = {b["id"]: b.get("type", "expense") for b in buckets}

    pay_events: dict[date, list] = {}
    for pc in paychecks:
        anchor = pc.get("anchor_date") or pc.get("anchorDate")
        if not anchor:
            continue
        for pd in _gen_pay_dates(anchor, int(pc.get("freq", 14)), today, end_date):
            if pd not in pay_events:
                pay_events[pd] = []
            pc_id = str(pc.get("id", ""))
            amt = float(paycheck_overrides.get(pc_id, pc.get("amount") or 0))
            transfers = []
            for r in external_rules:
                rid = r.get("id", "")
                v   = float(rule_overrides.get(rid, r.get("value") or 0))
                computed = round(amt * v / 100, 2) if r.get("type") == "pct" or r.get("value_type") == "pct" else v
                transfers.append({"name": r.get("name", "Transfer"), "amount": computed})
            allocs = []
            for r in internal_rules:
                rid = r.get("id", "")
                v   = float(rule_overrides.get(rid, r.get("value") or 0))
                computed = round(amt * v / 100, 2) if r.get("type") == "pct" or r.get("value_type") == "pct" else v
                bid = r.get("bucket_id") or r.get("bucketId", "")
                allocs.append({"name": bname.get(bid, ""), "amount": computed,
                               "is_vault": btype.get(bid, "expense") == "vault"})
            pay_events[pd].append({"label": pc.get("label", "Paycheck"),
                                   "amount": round(amt, 2),
                                   "transfers": transfers, "allocs": allocs})

    all_pay_dates = sorted(pay_events.keys())

    # ── Income override — scale all paycheck amounts ──────────────────────────
    if income_override > 0:
        nat_monthly = _natural_monthly_income(paychecks, today)
        scale = _income_scale(income_override, nat_monthly)
        if scale != 1.0:
            for pcs in pay_events.values():
                for pc_hit in pcs:
                    pc_hit["amount"]   = round(pc_hit["amount"] * scale, 2)
                    for xfr in pc_hit["transfers"]:
                        xfr["amount"] = round(xfr["amount"] * scale, 2)
                    for ae in pc_hit["allocs"]:
                        ae["amount"]  = round(ae["amount"] * scale, 2)

    # ── Period boundaries ─────────────────────────────────────────────────────
    periods_meta: list[tuple[date, date, bool]] = []
    if not all_pay_dates:
        periods_meta.append((today, end_date, True))
    else:
        if all_pay_dates[0] > today:
            periods_meta.append((today, all_pay_dates[0] - timedelta(days=1), True))
        for i, pd in enumerate(all_pay_dates):
            pe = all_pay_dates[i + 1] - timedelta(days=1) if i + 1 < len(all_pay_dates) else end_date
            periods_meta.append((pd, pe, False))

    # ── Monthly allocation data ───────────────────────────────────────────────
    monthly_allocs   = {m.get("id", ""): m.get("allocations", {}) for m in months_raw}
    monthly_budgets  = {m.get("id", ""): m.get("budgets", {}) for m in months_raw}
    monthly_handled  = {m.get("id", ""): m.get("handledBuckets", {}) for m in months_raw}
    today_mid = _mid(today)

    def _effective_bill_amt(b: dict, for_year: int = 0, for_month: int = 0) -> float:
        bid = b["id"]
        base = float(b.get("dueAmount") or b.get("defaultBudget") or 0)
        if timeline and for_year and for_month:
            rule = get_timeline_rule(timeline, bid, for_year, for_month)
            if rule is not None:
                if not rule.get("enabled", True):
                    return 0.0
                if rule.get("amount") is not None:
                    return float(rule["amount"])
        if bid in bucket_overrides:
            return _apply_expr(base, str(bucket_overrides[bid]))
        return base

    def _funded(bid: str, bill_date: date) -> bool:
        mid_    = _mid(bill_date)
        alloc   = float(monthly_allocs.get(mid_, {}).get(bid, 0))
        budget  = float(monthly_budgets.get(mid_, {}).get(bid, 0))
        bill_a  = _effective_bill_amt(next((b for b in buckets if b["id"] == bid), {}))
        target  = budget if budget > 0 else bill_a
        if target <= 0:
            return alloc > 0
        # Carryforward is always-on — a bucket funded by its rolled-over balance is not unfunded
        if mid_ == today_mid:
            bucket_obj = next((b for b in buckets if b["id"] == bid), None)
            month_obj = next((m for m in months_raw if m.get("id") == mid_), None)
            if bucket_obj and month_obj:
                avail = bucket_available(bucket_obj, month_obj, months_raw, txs)
                return avail >= target * 0.99
        return alloc >= target * 0.99

    # Check if a bill is already PAID (spent) in current month.
    # Consistent with the timeline: spent >= bill_amount (not allocation).
    # Scheduled transactions are excluded — they're intentional but not yet executed.
    paid_bids: set[str] = set()
    bkt_map = {b["id"]: b for b in buckets}
    spent_by_bid: dict[str, float] = {}
    for tx in txs:
        if (tx.get("type") == "out" and tx.get("bucketId")
                and not _is_scheduled(tx)
                and _mid(date.fromisoformat(tx["date"])) == today_mid):
            bid_ = tx["bucketId"]
            spent_by_bid[bid_] = spent_by_bid.get(bid_, 0.0) + float(tx.get("amount") or 0)
    for bid_, spent_ in spent_by_bid.items():
        bkt = bkt_map.get(bid_)
        if not bkt or bkt.get("archived"):
            continue
        bill_amt = float(bkt.get("dueAmount") or bkt.get("defaultBudget") or 0)
        if bill_amt > 0 and spent_ >= bill_amt * 0.99:
            paid_bids.add(bid_)

    active_buckets = [b for b in buckets if not b.get("archived") and b["id"] not in off_set]
    dated_bills = [b for b in active_buckets if b.get("dueDay") is not None
                   and _effective_bill_amt(b) > 0]
    freq_bills  = [b for b in active_buckets if b.get("dueDay") is None
                   and b.get("payFreq") in ("weekly", "biweekly", "triweekly", "monthly")
                   and _effective_bill_amt(b) > 0]
    # Scenario-injected buckets with no due date — treated as monthly on the 1st
    for ph in (phantom_monthly or []):
        if ph["id"] in off_set:
            continue
        amt = float(bucket_overrides.get(ph["id"], ph.get("amount", 0)))
        if amt <= 0:
            continue
        dated_bills.append({
            "id": ph["id"], "name": ph["name"],
            "dueDay": 1, "payFreq": "monthly",
            "dueAmount": amt, "defaultBudget": amt,
        })

    # ── Build periods ─────────────────────────────────────────────────────────
    running_balance = start_balance
    period_results: list[dict] = []
    grand_income   = 0.0
    grand_unfunded = 0.0
    grand_funded   = 0.0

    for ps, pe, is_gap in periods_meta:
        period_start_bal = running_balance

        income_events:   list[dict] = []
        transfer_events: list[dict] = []
        alloc_events:    list[dict] = []

        is_skipped   = (not is_gap) and (str(ps) in skipped_set)
        is_no_accrue = (not is_gap) and (not is_skipped) and (str(ps) in no_accrue_set)

        if not is_gap and ps in pay_events and not is_skipped and not is_no_accrue:
            for pc_hit in pay_events[ps]:
                running_balance += pc_hit["amount"]
                grand_income    += pc_hit["amount"]
                income_events.append({"label": pc_hit["label"], "amount": pc_hit["amount"]})
                for xfr in pc_hit["transfers"]:
                    running_balance -= xfr["amount"]
                    transfer_events.append(xfr)
                for ae in pc_hit["allocs"]:
                    if ae["is_vault"]:
                        running_balance -= ae["amount"]
                        alloc_events.append({"name": ae["name"], "amount": ae["amount"],
                                             "ae_type": "vault"})
                    else:
                        alloc_events.append({"name": ae["name"], "amount": ae["amount"],
                                             "ae_type": "info"})

        bal_after_xfr = running_balance

        # Collect bill events for this period
        funded_by_day:   dict[date, list] = {}
        unfunded_by_day: dict[date, list] = {}

        def _add_bill(b: dict, bd: date) -> None:
            bill_mid = _mid(bd)
            if b["id"] in paid_bids and bill_mid == today_mid:
                return
            if monthly_handled.get(bill_mid, {}).get(b["id"]):
                return
            if schedule.get(f"{b['id']}_{bill_mid}", "on") == "off":
                return
            if timeline:
                rule = get_timeline_rule(timeline, b["id"], bd.year, bd.month)
                if rule is not None and not rule.get("enabled", True):
                    return
            amt = _effective_bill_amt(b, bd.year, bd.month)
            if amt <= 0:
                return
            actual = round(spent_by_bid.get(b["id"], 0.0), 2) if is_gap or ps == today else 0.0
            entry = {"name": b["name"], "amount": amt, "actual": actual}
            if _funded(b["id"], bd):
                funded_by_day.setdefault(bd, []).append(entry)
            else:
                unfunded_by_day.setdefault(bd, []).append(entry)

        overdue_start = date(today.year, today.month, 1) if is_gap else ps
        for b in dated_bills:
            eff_due = due_day_overrides.get(b["id"]) or b.get("dueDay")
            for bd in _bill_dates(eff_due, b.get("payFreq"), overdue_start, pe):
                _add_bill(b, bd)
        for b in freq_bills:
            for bd in _freq_only_dates(b["payFreq"], ps, pe):
                _add_bill(b, bd)

        # Process funded (green) — deduct from balance
        funded_lines: list[dict] = []
        is_current_period = is_gap or (ps <= today <= pe)
        for d in sorted(funded_by_day):
            funded_lines.append({"row_type": "date", "text": _date_label(d)})
            for bill in funded_by_day[d]:
                running_balance -= bill["amount"]
                actual = bill.get("actual", 0.0) if is_current_period else 0.0
                funded_lines.append({"row_type": "bill", "text": bill["name"],
                                     "amount_fmt": _fmt(bill["amount"]),
                                     "actual_fmt": _fmt(actual) if actual else "",
                                     "variance_fmt": _fmt(actual - bill["amount"]) if actual else "",
                                     "variance_over": actual > bill["amount"] + 0.005 if actual else False})
                grand_funded += bill["amount"]

        bal_after_funded = running_balance  # snapshot before unfunded bills

        # Process unfunded (red) — deduct from balance
        unfunded_lines: list[dict] = []
        for d in sorted(unfunded_by_day):
            unfunded_lines.append({"row_type": "date", "text": _date_label(d)})
            for bill in unfunded_by_day[d]:
                running_balance -= bill["amount"]
                grand_unfunded  += bill["amount"]
                actual = bill.get("actual", 0.0) if is_current_period else 0.0
                unfunded_lines.append({"row_type": "bill", "text": bill["name"],
                                       "amount_fmt": _fmt(bill["amount"]),
                                       "actual_fmt": _fmt(actual) if actual else "",
                                       "variance_fmt": _fmt(actual - bill["amount"]) if actual else "",
                                       "variance_over": actual > bill["amount"] + 0.005 if actual else False})

        # Build transfer lines with cumulative totals
        xfr_cum = 0.0
        transfer_lines_with_cum = []
        for xfr in transfer_events:
            xfr_cum += xfr["amount"]
            transfer_lines_with_cum.append({
                "label": xfr["name"],
                "amount_fmt": _fmt(xfr["amount"]),
                "cum_fmt": _fmt(xfr_cum),
            })

        total_funded   = sum(b["amount"] for d in funded_by_day.values() for b in d)
        total_bills    = total_funded + sum(b["amount"] for d in unfunded_by_day.values() for b in d)
        funded_count   = sum(len(v) for v in funded_by_day.values())
        unfunded_count = sum(len(v) for v in unfunded_by_day.values())
        total_count    = funded_count + unfunded_count

        period_income    = sum(e["amount"] for e in income_events)
        period_unfunded  = sum(b["amount"] for d in unfunded_by_day.values() for b in d)
        period_net       = running_balance - period_start_bal

        total_vault_alloc = sum(ae["amount"] for ae in alloc_events if ae["ae_type"] == "vault")
        total_ext_xfr     = sum(xfr["amount"] for xfr in transfer_events)

        def _bal_color(b: float) -> str:
            if b < 100:  return "var(--red)"
            if b < 500:  return "var(--amber)"
            return "var(--green)"

        if is_gap:
            label = "Pre-Paycheck Gap"
        elif is_skipped:
            pay_labels = list({pc_hit["label"] for pc_hit in pay_events.get(ps, [])}) or ["Paycheck"]
            label = " + ".join(sorted(pay_labels)) + " (Skipped)"
        else:
            labels = list({e["label"] for e in income_events}) or ["Paycheck"]
            label  = " + ".join(sorted(labels))

        income_lines = [{"label": e["label"], "amount_fmt": _fmt(e["amount"])} for e in income_events]

        period_results.append({
            "id":                  str(ps),
            "type":                "gap" if is_gap else "paycheck",
            "is_skipped":          is_skipped,
            "is_no_accrue":        is_no_accrue,
            "label":               label,
            "date_range":          _range_label(ps, pe),
            "income_lines":        income_lines,
            "transfer_lines":      transfer_lines_with_cum,
            "alloc_events":        alloc_events,
            "funded_lines":        funded_lines,
            "unfunded_lines":      unfunded_lines,
            "has_income":          bool(income_events),
            "has_transfers":       bool(transfer_events),
            "has_alloc_events":    bool(alloc_events),
            "has_funded":          bool(funded_by_day),
            "has_unfunded":        bool(unfunded_by_day),
            "start_bal_fmt":          _fmt(period_start_bal),
            "bal_after_xfr_fmt":      _fmt(bal_after_xfr),
            "bal_after_xfr_color":    _bal_color(bal_after_xfr),
            "income_total_fmt":       _fmt(period_income),
            "unfunded_total_fmt":     _fmt(period_unfunded),
            "funded_total_fmt":       _fmt(total_funded),
            "net_fmt":                _fmt(abs(period_net)),
            "net_sign":               "+" if period_net >= 0 else "-",
            "net_negative":           period_net < 0,
            "end_bal_fmt":            _fmt(running_balance),
            "end_bal_raw":            running_balance,
            "end_bal_negative":       running_balance < 0,
            "end_bal_color":          _bal_color(running_balance),
            "shortfall":              running_balance < 0,
            "funded_count":           funded_count,
            "total_count":            total_count,
            "vault_alloc_total_fmt":  _fmt(total_vault_alloc),
            "has_vault_alloc":        total_vault_alloc > 0,
            "ext_xfr_total_fmt":      _fmt(total_ext_xfr),
            "bal_after_funded_fmt":   _fmt(bal_after_funded),
            "bal_after_funded_color": _bal_color(bal_after_funded),
            "safe_to_spend_fmt":      "",  # filled below
            "sts_color":              "",
        })

    # ── Safe to spend (forward minimum) ──────────────────────────────────────
    running_min = float("inf")
    fwd_mins    = [0.0] * len(period_results)
    for i in range(len(period_results) - 1, -1, -1):
        running_min = min(running_min, period_results[i]["end_bal_raw"])
        fwd_mins[i] = running_min

    safe_to_spend = fwd_mins[0] if fwd_mins else start_balance

    # ── Per-period cushion + safe-to-save ─────────────────────────────────────
    # cushion[i] = how much of end_bal[i] is above the forward minimum (truly surplus)
    # If period i IS the forward minimum, fwd_mins[i] == end_bal[i], cushion = 0.
    for i, p in enumerate(period_results):
        sts = fwd_mins[i]
        p["safe_to_spend_fmt"] = _fmt(sts)
        p["sts_color"]         = _sts_class(sts)
        cushion = max(0.0, p["end_bal_raw"] - fwd_mins[i])
        safe_save = round(cushion * 0.5, 2)
        p["cushion_raw"]      = cushion
        p["cushion_fmt"]      = _fmt(cushion)
        p["safe_to_save_fmt"] = _fmt(safe_save)

    shortfall_count = sum(1 for p in period_results if p["shortfall"])

    # ── Danger date — period with the lowest projected balance ────────────────
    danger_date = danger_balance_fmt = ""
    if period_results:
        danger_idx = min(range(len(period_results)),
                         key=lambda i: period_results[i]["end_bal_raw"])
        danger_bal = period_results[danger_idx]["end_bal_raw"]
        if danger_bal < start_balance:
            danger_date         = period_results[danger_idx]["date_range"]
            danger_balance_fmt  = _fmt(danger_bal)

    # ── Break-even — first future period where balance recovers to start ──────
    break_even_label = None
    for p in period_results:
        if p["end_bal_raw"] >= start_balance - 0.005 and not p.get("is_gap"):
            break_even_label = p["date_range"]
            break

    # ── Months of runway = start_balance / avg monthly spend ─────────────────
    avg_monthly_spend = (grand_funded + grand_unfunded) / n_months if n_months else 0
    if avg_monthly_spend > 0:
        runway_raw = start_balance / avg_monthly_spend
        runway_months = round(runway_raw, 1)
        runway_color = ("var(--red)" if runway_raw < 1
                        else "var(--amber)" if runway_raw < 3
                        else "var(--green)")
    else:
        runway_months = None
        runway_color  = "var(--text3)"

    return {
        "start_balance":      _fmt(start_balance),
        "safe_to_spend":      _fmt(safe_to_spend),
        "sts_color":          _sts_class(safe_to_spend),
        "total_income":       _fmt(grand_income),
        "total_unfunded":     _fmt(grand_unfunded),
        "shortfall_count":    shortfall_count,
        "periods":            period_results,
        "danger_date":        danger_date,
        "danger_balance_fmt": danger_balance_fmt,
        "break_even_label":   break_even_label,
        "runway_months":      runway_months,
        "runway_color":       runway_color,
    }


# ── Simple 60-day timeline (event feed) ──────────────────────────────────────

def compute_simple_timeline(data: dict, n_days: int = 60,
                            off_buckets: list = None) -> list[dict]:
    """
    Generate a flat 60-day event feed from today.
    Returns list of flat row dicts:
      {rt: "day",      lbl: "Today"/"Tomorrow"/"Mon Jun 2", td: "1"/"", pa: ""}
      {rt: "paycheck", lbl: "Paycheck Name",  amt: "$X.XX",  td: "", pa: ""}
      {rt: "bill",     lbl: "Bill Name",       amt: "$X.XX",  td: "", pa: "1"/"", pd: "1"/""}
    All values are strings.
    off_buckets: list of bucket IDs excluded by the active scenario.
    """
    today = date.today()
    end   = today + timedelta(days=n_days - 1)
    off_set = set(off_buckets or [])

    paychecks   = data.get("paychecks", [])
    buckets     = [b for b in data.get("buckets", []) if b.get("id") not in off_set]
    txs         = data.get("txs", [])
    months_raw  = data.get("months", [])
    handled_by_mid = {m.get("id", ""): m.get("handledBuckets", {}) for m in months_raw}

    # Paycheck events by date
    pc_by_date: dict[date, list] = {}
    for pc in paychecks:
        anchor = pc.get("anchor_date") or pc.get("anchorDate")
        if not anchor:
            continue
        for pd in _gen_pay_dates(anchor, int(pc.get("freq", 14)), today, end):
            pc_by_date.setdefault(pd, []).append({
                "label":      pc.get("label", "Paycheck"),
                "amount_fmt": _fmt(float(pc.get("amount") or 0)),
            })

    def _bill_amt(b: dict) -> float:
        return float(b.get("dueAmount") or b.get("defaultBudget") or 0)

    def _is_paid(b: dict, bd: date, occurrence: int = 1) -> bool:
        """
        True when confirmed (non-scheduled) spending for this bucket+month
        covers `occurrence` × the per-event amount.  Prevents a single
        transaction from marking every recurrence in the month as done.
        """
        mid = _mid(bd)
        amt = _bill_amt(b)
        if not amt:
            return False
        spent = sum(
            float(t.get("amount") or 0) for t in txs
            if t.get("bucketId") == b["id"] and t.get("type") == "out"
            and t.get("monthId") == mid
            and not _is_scheduled(t)
        )
        return spent >= amt * occurrence * 0.99

    def _has_scheduled_tx(b: dict, bd: date) -> bool:
        """True if there is a future-dated (scheduled, not yet executed) tx for this month."""
        mid = _mid(bd)
        return any(
            t for t in txs
            if t.get("bucketId") == b["id"] and t.get("type") == "out"
            and t.get("monthId") == mid
            and _is_scheduled(t)
        )

    dated_bills = [b for b in buckets if not b.get("archived") and b.get("dueDay") is not None
                   and _bill_amt(b) > 0]
    freq_bills  = [b for b in buckets if not b.get("archived") and b.get("dueDay") is None
                   and b.get("payFreq") in ("weekly", "biweekly", "triweekly", "monthly")
                   and _bill_amt(b) > 0]

    # occurrence_count tracks how many times each (bucket, month) pair has appeared
    # so the nth occurrence checks: total_spent >= n × per_event_amount
    occ_count: dict[tuple, int] = {}

    bill_by_date: dict[date, list] = {}
    for b in dated_bills:
        for bd in _bill_dates(b.get("dueDay"), b.get("payFreq"), today, end):
            if handled_by_mid.get(_mid(bd), {}).get(b["id"]):
                continue
            key = (b["id"], _mid(bd))
            occ_count[key] = occ_count.get(key, 0) + 1
            occ = occ_count[key]
            bill_by_date.setdefault(bd, []).append({
                "name":       b["name"],
                "amount_fmt": _fmt(_bill_amt(b)),
                "paid":       _is_paid(b, bd, occ),
                "scheduled":  not _is_paid(b, bd, occ) and _has_scheduled_tx(b, bd),
            })
    for b in freq_bills:
        for bd in _freq_only_dates(b["payFreq"], today, end):
            if handled_by_mid.get(_mid(bd), {}).get(b["id"]):
                continue
            key = (b["id"], _mid(bd))
            occ_count[key] = occ_count.get(key, 0) + 1
            occ = occ_count[key]
            bill_by_date.setdefault(bd, []).append({
                "name":       b["name"],
                "amount_fmt": _fmt(_bill_amt(b)),
                "paid":       _is_paid(b, bd, occ),
                "scheduled":  not _is_paid(b, bd, occ) and _has_scheduled_tx(b, bd),
            })

    all_dates = sorted(set(pc_by_date.keys()) | set(bill_by_date.keys()) | {today})

    _blank = {"rt": "", "lbl": "", "amt": "", "td": "", "pa": "", "pd": "", "sch": ""}

    def _row(**kw) -> dict:
        r = dict(_blank)
        r.update({k: str(v) for k, v in kw.items()})
        return r

    rows: list[dict] = []
    for d in all_dates:
        delta = (d - today).days
        if delta == 0:
            day_lbl = "Today"
        elif delta == 1:
            day_lbl = "Tomorrow"
        else:
            day_lbl = d.strftime("%a, %b %-d")

        rows.append(_row(rt="day", lbl=day_lbl,
                         td="1" if d == today else "",
                         pa="1" if d < today else ""))

        for pc in pc_by_date.get(d, []):
            rows.append(_row(rt="paycheck", lbl=pc["label"], amt=pc["amount_fmt"]))

        # Order: unpaid/unscheduled first, then scheduled, then paid
        bills = sorted(bill_by_date.get(d, []),
                       key=lambda b: (b["paid"], b["scheduled"], b["name"]))
        for bl in bills:
            rows.append(_row(rt="bill", lbl=bl["name"], amt=bl["amount_fmt"],
                             pa="1" if d < today else "",
                             pd="1" if bl["paid"] else "",
                             sch="1" if bl["scheduled"] and d >= today else ""))

    return rows


# ── Balance trajectory SVG ────────────────────────────────────────────────────

def build_balance_svg(periods: list, width: int = 840, height: int = 120) -> str:
    """Build a balance-over-time SVG from forecast period dicts."""
    if not periods:
        return ""

    def _parse(s: str) -> float:
        s = (s or "").strip().replace(",", "")
        if s.startswith("-$") or (s.startswith("-") and len(s) > 1):
            return -float(s.lstrip("-$").lstrip("-") or "0")
        return float(s.lstrip("$") or "0")

    # Use start_bal of first period + end_bal of every period
    pts: list[float] = []
    try:
        pts.append(_parse(periods[0].get("start_bal_fmt", "0")))
    except Exception:
        pts.append(0.0)
    for p in periods:
        try:
            pts.append(_parse(p.get("end_bal_fmt", "0")))
        except Exception:
            pts.append(0.0)

    pad_l, pad_r, pad_t, pad_b = 32, 16, 12, 24
    cw = width - pad_l - pad_r
    ch = height - pad_t - pad_b

    min_v = min(pts + [0])
    max_v = max(pts + [0])
    v_range = max_v - min_v or 1.0

    n = len(pts)

    def xp(i: int) -> float:
        return pad_l + (i / max(n - 1, 1)) * cw

    def yp(v: float) -> float:
        return pad_t + (1.0 - (v - min_v) / v_range) * ch

    zero_y = yp(0.0)
    coords = [(xp(i), yp(v)) for i, v in enumerate(pts)]

    # Area path
    area_d = f"M {coords[0][0]:.1f},{zero_y:.1f}"
    for cx, cy in coords:
        area_d += f" L {cx:.1f},{cy:.1f}"
    area_d += f" L {coords[-1][0]:.1f},{zero_y:.1f} Z"

    # Line path
    line_d = " ".join(f"{'M' if i == 0 else 'L'} {cx:.1f},{cy:.1f}"
                      for i, (cx, cy) in enumerate(coords))

    final_v = pts[-1]
    line_col  = "#30D158" if final_v >= 0 else "#FF453A"
    area_col  = "rgba(48,209,88,0.10)" if final_v >= 0 else "rgba(255,69,58,0.09)"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'style="width:100%;height:auto;overflow:visible;font-family:\'JetBrains Mono\',monospace;display:block">'
    ]

    # Zero baseline
    parts.append(
        f'<line x1="{pad_l}" y1="{zero_y:.1f}" x2="{pad_l + cw}" y2="{zero_y:.1f}" '
        f'stroke="rgba(255,255,255,0.10)" stroke-dasharray="4,4" stroke-width="1"/>'
    )

    # Area fill
    parts.append(f'<path d="{area_d}" fill="{area_col}"/>')

    # Line
    parts.append(
        f'<path d="{line_d}" stroke="{line_col}" stroke-width="2" fill="none" '
        f'stroke-linejoin="round" stroke-linecap="round"/>'
    )

    # Dots + balance labels every other point
    for i, (cx, cy) in enumerate(coords):
        v = pts[i]
        c = "#30D158" if v >= 0 else "#FF453A"
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="3.5" fill="{c}" stroke="{c}" stroke-width="1"/>')
        if i % 2 == 0 or i == n - 1:
            lbl = f"${abs(v):,.0f}" if v >= 0 else f"-${abs(v):,.0f}"
            anchor = "middle" if 0 < i < n - 1 else ("start" if i == 0 else "end")
            y_off = cy - 8 if cy > pad_t + 18 else cy + 16
            parts.append(
                f'<text x="{cx:.1f}" y="{y_off:.1f}" text-anchor="{anchor}" '
                f'font-size="9" fill="{c}" opacity="0.85">{lbl}</text>'
            )

    parts.append("</svg>")
    return "".join(parts)
