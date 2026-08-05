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


def _external_out(amount: float, rules: list[dict]) -> float:
    total = 0.0
    for r in rules:
        if r["value_type"] == "pct":
            total += amount * r["value"] / 100.0
        elif r["value_type"] == "fixed":
            total += r["value"]
    return round(total, 2)


def _paycheck_allocs(amount: float, rules: list[dict]) -> list[dict]:
    """How a paycheck is split, for display (internal amounts may be None when the
    rule is 'fund to target')."""
    out = []
    for r in rules:
        if r["value_type"] == "pct":
            val = round(amount * r["value"] / 100.0, 2)
        elif r["value_type"] == "fixed":
            val = round(r["value"], 2)
        else:
            val = None                               # fund-to-target: amount varies
        out.append({"name": r["name"], "amount": val, "kind": r["kind"]})
    return out


def project(start_balance: float, paychecks: list[dict], rules: list[dict],
            bills: list[dict], today: date | None = None, horizon_days: int = 90) -> dict:
    """Roll the checking balance forward. See module docstring for the model.

    paychecks: [{label, amount, freq, anchor}]
    rules:     [{name, kind, value, value_type, active}]   (kind in internal/external)
    bills:     [{name, amount(target), spent, available, due_day, frequency}]
    """
    today = today or date.today()
    end = today + timedelta(days=horizon_days)
    ext_rules = [r for r in rules if r.get("active") and r["kind"] == "external"]
    int_rules = [r for r in rules if r.get("active") and r["kind"] == "internal"]

    events: list[dict] = []

    for pc in paychecks:
        amt = round(pc["amount"], 2)
        ext = _external_out(amt, ext_rules)
        allocs = _paycheck_allocs(amt, ext_rules + int_rules)
        for d in pay_dates(pc.get("anchor", ""), pc.get("freq", "biweekly"), today, end):
            events.append({"date": d, "kind": "income", "name": pc["label"],
                           "income": amt, "external": ext, "allocs": allocs})

    for b in bills:
        target = round(b["amount"], 2)
        spent = round(b.get("spent", 0.0), 2)
        for d in bill_dates(b.get("due_day"), b.get("frequency"), today, end):
            # This month's real obligation is what's left after money already spent.
            this_month = (d.year, d.month) == (today.year, today.month)
            amt = max(0.0, round(target - spent, 2)) if this_month else target
            if amt <= 0.005:
                continue
            # "unfunded" only means something for money you should already have set
            # aside — this cycle. Future bills aren't alarms; the balance line is.
            funded = (b.get("available", 0.0) >= amt - 0.005) if this_month else True
            events.append({"date": d, "kind": "bill", "name": b["name"],
                           "amount": amt, "funded": funded, "this_month": this_month})

    # income before bills on the same day (you get paid, then bills clear)
    events.sort(key=lambda e: (e["date"], 0 if e["kind"] == "income" else 1))

    running = round(start_balance, 2)
    trajectory = [{"date": today.isoformat(), "balance": running}]
    low = {"balance": running, "date": today.isoformat()}
    for e in events:
        if e["kind"] == "income":
            running = round(running + e["income"] - e["external"], 2)
        else:
            running = round(running - e["amount"], 2)
        e["balance_after"] = running
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
        income = round(sum(e["income"] for e in evs if e["kind"] == "income"), 2)
        external = round(sum(e["external"] for e in evs if e["kind"] == "income"), 2)
        bill_evs = [e for e in evs if e["kind"] == "bill"]
        bills_out = round(sum(e["amount"] for e in bill_evs), 2)
        end_bal = evs[-1]["balance_after"] if evs else start_bal
        is_gap = not any(e["kind"] == "income" for e in evs)
        label = "Now → first payday" if is_gap else " · ".join(
            sorted({e["name"] for e in evs if e["kind"] == "income"}))
        periods.append({
            "label": label or "Paycheck", "start": ps.isoformat(), "end": pe.isoformat(),
            "is_gap": is_gap, "income": income, "external": external, "bills_out": bills_out,
            "unfunded": round(sum(e["amount"] for e in bill_evs if not e["funded"]), 2),
            "start_balance": start_bal, "end_balance": end_bal, "negative": end_bal < 0,
            "allocs": next((e["allocs"] for e in evs if e["kind"] == "income"), []),
            "events": [{"date": e["date"].isoformat(), "kind": e["kind"], "name": e["name"],
                        "amount": e.get("income", e.get("amount", 0.0)),
                        "external": e.get("external", 0.0),
                        "funded": e.get("funded", True), "balance": e["balance_after"]}
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
