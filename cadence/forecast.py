"""
Cadence Forecast — a forward cash-flow projection (pure, no framework).

The question it answers: given the income you've set up and the bills on your
calendar, what does your checking balance look like every day from now forward —
and what's the *lowest* it gets? That forward-minimum is the honest "safe to
spend today": dip into it and a future week craters.

Model (deliberately a cash-flow view of the checking account):
  balance(t) = start + Σ income≤t − Σ external-transfers≤t − Σ bills≤t
Internal funding (moving money between envelopes inside the account) doesn't
move the checking balance, so it's shown as info, not an outflow. External rules
(401k, transfers out) and dated bills are the real outflows.

Everything here is a pure function of plain dicts, so the demo store and the live
Supabase store feed it exactly the same way.
"""
from __future__ import annotations

import calendar
from datetime import date, timedelta

_STEP = {"weekly": 7, "biweekly": 14, "triweekly": 21}
# Periods per month (30.44-day average) — spreads a monthly target across a cadence.
_PPM = {"weekly": 30.44 / 7, "biweekly": 30.44 / 14, "triweekly": 30.44 / 21}


def _day_date(due_day, y: int, m: int) -> date:
    last = calendar.monthrange(y, m)[1]
    if isinstance(due_day, str) and due_day.lower() == "eom":
        return date(y, m, last)
    return date(y, m, min(int(due_day), last))


def _next_month(y: int, m: int) -> tuple[int, int]:
    return (y + 1, 1) if m == 12 else (y, m + 1)


def pay_dates(anchor_iso: str, freq: str, start: date, end: date) -> list[date]:
    """Paydays in [start, end] for a paycheck anchored at its next occurrence."""
    try:
        anchor = date.fromisoformat(str(anchor_iso)[:10])
    except (ValueError, TypeError):
        return []

    if freq == "semimonthly":                       # 1st & 15th each month
        out, (y, m) = [], (start.year, start.month)
        while date(y, m, 1) <= end:
            for day in (1, 15):
                d = _day_date(day, y, m)
                if start <= d <= end:
                    out.append(d)
            y, m = _next_month(y, m)
        return sorted(out)

    if freq == "monthly":
        out, (y, m) = [], (start.year, start.month)
        while True:
            d = _day_date(anchor.day, y, m)
            if d > end:
                break
            if d >= start:
                out.append(d)
            y, m = _next_month(y, m)
        return out

    step = _STEP.get(freq, 14)                       # weekly / biweekly (default)
    d = anchor
    if d < start:                                    # fast-forward to the window
        d += timedelta(days=((start - d).days + step - 1) // step * step)
    out = []
    while d <= end:
        if d >= start:
            out.append(d)
        d += timedelta(days=step)
    return out


def bill_dates(due_day, frequency, start: date, end: date) -> list[date]:
    """Due dates in [start, end] for a bill. A due_day gives a monthly date (or a
    recurring one if paired with a weekly/biweekly/triweekly frequency); a bare
    frequency with no due_day recurs from `start`."""
    out: list[date] = []
    if due_day is not None and due_day != "":
        if frequency in _STEP:
            d = _day_date(due_day, start.year, start.month)
            while d < start:
                d += timedelta(days=_STEP[frequency])
            while d <= end:
                out.append(d)
                d += timedelta(days=_STEP[frequency])
            return out
        y, m = start.year, start.month              # monthly on the due day
        while True:
            d = _day_date(due_day, y, m)
            if d > end:
                break
            if d >= start:
                out.append(d)
            y, m = _next_month(y, m)
        return out

    if frequency == "monthly":
        y, m = start.year, start.month
        while True:
            d = max(date(y, m, 1), start) if (y, m) == (start.year, start.month) else date(y, m, 1)
            if d > end:
                break
            out.append(d)
            y, m = _next_month(y, m)
        return out
    if frequency in _STEP:
        d = start
        while d <= end:
            out.append(d)
            d += timedelta(days=_STEP[frequency])
    return out


def project(start_balance: float, paychecks: list[dict], rules: list[dict],
            bills: list[dict], scheduled: list[dict] | None = None,
            today: date | None = None, horizon_days: int = 90) -> dict:
    """Roll the checking balance forward. See module docstring for the model.

    Injects *everything* that moves the account: recurring income (paychecks),
    external transfers out (rules), recurring bills (bucket targets), AND any
    specific future-dated transactions the user has already entered (scheduled
    payments, transfers, expected income). Internal rule allocations (funding
    savings goals / vaults) are shown per paycheck as money set aside — they don't
    leave checking, so they don't move the balance line, but you see where the
    paycheck goes.

    paychecks: [{label, amount, freq, anchor}]
    rules:     [{name, kind, value, value_type, active, bucket_name}]
    bills:     [{id, name, amount(target), spent, available, due_day, frequency}]
    scheduled: [{kind, amount, date, bucket_id, name}]   (future-dated real txns)
    """
    today = today or date.today()
    end = today + timedelta(days=horizon_days)
    ext_rules = [r for r in rules if r.get("active") and r["kind"] == "external"]
    int_rules = [r for r in rules if r.get("active") and r["kind"] == "internal"
                 and r.get("value_type") in ("pct", "fixed")]
    scheduled = scheduled or []

    events: list[dict] = []

    # Paydays: income lands; external rules move money out; internal rules set money
    # aside (info — stays in checking). Each is its own line so it reads like a register.
    for pc in paychecks:
        amt = round(pc["amount"], 2)
        for d in pay_dates(pc.get("anchor", ""), pc.get("freq", "biweekly"), today, end):
            events.append({"date": d, "kind": "income", "name": pc["label"], "amount": amt})
            for r in ext_rules:
                v = round(amt * r["value"] / 100.0 if r["value_type"] == "pct" else r["value"], 2)
                if v > 0.005:
                    events.append({"date": d, "kind": "transfer", "name": r["name"], "amount": v})
            for r in int_rules:
                v = round(amt * r["value"] / 100.0 if r["value_type"] == "pct" else r["value"], 2)
                if v > 0.005:
                    events.append({"date": d, "kind": "internal", "name": r["name"], "amount": v,
                                   "bucket": r.get("bucket_name")})

    # Specific future-dated transactions the user already entered — the real,
    # committed items. Scheduled expenses against a bucket also suppress that
    # bucket's recurring estimate for the month so nothing double-counts.
    sched_exp: dict[tuple, float] = {}
    for t in scheduled:
        try:
            d = date.fromisoformat(str(t.get("date"))[:10])
        except (ValueError, TypeError):
            continue
        if not (today < d <= end):
            continue
        amt = round(abs(t.get("amount", 0.0)), 2)
        if amt <= 0.005:
            continue
        k, ym = t.get("kind"), (d.year, d.month)
        if k in ("income", "refund"):
            events.append({"date": d, "kind": "income", "name": t.get("name") or "Income", "amount": amt, "scheduled": True})
        elif k == "transfer":
            events.append({"date": d, "kind": "transfer", "name": t.get("name") or "Transfer", "amount": amt, "scheduled": True})
        elif k == "expense":
            events.append({"date": d, "kind": "bill", "name": t.get("name") or "Payment", "amount": amt,
                           "funded": True, "scheduled": True})
            if t.get("bucket_id"):
                sched_exp[(t["bucket_id"], ym)] = round(sched_exp.get((t["bucket_id"], ym), 0.0) + amt, 2)

    # Bills. A dated bill (due day, no sub-monthly frequency) hits its full amount
    # once a month. A weekly/bi-weekly/tri-weekly bucket spreads its MONTHLY target
    # across the periods — $400/mo weekly ≈ $92 a week (sums back to the month).
    for b in bills:
        target = round(b["amount"], 2)
        freq, bid = b.get("frequency"), b.get("id")
        if freq in _PPM:
            per = round(target / _PPM[freq], 2)
            if per > 0.005:
                for d in bill_dates(b.get("due_day"), freq, today, end):
                    events.append({"date": d, "kind": "bill", "name": b["name"],
                                   "amount": per, "funded": True, "cadence": freq})
        else:
            spent = round(b.get("spent", 0.0), 2)
            for d in bill_dates(b.get("due_day"), freq, today, end):
                this_month = (d.year, d.month) == (today.year, today.month)
                base = max(0.0, round(target - spent, 2)) if this_month else target
                # a scheduled payment against this bucket this month already covers it
                base = round(max(0.0, base - sched_exp.get((bid, (d.year, d.month)), 0.0)), 2)
                if base <= 0.005:
                    continue
                funded = (b.get("available", 0.0) >= base - 0.005) if this_month else True
                events.append({"date": d, "kind": "bill", "name": b["name"],
                               "amount": base, "funded": funded})

    # Same-day order: income first, then set-asides, transfers out, bills clear.
    _ord = {"income": 0, "internal": 1, "transfer": 2, "bill": 3}
    events.sort(key=lambda e: (e["date"], _ord[e["kind"]]))

    running = round(start_balance, 2)
    trajectory = [{"date": today.isoformat(), "balance": running}]
    low = {"balance": running, "date": today.isoformat()}
    for e in events:
        if e["kind"] == "income":
            running = round(running + e["amount"], 2)
        elif e["kind"] in ("transfer", "bill"):        # internal set-asides don't leave checking
            running = round(running - e["amount"], 2)
        e["balance_after"] = running
        if e["kind"] != "internal":
            trajectory.append({"date": e["date"].isoformat(), "balance": running})
        if running < low["balance"]:
            low = {"balance": running, "date": e["date"].isoformat()}

    # ── pay periods (payday → day before next payday) ─────────────────────────
    pay_ds = sorted({e["date"] for e in events if e["kind"] == "income"})
    bounds: list[tuple[date, date]] = []
    if not pay_ds:
        bounds.append((today, end))
    else:
        if pay_ds[0] > today:
            bounds.append((today, pay_ds[0] - timedelta(days=1)))
        for i, pd in enumerate(pay_ds):
            pe = pay_ds[i + 1] - timedelta(days=1) if i + 1 < len(pay_ds) else end
            bounds.append((pd, pe))

    periods, start_bal = [], round(start_balance, 2)
    for ps, pe in bounds:
        evs = [e for e in events if ps <= e["date"] <= pe]
        income = round(sum(e["amount"] for e in evs if e["kind"] == "income"), 2)
        external = round(sum(e["amount"] for e in evs if e["kind"] == "transfer"), 2)
        internal = round(sum(e["amount"] for e in evs if e["kind"] == "internal"), 2)
        bill_evs = [e for e in evs if e["kind"] == "bill"]
        bills_out = round(sum(e["amount"] for e in bill_evs), 2)
        # last non-internal event carries the period's ending balance
        bal_evs = [e for e in evs if e["kind"] != "internal"]
        end_bal = bal_evs[-1]["balance_after"] if bal_evs else start_bal
        is_gap = not any(e["kind"] == "income" for e in evs)
        label = "Now → first payday" if is_gap else " · ".join(
            sorted({e["name"] for e in evs if e["kind"] == "income"}))
        periods.append({
            "label": label or "Paycheck", "start": ps.isoformat(), "end": pe.isoformat(),
            "is_gap": is_gap, "income": income, "external": external, "internal": internal,
            "bills_out": bills_out,
            "unfunded": round(sum(e["amount"] for e in bill_evs if not e.get("funded", True)), 2),
            "start_balance": start_bal, "end_balance": end_bal, "negative": end_bal < 0,
            "events": [{"date": e["date"].isoformat(), "kind": e["kind"], "name": e["name"],
                        "amount": round(e["amount"], 2), "funded": e.get("funded", True),
                        "cadence": e.get("cadence"), "scheduled": e.get("scheduled", False),
                        "bucket": e.get("bucket"), "balance": e["balance_after"]}
                       for e in evs],
        })
        start_bal = end_bal

    safe = max(0.0, round(low["balance"], 2))
    return {
        "start_balance": round(start_balance, 2),
        "horizon_days": horizon_days,
        "today": today.isoformat(),
        "end_date": end.isoformat(),
        "low": {"balance": round(low["balance"], 2), "date": low["date"]},
        "safe_to_spend": safe,
        "shortfall": low["balance"] < -0.005,
        "total_income": round(sum(p["income"] for p in periods), 2),
        "total_out": round(sum(p["external"] + p["bills_out"] for p in periods), 2),
        "trajectory": trajectory,
        "periods": periods,
    }
