"""
Cadence money domain — pure functions, no framework.

The single invariant that keeps every screen honest:

    Available Balance  ==  Unallocated + Σ over ALL envelopes (funded − spent)

`funded` is authoritative (fund/defund move it; spending never does).
`spent` is DERIVED from the ledger, so editing a transaction recomputes live.
Ready to Spend excludes vaults (locked savings). Nothing is cached.
"""

from __future__ import annotations
import uuid
import calendar
from datetime import date

SPEND, GOAL, VAULT = "spend", "goal", "vault"
EXPENSE, INCOME, REFUND = "expense", "income", "refund"


def genesis(opening: float) -> dict:
    return {"opening": round(opening, 2), "unallocated": round(opening, 2),
            "categories": [], "envelopes": [], "transactions": [],
            "paychecks": [], "rules": []}


def _id() -> str:
    return uuid.uuid4().hex[:12]


def add_category(s: dict, name: str, color: str) -> dict:
    c = {"id": _id(), "name": name, "color": color}
    s["categories"].append(c)
    return c


def add_envelope(s: dict, name: str, cat_id: str, type: str = SPEND,
                 target: float = 0.0, funded: float = 0.0,
                 due_day=None, frequency: str | None = None,
                 flex: bool = False, target_date: str | None = None,
                 notes: str = "") -> dict:
    e = {"id": _id(), "name": name, "cat_id": cat_id, "type": type,
         "target": round(target, 2), "funded": round(funded, 2),
         "due_day": _norm_due_day(due_day), "frequency": frequency or None,
         "flex": bool(flex), "handled": False,
         "target_date": target_date or None, "notes": notes or ""}
    s["envelopes"].append(e)
    return e


def env(s: dict, eid: str) -> dict:
    return next(e for e in s["envelopes"] if e["id"] == eid)


# ── Due dates + urgency (drives sort order and Forecast) ──────────────────────

def _norm_due_day(due_day):
    """Accept 1–31, the sentinel "eom" (end of month), or None."""
    if due_day is None or due_day == "":
        return None
    if isinstance(due_day, str) and due_day.strip().lower() == "eom":
        return "eom"
    try:
        d = int(due_day)
        return d if 1 <= d <= 31 else None
    except (ValueError, TypeError):
        return None


def _day_in_month(due_day, y: int, m: int) -> int:
    """Resolve a due_day (int or "eom") to a real day-of-month for (y, m)."""
    last = calendar.monthrange(y, m)[1]
    if isinstance(due_day, str) and due_day.lower() == "eom":
        return last
    return min(int(due_day), last)


def days_until(due_day, today: date | None = None) -> int | None:
    """Days until the next occurrence of a day-of-month (or "eom"), or None."""
    due_day = _norm_due_day(due_day)
    if due_day is None:
        return None
    today = today or date.today()
    y, m = today.year, today.month
    cand = date(y, m, _day_in_month(due_day, y, m))
    if cand < today:                                   # already passed → next month
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
        cand = date(y, m, _day_in_month(due_day, y, m))
    return (cand - today).days


def days_until_due(e: dict, today: date | None = None) -> int | None:
    return days_until(e.get("due_day"), today)


def urgency_score(available: float, gap: float, days, flex: bool = False,
                  handled: bool = False, is_vault: bool = False) -> float:
    """Pure scoring — reused for both the demo and live data. Higher floats up."""
    if handled:
        return -100.0
    if is_vault:
        return -50.0
    over = max(0.0, -available)
    score = 500.0 + over if over > 0 else 0.0          # overspent needs attention now
    if flex:
        return score                                    # flex isn't "due"; only urgent if overspent
    if gap > 0.005:
        if days is None:
            score += 10.0 + gap * 0.02                  # no date, mild nudge by size
        elif days < 0:
            score += 400.0 + gap                        # past due + unfunded → top
        else:
            score += max(0.0, 200.0 - days * 5.0) + gap * 0.03   # sooner/bigger = higher
    return score


def urgency(s: dict, e: dict) -> float:
    gap = round(max(0.0, e.get("target", 0.0) - e["funded"]), 2)
    return urgency_score(available(s, e), gap, days_until_due(e),
                         e.get("flex"), e.get("handled"), e["type"] == VAULT)


def status(available: float, gap: float, days, flex: bool = False, handled: bool = False) -> str:
    """A one-word state used for the badge on each card."""
    if handled:
        return "handled"
    if available < -0.005:
        return "over"
    if flex:
        return "flex"
    if gap > 0.005 and days is not None and days < 0:
        return "pastdue"
    if gap > 0.005 and days is not None and days <= 10:
        return "soon"
    if gap > 0.005:
        return "under"
    return "ok"


# ── Placement (silent — no ledger row) ────────────────────────────────────────

def fund(s: dict, eid: str, amount: float) -> float:
    """Move money Unallocated → envelope. RULE: you can never assign more than
    you have, so Unallocated never goes negative — a positive request is capped
    at whatever's Unallocated. Returns the amount actually moved."""
    amount = round(amount, 2)
    if amount > 0:
        amount = min(amount, round(s["unallocated"], 2))
    if amount == 0:
        return 0.0
    env(s, eid)["funded"] = round(env(s, eid)["funded"] + amount, 2)
    s["unallocated"] = round(s["unallocated"] - amount, 2)
    return amount


def defund(s: dict, eid: str, amount: float) -> None:
    fund(s, eid, -amount)


def set_funded(s: dict, eid: str, value: float) -> None:
    """Assign the envelope to an exact funded level (moves the delta to/from Unallocated)."""
    fund(s, eid, round(value - env(s, eid)["funded"], 2))


def move(s: dict, src_id: str, dst_id: str, amount: float) -> None:
    """Reallocate between two envelopes without touching Unallocated."""
    amount = round(amount, 2)
    env(s, src_id)["funded"] = round(env(s, src_id)["funded"] - amount, 2)
    env(s, dst_id)["funded"] = round(env(s, dst_id)["funded"] + amount, 2)


# ── Structure edits ───────────────────────────────────────────────────────────

def rename(s: dict, eid: str, name: str) -> None:
    name = (name or "").strip()
    if name:
        env(s, eid)["name"] = name


def set_target(s: dict, eid: str, value: float) -> None:
    env(s, eid)["target"] = round(max(0.0, value), 2)


def set_due_day(s: dict, eid: str, day) -> None:
    env(s, eid)["due_day"] = _norm_due_day(day)


def set_frequency(s: dict, eid: str, freq) -> None:
    env(s, eid)["frequency"] = freq or None


def set_target_date(s: dict, eid: str, target_date) -> None:
    """A goal's target month (YYYY-MM) — when you want to have saved the target."""
    env(s, eid)["target_date"] = (str(target_date).strip() or None) if target_date else None


def set_notes(s: dict, eid: str, notes) -> None:
    env(s, eid)["notes"] = (notes or "").strip()


def set_flex(s: dict, eid: str, flex: bool) -> None:
    env(s, eid)["flex"] = bool(flex)


def toggle_handled(s: dict, eid: str) -> None:
    e = env(s, eid)
    e["handled"] = not e.get("handled")


def set_category(s: dict, eid: str, cat_id: str) -> None:
    env(s, eid)["cat_id"] = cat_id


def delete_envelope(s: dict, eid: str) -> None:
    """Remove an envelope. Its unspent balance returns to Unallocated (money is
    never vaporized); past spending stays on the books."""
    e = env(s, eid)
    s["unallocated"] = round(s["unallocated"] + available(s, e), 2)
    s["envelopes"] = [x for x in s["envelopes"] if x["id"] != eid]


# ── Ledger (cleared money) ────────────────────────────────────────────────────

def add_expense(s: dict, eid: str, amount: float, desc: str = "", date: str = "") -> dict:
    if env(s, eid)["type"] == VAULT:
        raise ValueError("a vault can't be spent from — move money out with a transfer first")
    return _tx(s, EXPENSE, round(amount, 2), eid, desc, date)


def add_income(s: dict, amount: float, desc: str = "", date: str = "") -> dict:
    tx = _tx(s, INCOME, round(amount, 2), None, desc, date)
    s["unallocated"] = round(s["unallocated"] + amount, 2)
    return tx


def add_refund(s: dict, eid: str, amount: float, desc: str = "", date: str = "") -> dict:
    """Money that came back into an envelope (return, reimbursement) — the inverse
    of an expense. It lifts the envelope's available and the account balance."""
    if env(s, eid)["type"] == VAULT:
        raise ValueError("a vault holds no spending to refund")
    return _tx(s, REFUND, round(amount, 2), eid, desc, date)


def _tx(s: dict, kind: str, amount: float, eid, desc: str, date: str) -> dict:
    tx = {"id": _id(), "kind": kind, "amount": amount, "envelope_id": eid,
          "desc": desc, "date": date}
    s["transactions"].append(tx)
    return tx


def txn(s: dict, tid: str) -> dict:
    return next(t for t in s["transactions"] if t["id"] == tid)


_UNSET = object()


def edit_transaction(s: dict, tid: str, amount=_UNSET, desc=_UNSET,
                     date=_UNSET, envelope_id=_UNSET) -> None:
    """Edit a ledger row. Everything downstream (spent, available, balance) is
    derived, so a change recomputes live. Income touches Unallocated, which must
    never go negative — reducing income already given a job is refused."""
    t = txn(s, tid)
    if amount is not _UNSET:
        amount = round(float(amount), 2)
        if t["kind"] == INCOME:
            delta = round(amount - t["amount"], 2)
            if round(s["unallocated"] + delta, 2) < -0.005:
                raise ValueError("That income is already assigned to buckets — free it up first.")
            s["unallocated"] = round(s["unallocated"] + delta, 2)
        t["amount"] = amount
    if desc is not _UNSET:
        t["desc"] = desc
    if date is not _UNSET:
        t["date"] = date
    if envelope_id is not _UNSET and envelope_id and t["kind"] in (EXPENSE, REFUND):
        if env(s, envelope_id)["type"] == VAULT:
            raise ValueError("a vault can't be spent from")
        t["envelope_id"] = envelope_id


def delete_transaction(s: dict, tid: str) -> None:
    t = txn(s, tid)
    if t["kind"] == INCOME:
        if round(s["unallocated"] - t["amount"], 2) < -0.005:
            raise ValueError("That income is already assigned to buckets — free it up first.")
        s["unallocated"] = round(s["unallocated"] - t["amount"], 2)
    s["transactions"] = [x for x in s["transactions"] if x["id"] != tid]


# ── Income sources + allocation rules (settings that feed the Forecast) ───────

PAY_FREQS = ("weekly", "biweekly", "semimonthly", "monthly")
RULE_KINDS = ("internal", "external")
RULE_VALUE_TYPES = ("fixed", "pct", "fund")


def add_paycheck(s: dict, label: str, amount: float, freq: str, anchor: str) -> dict:
    p = {"id": _id(), "label": (label or "Paycheck").strip(),
         "amount": round(float(amount or 0), 2),
         "freq": freq if freq in PAY_FREQS else "biweekly", "anchor": anchor or ""}
    s["paychecks"].append(p)
    return p


def edit_paycheck(s: dict, pid: str, label=None, amount=None, freq=None, anchor=None) -> None:
    p = next(x for x in s["paychecks"] if x["id"] == pid)
    if label is not None:
        p["label"] = label.strip() or p["label"]
    if amount is not None:
        p["amount"] = round(float(amount or 0), 2)
    if freq is not None and freq in PAY_FREQS:
        p["freq"] = freq
    if anchor is not None:
        p["anchor"] = anchor or ""


def delete_paycheck(s: dict, pid: str) -> None:
    s["paychecks"] = [x for x in s["paychecks"] if x["id"] != pid]


def add_rule(s: dict, name: str, kind: str, bucket_id, value: float,
             value_type: str, active: bool = True) -> dict:
    r = {"id": _id(), "name": (name or "Rule").strip(),
         "kind": kind if kind in RULE_KINDS else "internal",
         "bucket_id": bucket_id or None, "value": round(float(value or 0), 2),
         "value_type": value_type if value_type in RULE_VALUE_TYPES else "fixed",
         "active": bool(active)}
    s["rules"].append(r)
    return r


def edit_rule(s: dict, rid: str, name=None, kind=None, bucket_id=_UNSET,
              value=None, value_type=None, active=None) -> None:
    r = next(x for x in s["rules"] if x["id"] == rid)
    if name is not None:
        r["name"] = name.strip() or r["name"]
    if kind is not None and kind in RULE_KINDS:
        r["kind"] = kind
    if bucket_id is not _UNSET:
        r["bucket_id"] = bucket_id or None
    if value is not None:
        r["value"] = round(float(value or 0), 2)
    if value_type is not None and value_type in RULE_VALUE_TYPES:
        r["value_type"] = value_type
    if active is not None:
        r["active"] = bool(active)


def delete_rule(s: dict, rid: str) -> None:
    s["rules"] = [x for x in s["rules"] if x["id"] != rid]


def toggle_rule(s: dict, rid: str) -> None:
    r = next(x for x in s["rules"] if x["id"] == rid)
    r["active"] = not r["active"]


# ── Derived metrics (computed, never stored) ──────────────────────────────────

def spent(s: dict, eid: str) -> float:
    """Net spent from an envelope: expenses less any refunds booked against it."""
    total = 0.0
    for t in s["transactions"]:
        if t.get("envelope_id") != eid:
            continue
        if t["kind"] == EXPENSE:
            total += t["amount"]
        elif t["kind"] == REFUND:
            total -= t["amount"]
    return round(total, 2)


def available(s: dict, e: dict) -> float:
    return round(e["funded"] - spent(s, e["id"]), 2)


def unallocated(s: dict) -> float:
    return round(s["unallocated"], 2)


def ready_to_spend(s: dict) -> float:
    return round(s["unallocated"] + sum(available(s, e) for e in s["envelopes"]
                                        if e["type"] != VAULT), 2)


def available_balance(s: dict) -> float:
    bal = s["opening"]
    for t in s["transactions"]:
        if t["kind"] in (INCOME, REFUND):
            bal += t["amount"]
        elif t["kind"] == EXPENSE:
            bal -= t["amount"]
    return round(bal, 2)
