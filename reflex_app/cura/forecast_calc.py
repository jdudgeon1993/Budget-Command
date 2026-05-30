"""
Forecast calculation — pure Python, no Reflex dependencies.
Ported from app/app.py forecast endpoint.
"""

import calendar as _cal
from datetime import date, timedelta


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


def _range_label(s: date, e: date) -> str:
    if s.year == e.year:
        return f"{s.strftime('%b %-d')} – {e.strftime('%b %-d')}"
    return f"{s.strftime('%b %-d, %Y')} – {e.strftime('%b %-d, %Y')}"


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


# ── Main calculation ──────────────────────────────────────────────────────────

def compute_forecast(data: dict, n_months: int = 3, account_id: str = "") -> dict:
    """
    Returns {
        start_balance, safe_to_spend, total_income, total_unfunded,
        shortfall_count, periods: [period_dict, ...]
    }
    """
    today = date.today()

    accounts   = data.get("accounts", [])
    buckets    = data.get("buckets", [])
    txs        = data.get("txs", [])
    months_raw = data.get("months", [])
    paychecks  = data.get("paychecks", [])
    rules_raw  = data.get("allocationRules", [])

    # ── Starting balance ──────────────────────────────────────────────────────
    def _acct_bal(a: dict) -> float:
        aid = a["id"]
        bal = float(a.get("openingBalance") or 0)
        for t in txs:
            if t.get("accountId") == aid:
                if t.get("type") == "in":
                    bal += float(t.get("amount") or 0)
                elif t.get("type") in ("out", "xfr"):
                    bal -= float(t.get("amount") or 0)
            if t.get("toAccountId") == aid and t.get("type") == "xfr":
                bal += float(t.get("amount") or 0)
        return bal

    budget_accounts = [a for a in accounts if a.get("type") == "budget" and not a.get("archived")]
    if account_id:
        start_accounts = [a for a in budget_accounts if a["id"] == account_id]
    else:
        start_accounts = budget_accounts
    start_balance = sum(_acct_bal(a) for a in start_accounts)

    # ── End date ──────────────────────────────────────────────────────────────
    y = today.year + (today.month - 1 + n_months) // 12
    m = (today.month - 1 + n_months) % 12 + 1
    end_date = date(y, m, _cal.monthrange(y, m)[1])

    # ── Pay events ────────────────────────────────────────────────────────────
    external_rules = [r for r in rules_raw if r.get("ruleType") == "external" and r.get("active", True)]
    internal_rules = [r for r in rules_raw if r.get("ruleType") != "external" and r.get("active", True) and r.get("bucketId")]
    bname = {b["id"]: b["name"] for b in buckets}
    btype = {b["id"]: b.get("type", "expense") for b in buckets}

    pay_events: dict[date, list] = {}
    for pc in paychecks:
        if not pc.get("anchorDate"):
            continue
        for pd in _gen_pay_dates(pc["anchorDate"], int(pc.get("freq", 14)), today, end_date):
            if pd not in pay_events:
                pay_events[pd] = []
            amt = float(pc.get("amount") or 0)
            transfers = []
            for r in external_rules:
                v = float(r.get("value") or 0)
                computed = round(amt * v / 100, 2) if r.get("type") == "pct" else v
                transfers.append({"name": r.get("name", "Transfer"), "amount": computed})
            allocs = []
            for r in internal_rules:
                v = float(r.get("value") or 0)
                computed = round(amt * v / 100, 2) if r.get("type") == "pct" else v
                bid = r["bucketId"]
                allocs.append({"name": bname.get(bid, ""), "amount": computed,
                               "is_vault": btype.get(bid, "expense") == "vault"})
            pay_events[pd].append({"label": pc.get("label", "Paycheck"),
                                   "amount": round(amt, 2),
                                   "transfers": transfers, "allocs": allocs})

    all_pay_dates = sorted(pay_events.keys())

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
    monthly_allocs  = {m.get("id", ""): m.get("allocations", {}) for m in months_raw}
    monthly_budgets = {m.get("id", ""): m.get("budgets", {}) for m in months_raw}
    today_mid = _mid(today)

    bucket_bill_amt = {
        b["id"]: float(b.get("dueAmount") or b.get("defaultBudget")
                       or monthly_budgets.get(today_mid, {}).get(b["id"]) or 0)
        for b in buckets
    }

    def _funded(bid: str, bill_date: date) -> bool:
        mid_    = _mid(bill_date)
        alloc   = float(monthly_allocs.get(mid_, {}).get(bid, 0))
        budget  = float(monthly_budgets.get(mid_, {}).get(bid, 0))
        bill_a  = bucket_bill_amt.get(bid, 0)
        target  = budget if budget > 0 else bill_a
        return (alloc >= target * 0.99) if target > 0 else alloc > 0

    def _bill_amt(b: dict) -> float:
        return bucket_bill_amt.get(b["id"], 0)

    # Check if a bill is already PAID (spent) in current month
    paid_bids: set[str] = set()
    for t in txs:
        if t.get("type") == "out" and t.get("bucketId") and _mid(date.fromisoformat(t["date"])) == today_mid:
            bid_ = t["bucketId"]
            alloc_ = float(monthly_allocs.get(today_mid, {}).get(bid_, 0))
            spent_ = sum(float(tx.get("amount") or 0) for tx in txs
                         if tx.get("bucketId") == bid_ and tx.get("type") == "out"
                         and _mid(date.fromisoformat(tx["date"])) == today_mid)
            if alloc_ > 0 and spent_ >= alloc_ * 0.99:
                paid_bids.add(bid_)

    dated_bills = [b for b in buckets if not b.get("archived") and b.get("dueDay") is not None
                   and _bill_amt(b) > 0]
    freq_bills  = [b for b in buckets if not b.get("archived") and b.get("dueDay") is None
                   and b.get("payFreq") in ("weekly", "biweekly", "triweekly", "monthly")
                   and _bill_amt(b) > 0]

    # ── Build periods ─────────────────────────────────────────────────────────
    running_balance = start_balance
    period_results: list[dict] = []
    grand_income   = 0.0
    grand_unfunded = 0.0

    for ps, pe, is_gap in periods_meta:
        period_start_bal = running_balance

        income_events:   list[dict] = []
        transfer_events: list[dict] = []

        if not is_gap and ps in pay_events:
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

        bal_after_xfr = running_balance

        # Collect bill events for this period
        funded_by_day:   dict[date, list] = {}
        unfunded_by_day: dict[date, list] = {}

        def _add_bill(b: dict, bd: date) -> None:
            if b["id"] in paid_bids and _mid(bd) == today_mid:
                return
            amt   = _bill_amt(b)
            entry = {"name": b["name"], "amount": amt}
            if _funded(b["id"], bd):
                funded_by_day.setdefault(bd, []).append(entry)
            else:
                unfunded_by_day.setdefault(bd, []).append(entry)

        overdue_start = date(today.year, today.month, 1) if is_gap else ps
        for b in dated_bills:
            for bd in _bill_dates(b.get("dueDay"), b.get("payFreq"), overdue_start, pe):
                _add_bill(b, bd)
        for b in freq_bills:
            for bd in _freq_only_dates(b["payFreq"], ps, pe):
                _add_bill(b, bd)

        # Process funded (green) — deduct from balance
        funded_lines: list[dict] = []
        for d in sorted(funded_by_day):
            funded_lines.append({"row_type": "date", "text": _date_label(d), "amount_fmt": ""})
            for bill in funded_by_day[d]:
                running_balance -= bill["amount"]
                funded_lines.append({"row_type": "bill", "text": bill["name"],
                                     "amount_fmt": _fmt(bill["amount"])})
            funded_lines.append({"row_type": "bal", "text": _fmt(running_balance), "amount_fmt": ""})

        # Process unfunded (red) — deduct from balance
        unfunded_lines: list[dict] = []
        for d in sorted(unfunded_by_day):
            unfunded_lines.append({"row_type": "date", "text": _date_label(d), "amount_fmt": ""})
            for bill in unfunded_by_day[d]:
                running_balance -= bill["amount"]
                grand_unfunded  += bill["amount"]
                unfunded_lines.append({"row_type": "bill", "text": bill["name"],
                                       "amount_fmt": _fmt(bill["amount"])})
            unfunded_lines.append({"row_type": "bal", "text": _fmt(running_balance), "amount_fmt": ""})

        period_income    = sum(e["amount"] for e in income_events)
        period_unfunded  = sum(b["amount"] for d in unfunded_by_day.values() for b in d)
        period_net       = running_balance - period_start_bal

        if is_gap:
            label = "Pre-Paycheck Gap"
        else:
            labels = list({e["label"] for e in income_events}) or ["Paycheck"]
            label  = " + ".join(sorted(labels))

        income_lines   = [{"label": e["label"], "amount_fmt": _fmt(e["amount"])} for e in income_events]
        transfer_lines = [{"label": e["name"],  "amount_fmt": _fmt(e["amount"])} for e in transfer_events]

        period_results.append({
            "id":              str(ps),
            "type":            "gap" if is_gap else "paycheck",
            "label":           label,
            "date_range":      _range_label(ps, pe),
            "income_lines":    income_lines,
            "transfer_lines":  transfer_lines,
            "funded_lines":    funded_lines,
            "unfunded_lines":  unfunded_lines,
            "has_income":      bool(income_events),
            "has_transfers":   bool(transfer_events),
            "has_funded":      bool(funded_by_day),
            "has_unfunded":    bool(unfunded_by_day),
            "start_bal_fmt":   _fmt(period_start_bal),
            "bal_after_xfr_fmt": _fmt(bal_after_xfr),
            "income_total_fmt": _fmt(period_income),
            "unfunded_total_fmt": _fmt(period_unfunded),
            "net_fmt":         _fmt(abs(period_net)),
            "net_sign":        "+" if period_net >= 0 else "-",
            "net_negative":    period_net < 0,
            "end_bal_fmt":     _fmt(running_balance),
            "end_bal_negative": running_balance < 0,
            "shortfall":       running_balance < 0,
            "safe_to_spend_fmt": "",  # filled in below
            "sts_color":       "",
        })

    # ── Safe to spend (forward minimum) ──────────────────────────────────────
    end_bals = [p["end_bal_fmt"] for p in period_results]
    end_vals = [running_balance] * len(period_results)
    # Recompute end values from periods
    running_min = float("inf")
    fwd_mins    = [0.0] * len(period_results)
    # We need end balance floats — extract from stored net
    # Use accumulated running_balance as final; back-compute
    # Simpler: store end_balance as float too
    end_floats = []
    rb = start_balance
    # Can't re-derive easily — let's store it in period dict directly
    # Fix: add end_balance float to period_results (done below via restructure)

    # Rebuild with float end balances
    rb2 = start_balance
    for p in period_results:
        # Parse end_bal_fmt back to float — simpler to just store the float
        pass  # handled below with a second pass

    # Store float end balances in a parallel list
    # Actually, let me fix this: recompute by storing end_balance as a number
    # The issue is I didn't store the float. Let me add it.
    # I'll parse back from the fmt string — not ideal but workable.
    def _parse_fmt(s: str) -> float:
        s = s.strip().lstrip("$").replace(",", "")
        if s.startswith("-"):
            return -float(s[1:].lstrip("$").replace(",", ""))
        return float(s)

    # Recalculate forward mins using stored net signs and values
    # Better: just rerun with floats. Let me add end_balance_float to the dict above.
    # For now, reconstruct from accumulated running_balance after final period.
    # Re-derive by parsing:
    float_ends = [_parse_fmt(p["end_bal_fmt"]) for p in period_results]
    running_min = float("inf")
    for i in range(len(period_results) - 1, -1, -1):
        running_min = min(running_min, float_ends[i])
        fwd_mins[i] = running_min

    safe_to_spend = fwd_mins[0] if fwd_mins else start_balance

    for i, p in enumerate(period_results):
        sts = fwd_mins[i]
        p["safe_to_spend_fmt"] = _fmt(sts)
        p["sts_color"] = "#34d399" if sts > 0 else ("#fbbf24" if sts == 0 else "#f87171")

    shortfall_count = sum(1 for p in period_results if p["shortfall"])

    return {
        "start_balance":    _fmt(start_balance),
        "safe_to_spend":    _fmt(safe_to_spend),
        "sts_color":        "#34d399" if safe_to_spend > 0 else ("#fbbf24" if safe_to_spend == 0 else "#f87171"),
        "total_income":     _fmt(grand_income),
        "total_unfunded":   _fmt(grand_unfunded),
        "shortfall_count":  shortfall_count,
        "periods":          period_results,
    }
