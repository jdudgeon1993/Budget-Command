"""
Cadence Forecast — a forward cash-flow projection (pure, no framework).

The question it answers: given the income you've set up, what you've committed
to save, and the bills on your calendar, what's actually left every day from now
forward — and what's the *lowest* it gets? That forward-minimum is the honest
"safe to spend today": dip into it and a future week craters.

Model — a single running balance that depletes for every commitment, not just
the ones that physically leave the bank:
  balance(t) = start + Σ income≤t − Σ internal-set-asides≤t − Σ external-transfers≤t − Σ bills≤t
Internal set-asides (funding a savings goal/vault) don't move the CHECKING
balance at the bank — but once that money has a job, it's not yours to spend
freely, so it comes out of the running number here too. Honoring your own
savings commitments is part of "can I afford this," same as any bill.

Two more things layer on top of the balance line:

  • Per-bill funding — each dated bill tracks its own "saved so far" (seeded
    from the bucket today, topped up by internal rules AND, in Aggressive
    mode, by automatic sinking-fund pacing — see pace_amount()) so a bill's
    per-event "funded"/"shortfall" flag reflects what's actually true by the
    time it's due, not just today's snapshot.

  • Vaults — pure accumulation, no due date. Tracked the same way (seeded from
    today, topped up by internal rules), so growth is visible paycheck by
    paycheck.

  • Warnings — deliberately just one honest question per period: does the
    projected balance ever dip, and how badly (see _period_warnings()). The
    Forecast doesn't try to explain WHICH bucket is short or why — that's
    Buckets' job, and Aggressive pacing's. Two separate, honest questions
    instead of one page trying to answer both.

Aggressive mode (see pace_amount(), paychecks_between(), next_unmet_due()) is
the sinking-fund distribution model: every underfunded dated bill gets paced
toward its due date automatically, evenly split across today + every future
payday before it's due — recomputed fresh each time, which is what gives it a
safety margin for free (once only one future payday remains, that payday
demands the full remaining amount, leaving the true last one as pure slack).
`_build_steps()` in store.py uses the same functions for the live Distribute
plan, so what the Forecast projects and what Distribute actually asks for
agree by construction.

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


def next_payday(anchor_iso: str, freq: str, after: date) -> str | None:
    """The next payday strictly after `after` — used to advance a paycheck's
    stored anchor once it's been received, so a stale anchor (still sitting on
    today or a past date) doesn't get projected again on top of the real
    income already logged in the Ledger. None if the anchor can't be parsed."""
    start = after + timedelta(days=1)
    dates = pay_dates(anchor_iso, freq, start, start + timedelta(days=400))
    return dates[0].isoformat() if dates else None


def paychecks_between(paychecks: list[dict], today: date, due: date) -> int:
    """How many real paydays land in (today, due] — the union across every
    income source, since any of them is a funding opportunity for a bill."""
    if due <= today:
        return 0
    seen = set()
    for pc in paychecks:
        seen.update(pay_dates(pc.get("anchor", ""), pc.get("freq", "biweekly"),
                              today + timedelta(days=1), due))
    return len(seen)


def pace_amount(gap: float, due: date | None, today: date, paychecks: list[dict]) -> float:
    """Sinking-fund pacing: what THIS paycheck should put toward a bill. Split
    evenly across today + every future payday before it's due — BUT this is
    always recomputed fresh, live, against whatever's still actually owed. That
    self-buffering is what gives it the safety margin: once only one future
    payday remains, this one demands the full remaining amount, automatically
    leaving that last payday as pure slack instead of cutting it on the wire.
    Zero future paydays (due before/at the next one) collapses the same way —
    needs it all, now, there's no more runway to spread across."""
    gap = round(max(0.0, gap), 2)
    if gap <= 0.005 or due is None:
        return 0.0
    n = paychecks_between(paychecks, today, due)   # future paydays only, not counting today
    return round(gap / max(1, n), 2)


def next_unmet_due(due_day, frequency, gap: float, days_until_due, today: date) -> date | None:
    """The due date pacing should aim at: the bill's current occurrence if it's
    still unfunded (even if overdue — days_until_due can be negative), otherwise
    the NEXT occurrence after this one's already been satisfied. This is what
    lets pacing keep going the moment a bill clears instead of going idle until
    it's "due" again — e.g. a mortgage paid on the 1st starts pacing toward next
    month's payment immediately, it doesn't wait around."""
    if due_day is None and frequency not in _STEP and frequency != "monthly":
        return None
    if gap > 0.005 and days_until_due is not None:
        return today + timedelta(days=days_until_due)
    dates = bill_dates(due_day, frequency, today + timedelta(days=1), today + timedelta(days=400))
    return dates[0] if dates else None


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


DIP_CAUTION = 1000.0     # below this, the period is worth a look
DIP_DANGER = 0.0         # below this, it's a real overdraft


def _period_warnings(end_bal: float) -> list[dict]:
    """One honest signal per period: does the projected balance ever dip. That's
    the whole question the Forecast answers — not which bucket is short or why
    (that's Buckets' job, and Aggressive pacing's). Below $0 is immediate
    action; below $1,000 is worth a look; otherwise this period is quiet."""
    if end_bal < DIP_DANGER - 0.005:
        return [{"kind": "danger", "severity": 0, "end_balance": round(end_bal, 2)}]
    if end_bal < DIP_CAUTION - 0.005:
        return [{"kind": "caution", "severity": 1, "end_balance": round(end_bal, 2)}]
    return []


def project(start_balance: float, paychecks: list[dict], rules: list[dict],
            bills: list[dict], vaults: list[dict] | None = None,
            scheduled: list[dict] | None = None,
            today: date | None = None, horizon_days: int = 90,
            aggressive: bool = False) -> dict:
    """Roll the checking balance forward. See module docstring for the model.

    paychecks: [{label, amount, freq, anchor}]
    rules:     [{name, kind, value, value_type, active, bucket_name, bucket_id}]
    bills:     [{id, name, amount(target), spent, available, due_day, frequency}]
    vaults:    [{id, name, available}]                  (vault/goal buckets — pure
                accumulation, no due date, tracked the same way as bill funding)
    scheduled: [{kind, amount, date, bucket_id, name}]   (future-dated real txns)
    """
    today = today or date.today()
    end = today + timedelta(days=horizon_days)
    ext_rules = [r for r in rules if r.get("active") and r["kind"] == "external"]
    int_rules = [r for r in rules if r.get("active") and r["kind"] == "internal"
                 and r.get("value_type") in ("pct", "fixed")]
    scheduled = scheduled or []
    vaults = vaults or []

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
                                   "bucket": r.get("bucket_name"), "bucket_id": r.get("bucket_id")})

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

    # Each dated bill has its own running "available" — what's actually saved
    # toward it — seeded from the bucket today and topped up by internal
    # set-asides aimed at it as paydays land, in chronological order. This is
    # what answers "will this paycheck actually afford the bill," not just
    # whether cash overall survives: a bill can clear (money leaves checking
    # either way) while still being genuinely UNDER-saved-for.
    bucket_avail: dict[str, float] = {
        b["id"]: round(b.get("available", 0.0), 2)
        for b in bills if b.get("id") and b.get("frequency") not in _PPM
    }
    # Vaults never "clear" — they just accumulate. Same tracking, no bill event.
    vault_avail: dict[str, float] = {v["id"]: round(v.get("available", 0.0), 2) for v in vaults if v.get("id")}
    vault_names = {v["id"]: v["name"] for v in vaults if v.get("id")}
    vaults_today = round(sum(vault_avail.values()), 2)

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
                                   "amount": per, "funded": True, "shortfall": 0.0, "cadence": freq})
        else:
            spent = round(b.get("spent", 0.0), 2)
            for d in bill_dates(b.get("due_day"), freq, today, end):
                this_month = (d.year, d.month) == (today.year, today.month)
                base = max(0.0, round(target - spent, 2)) if this_month else target
                # a scheduled payment against this bucket this month already covers it
                base = round(max(0.0, base - sched_exp.get((bid, (d.year, d.month)), 0.0)), 2)
                if base <= 0.005:
                    continue
                # funded/shortfall is resolved once events are walked in order below —
                # it depends on what's landed in the bucket by THIS date, not just today.
                events.append({"date": d, "kind": "bill", "name": b["name"],
                               "amount": base, "_bid": bid, "_target": base})

    # Aggressive pacing: every dated bill without an explicit internal rule
    # already claiming it gets the same sinking-fund pace Distribute uses —
    # a placeholder event per payday, its amount resolved live during the walk
    # below against that moment's actual remaining gap. That's what lets a
    # future period correctly show a bill as funded by the time it's due,
    # instead of only ever seeing today's snapshot.
    if aggressive:
        ruled_buckets = {r.get("bucket_id") for r in int_rules if r.get("bucket_id")}
        bill_occurrences: dict[str, list[dict]] = {}
        for e in events:
            # a split bucket's individual bill items carry no bucket id of their
            # own (the money pool is the parent bucket, which isn't represented
            # here at all) — grouping by _bid would merge unrelated items from
            # different split buckets under the same "None" key and double-count
            # them as a phantom pacing contribution on top of their real bill
            # event. Nothing to pace toward without a real bucket, so skip them.
            if e["kind"] == "bill" and e.get("_bid"):
                bill_occurrences.setdefault(e["_bid"], []).append(e)
        for occ in bill_occurrences.values():
            occ.sort(key=lambda x: x["date"])
        all_paydays = sorted({e["date"] for e in events if e["kind"] == "income"})
        for bid, occ in bill_occurrences.items():
            if bid in ruled_buckets:
                continue
            for d in all_paydays:
                events.append({"date": d, "kind": "internal", "name": "Paced funding",
                               "amount": 0.0, "bucket_id": bid, "_pace_occ": occ})

    # Same-day order: income first, then set-asides, transfers out, bills clear.
    _ord = {"income": 0, "internal": 1, "transfer": 2, "bill": 3}
    events.sort(key=lambda e: (e["date"], _ord[e["kind"]]))

    running = round(start_balance, 2)
    trajectory = [{"date": today.isoformat(), "balance": running}]
    low = {"balance": running, "date": today.isoformat()}
    for e in events:
        if e["kind"] == "internal" and "_pace_occ" in e:
            occ = [o for o in e["_pace_occ"] if o["date"] > e["date"]]
            if occ:
                nxt = occ[0]
                gap_now = max(0.0, round(nxt["_target"] - bucket_avail.get(e["bucket_id"], 0.0), 2))
                e["amount"] = pace_amount(gap_now, nxt["date"], e["date"], paychecks)
                e["bucket"] = nxt["name"]
        if e["kind"] == "internal":
            bid = e.get("bucket_id")
            if bid in bucket_avail:
                bucket_avail[bid] = round(bucket_avail[bid] + e["amount"], 2)
            if bid in vault_avail:
                vault_avail[bid] = round(vault_avail[bid] + e["amount"], 2)
                e["vault_name"] = vault_names.get(bid)
                e["vault_balance_after"] = vault_avail[bid]
        elif e["kind"] == "bill" and "_bid" in e:
            bid, tgt = e["_bid"], e["_target"]
            have = bucket_avail.get(bid, 0.0)
            if round(have - tgt, 2) >= -0.005:
                e["funded"], e["shortfall"] = True, 0.0
                bucket_avail[bid] = round(have - tgt, 2)
            else:
                e["funded"], e["shortfall"] = False, round(tgt - have, 2)
                bucket_avail[bid] = 0.0   # this occurrence used up everything saved
        # every event depletes the running balance — income adds, everything else
        # (internal set-asides included) subtracts, so the number always reflects
        # what's actually left once you've honored your own savings commitments too.
        running = round(running + e["amount"] if e["kind"] == "income" else running - e["amount"], 2)
        e["balance_after"] = running
        e["_vaults_total_after"] = round(sum(vault_avail.values()), 2)
        trajectory.append({"date": e["date"].isoformat(), "balance": running})
        if running < low["balance"]:
            low = {"balance": running, "date": e["date"].isoformat()}

    # a paced bucket already fully covered by the time a payday lands resolves
    # to $0 — drop those rather than showing a zero-amount "paced funding" line
    events = [e for e in events if not ("_pace_occ" in e and e["amount"] <= 0.005)]

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

    periods, start_bal, vault_bal = [], round(start_balance, 2), vaults_today
    for ps, pe in bounds:
        evs = [e for e in events if ps <= e["date"] <= pe]
        income = round(sum(e["amount"] for e in evs if e["kind"] == "income"), 2)
        external = round(sum(e["amount"] for e in evs if e["kind"] == "transfer"), 2)
        internal = round(sum(e["amount"] for e in evs if e["kind"] == "internal"), 2)
        bill_evs = [e for e in evs if e["kind"] == "bill"]
        bills_out = round(sum(e["amount"] for e in bill_evs), 2)
        end_bal = evs[-1]["balance_after"] if evs else start_bal
        vault_bal = evs[-1]["_vaults_total_after"] if evs else vault_bal
        is_gap = not any(e["kind"] == "income" for e in evs)
        label = "Now → first payday" if is_gap else " · ".join(
            sorted({e["name"] for e in evs if e["kind"] == "income"}))
        periods.append({
            "label": label or "Paycheck", "start": ps.isoformat(), "end": pe.isoformat(),
            "is_gap": is_gap, "income": income, "external": external, "internal": internal,
            "bills_out": bills_out,
            "start_balance": start_bal, "end_balance": end_bal, "negative": end_bal < 0,
            "vaults_total": vault_bal,
            "warnings": _period_warnings(end_bal),
            "events": [{"date": e["date"].isoformat(), "kind": e["kind"], "name": e["name"],
                        "amount": round(e["amount"], 2), "funded": e.get("funded", True),
                        "shortfall": round(e.get("shortfall", 0.0), 2),
                        "cadence": e.get("cadence"), "scheduled": e.get("scheduled", False),
                        "bucket": e.get("bucket"), "vault_name": e.get("vault_name"),
                        "vault_balance_after": e.get("vault_balance_after"),
                        "balance": e["balance_after"]}
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
        "vaults_today": vaults_today,
        "total_income": round(sum(p["income"] for p in periods), 2),
        "total_out": round(sum(p["external"] + p["internal"] + p["bills_out"] for p in periods), 2),
        "trajectory": trajectory,
        "periods": periods,
    }
